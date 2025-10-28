# -*- coding:utf-8 -*-
"""
加载并处理地理空间数据：
    加载一个包含地理边界的 FeatureCollection。
    确认边界数据集中有特征存在。
处理 Landsat-8 图像数据：
    创建一个过滤后的 Landsat-8 图像集合，包括时间和地理范围的筛选。
    使用 QA_PIXEL 波段进行云遮蔽处理。
    计算自定义指数 (SR_B6 - SR_B3) / (SR_B6 + SR_B3)。
    处理无效值，限制比值范围，并转换数据类型。
    计算图像集合的中值图像，并按边界裁剪。
导出处理后的图像数据：
    将处理后的自定义指数图像导出到 Google Drive。

作者：23242
日期：2024年09月10日
"""

import ee
from datetime import datetime
import os
import time

# 设置网络代理（如有需要）
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:4780'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:4780'

# 设置代理超时时间（如有需要）
os.environ['http_proxy_timeout'] = '300'
os.environ['https_proxy_timeout'] = '300'

# 设置环境变量以解决 OpenSSL 3.0 的兼容性问题
os.environ['CRYPTOGRAPHY_OPENSSL_NO_LEGACY'] = '1'

# 授权并初始化 Earth Engine API
ee.Authenticate()
ee.Initialize(project='ee-nicexian0011')


def crop_image_landsat(boundary, year, output_path):
    """
    裁剪 Landsat 8 图像，计算自定义指数并导出到 Google Drive。

    参数:
    boundary (str): 资产的完整路径，如 'users/nicexian0011/_DGS_GSV_Grids/20367'
    year (int): 年份，用于过滤图像
    output_path (str): 导出到 Google Drive 的文件夹名称
    """
    img_boundary = boundary
    date_year = year
    img_folder = output_path
    img_name = img_boundary.split('/')[-1]

    try:
        # 加载用户的行政区划边界数据集
        adminBoundary = ee.FeatureCollection(img_boundary)

        # 检查边界数据集中是否有特征
        numFeatures = adminBoundary.size().getInfo()
        if numFeatures > 0:
            # 获取边界数据集的几何信息
            boundaryGeometry = adminBoundary.geometry()

            # 创建 Landsat 8 Level-2 反射率图像集合
            ls8ImageCollection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                .filterBounds(boundaryGeometry) \
                .filterDate(ee.Date.fromYMD(date_year, 1, 1), ee.Date.fromYMD(date_year + 1, 1, 1)) \
                .filter(ee.Filter.lte('CLOUD_COVER', 40)) \
                .sort('CLOUD_COVER') \
                .limit(5)  # 限制最多获取5副图像

            # 检查图像集合的大小
            numImages = ls8ImageCollection.size().getInfo()
            if numImages > 0:
                # 定义一个函数来遮蔽 Landsat 8 图像中的云
                def mask_landsat8_clouds(image):
                    # 使用内置的 QA_PIXEL 波段来进行云掩膜
                    qa_band = image.select('QA_PIXEL')
                    cloud_mask = qa_band.bitwiseAnd(1 << 5).eq(0) \
                        .And(qa_band.bitwiseAnd(1 << 3).eq(0)) \
                        .And(qa_band.bitwiseAnd(1 << 4).eq(0))
                    return image.updateMask(cloud_mask).divide(10000)

                # 应用云掩膜到图像集合
                masked_ls8 = ls8ImageCollection.map(mask_landsat8_clouds)

                # 计算图像集合的中值图像，并按边界裁剪
                clippedMedian = masked_ls8.median().clip(boundaryGeometry)

                # 计算自定义指数 (SR_B6 - SR_B3) / (SR_B6 + SR_B3)
                custom_index = clippedMedian.expression(
                    '(SR_B6 - SR_B3) / (SR_B6 + SR_B3)', {
                        'SR_B3': clippedMedian.select('SR_B3'),
                        'SR_B6': clippedMedian.select('SR_B6')
                    }
                ).rename('Custom_Index')

                # 处理无效值和限制比值范围
                custom_index = custom_index.unmask(0) \
                    .max(0).min(1) \
                    .multiply(255) \
                    .toByte()

                # 设置自定义指数的可视化参数（可选）
                indexVis = {
                    'min': 0,
                    'max': 255,
                    'palette': ['blue', 'white', 'green']
                }

                # 导出裁剪后的自定义指数图像到 Google Drive
                outputDescription = img_name + '_MNDWI'
                task = ee.batch.Export.image.toDrive(
                    image=custom_index,
                    folder=img_folder,
                    fileNamePrefix=outputDescription,
                    region=boundaryGeometry.getInfo()['coordinates'],
                    scale=30,
                    maxPixels=1e13,
                    description=f'Download Landsat 8 {outputDescription}'  # 使用定义的任务名称
                )
                task.start()
                print(f'Task started: {outputDescription}')

                # # 可选：监控任务状态
                # while task.active():
                #     print('Task is running...')
                #     time.sleep(30)  # 每30秒检查一次
                #     # pass
                print(f'Task completed with status: {task.status()}')
            else:
                print(f'No Landsat 8 images found for boundary: {img_boundary}')
        else:
            print('FeatureCollection is empty.')
    except ee.EEException as e:
        print(f'Error processing boundary {img_boundary}: {e}')


def list_assets_in_folder(folder_path):
    """
    列出指定文件夹下的所有资产名称，包括子文件夹中的资产。

    参数:
    folder_path (str): 文件夹路径，如 'users/nicexian0011/_DGS_GSV_Grids'

    返回:
    list: 包含指定文件夹下所有资产名称的列表。
    """
    assets = []

    def _list_assets_recursive(prefix):
        try:
            response = ee.data.listAssets({'parent': prefix})
            for asset in response.get('assets', []):
                asset_name = asset['name']
                assets.append(asset_name)
                # 如果资产是文件夹，则递归列出其内容
                if asset['type'] == 'FOLDER':
                    _list_assets_recursive(asset_name + '/')
        except ee.EEException as e:
            print(f"Error listing assets in {prefix}: {e}")

    _list_assets_recursive(folder_path)
    return assets


def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)

    return f"{hours:02}:{minutes:02}:{seconds:02}"


def main():
    # 记录开始时间
    start_time = time.time()
    # 指定文件夹路径
    folder_path = 'users/nicexian0011/_DGS_GSV_Grids'
    # 获取文件夹下的所有资产名称
    asset_names = list_assets_in_folder(folder_path)
    # 需要处理的资产列表
    aim_list = ["UID_15698", "UID_17810", "UID_17811", "UID_18888", "UID_19999", "UID_20000", "UID_20003", "UID_20004",
                "UID_20005", "UID_20006", "UID_20358", "UID_20359", "UID_20366", "UID_20367", "UID_20368", "UID_20718",
                "UID_20729", "UID_20730", "UID_21090", "UID_21798", "UID_22157", "UID_22173", "UID_22516", "UID_22876",
                "UID_22893", "UID_23253", "UID_23265", "UID_23266", "UID_23267", "UID_23595", "UID_23615", "UID_23624",
                "UID_23625", "UID_23628", "UID_23976", "UID_23984", "UID_23988", "UID_24315", "UID_24336", "UID_24341",
                "UID_24344", "UID_24348", "UID_24349", "UID_24696", "UID_24700", "UID_24704", "UID_24709", "UID_24716",
                "UID_25055", "UID_25056", "UID_25064", "UID_25065", "UID_25069", "UID_25078", "UID_25415", "UID_25416",
                "UID_25425", "UID_25429", "UID_25430", "UID_25438", "UID_25444", "UID_25776", "UID_25777", "UID_25784",
                "UID_25785", "UID_25790", "UID_26137", "UID_26138", "UID_26139", "UID_26140", "UID_26144", "UID_26145",
                "UID_26150", "UID_26455", "UID_26500", "UID_26501", "UID_26505", "UID_26506", "UID_26507", "UID_26510",
                "UID_26520", "UID_26815", "UID_26861", "UID_26866", "UID_26867", "UID_26868", "UID_26870", "UID_26871",
                "UID_26875", "UID_27193", "UID_27221", "UID_27228", "UID_27229", "UID_27231", "UID_27553", "UID_27581",
                "UID_27586", "UID_27588", "UID_27589", "UID_27590", "UID_27591", "UID_27941", "UID_27944", "UID_27945",
                "UID_27946", "UID_27949", "UID_27950", "UID_28301", "UID_28304", "UID_28308", "UID_28310", "UID_28660",
                "UID_28661", "UID_28668", "UID_28672", "UID_29020", "UID_29027", "UID_29028", "UID_29031", "UID_29354",
                "UID_29380", "UID_29686", "UID_29714", "UID_29740", "UID_29753", "UID_30073", "UID_30099", "UID_30100",
                "UID_30113", "UID_30114", "UID_30433", "UID_30434", "UID_30459", "UID_30460", "UID_30474", "UID_30792",
                "UID_30820", "UID_30834", "UID_30836", "UID_31151", "UID_31152", "UID_31180", "UID_31181", "UID_31196",
                "UID_31510", "UID_31511", "UID_31541", "UID_31542", "UID_31866", "UID_31869", "UID_31870", "UID_31901",
                "UID_31902", "UID_31903", "UID_32229", "UID_32230", "UID_32263", "UID_32587", "UID_32590", "UID_32948",
                "UID_32950", "UID_33310", "UID_33346", "UID_33669", "UID_33670", "UID_34011", "UID_34012", "UID_34013",
                "UID_34014", "UID_34018", "UID_34019", "UID_34026", "UID_34027", "UID_34028", "UID_34029", "UID_34030",
                "UID_34370", "UID_34371", "UID_34375", "UID_34376", "UID_34377", "UID_34378", "UID_34379", "UID_34380",
                "UID_34381", "UID_34385", "UID_34386", "UID_34387", "UID_34389", "UID_34729", "UID_34730", "UID_34742",
                "UID_34743", "UID_34744", "UID_34745", "UID_35087", "UID_35088", "UID_35089", "UID_35447", "UID_35448",
                "UID_35511", "UID_35807", "UID_36165", "UID_36166", "UID_36167", "UID_36226", "UID_36524", "UID_36525",
                "UID_36526", "UID_36583", "UID_36584", "UID_36588", "UID_36591", "UID_36884", "UID_36885", "UID_36943",
                "UID_36944", "UID_36953", "UID_36954", "UID_36955", "UID_37244", "UID_37302", "UID_37303", "UID_37596",
                "UID_37597", "UID_37603", "UID_37604", "UID_37661", "UID_37662", "UID_37957", "UID_37964", "UID_38020",
                "UID_38021", "UID_38315", "UID_38316", "UID_38318", "UID_38324", "UID_38380", "UID_38381", "UID_38675",
                "UID_38676", "UID_39098", "UID_39099", "UID_39404", "UID_39458", "UID_39459", "UID_39764", "UID_39818",
                "UID_40178", "UID_40536", "UID_40537", "UID_40845", "UID_40896", "UID_40897", "UID_41256", "UID_41974",
                "UID_42282", "UID_42283", "UID_42285", "UID_42334", "UID_42643", "UID_42644", "UID_42645", "UID_42646",
                "UID_42647", "UID_43007", "UID_43053", "UID_43364", "UID_43365", "UID_43400", "UID_43401", "UID_43409",
                "UID_43410", "UID_43413", "UID_43731", "UID_43760", "UID_43765", "UID_43766", "UID_43767", "UID_43768",
                "UID_43769", "UID_43770", "UID_43771", "UID_43772", "UID_43773", "UID_44083", "UID_44084", "UID_44091",
                "UID_44092", "UID_44113", "UID_44114", "UID_44115", "UID_44121", "UID_44122", "UID_44123", "UID_44124",
                "UID_44125", "UID_44444", "UID_44453", "UID_44471", "UID_44472", "UID_44814", "UID_44831", "UID_44832",
                "UID_45175", "UID_45176", "UID_45177", "UID_45178", "UID_45179", "UID_45180", "UID_45181", "UID_45191",
                "UID_45192", "UID_45541", "UID_45542", "UID_45543", "UID_45544", "UID_45545", "UID_45546", "UID_45547",
                "UID_45548", "UID_45549", "UID_45551", "UID_45907", "UID_45908", "UID_45909", "UID_45910", "UID_45911",
                "UID_20363", "UID_21078", "UID_21811", "UID_22875", "UID_23254", "UID_23616", "UID_26472", "UID_28993",
                "UID_28994", "UID_32624", "UID_32985", "UID_36228", "UID_36232", "UID_37245", "UID_37963", "UID_41205",
                "UID_41926", "UID_42287", "UID_42288", "UID_42648", "UID_43371", "UID_44452", "UID_44454", "UID_20719",
                "UID_21079", "UID_21091", "UID_21438", "UID_21451", "UID_21797", "UID_22533", "UID_23235", "UID_23955",
                "UID_25393", "UID_26112", "UID_28634", "UID_29032", "UID_30833", "UID_31193", "UID_32986", "UID_36225",
                "UID_36227", "UID_37956", "UID_37958", "UID_38325", "UID_40844", "UID_41206", "UID_41566", "UID_41927",
                "UID_42286", "UID_42649"]

    # aim_list = ['20366']

    for asset_name in asset_names:
        # asset_name 格式如 'users/nicexian0011/_DGS_GSV_Grids/20367'
        uid = asset_name.split('/')[-1]

        if uid in aim_list:
            # 直接传递完整的资产路径
            island_boundary = asset_name
            start_year = 2015  # 修改为你需要的年份
            gee_output_path = "_DGS_GSV_Landsat"
            crop_image_landsat(boundary=island_boundary, year=start_year, output_path=gee_output_path)
    # 记录结束时间
    end_time = time.time()
    # 计算差值即为程序运行时间
    formatted_time = format_time(end_time - start_time)
    print(f"Task completed in: {formatted_time}")


if __name__ == '__main__':
    main()
