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

# 指定文件夹路径
folder_path = r'E:\_GoogleDrive\_DGS_GSV_Landsat'
# 创建一个空列表来存放文件名
tif_files = []
# 遍历指定的文件夹
for filename in os.listdir(folder_path):
    if filename.endswith('_MNDWI.tif'):  # 判断文件是否以 .tif 结尾
        tif_files.append(filename.split('_MNDWI')[0])  # 将符合条件的文件名添加到列表中
# 定义已经处理的文件名列表
# list_tif = ["UID_10000", "UID_10233"]  # 文件名示例
list_tif = tif_files


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

                # 检查文件名是否在草稿列表中
                if img_name not in list_tif:
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
                    return task  # 返回任务对象
                else:
                    print(f"Skipping file {img_name}, as it's in the draft list.")
                    return None  # 返回None表示跳过任务
            else:
                print(f'No Landsat 8 images found for boundary: {img_boundary}')
        else:
            print('FeatureCollection is empty.')
    except ee.EEException as e:
        print(f'Error processing boundary {img_boundary}: {e}')
        return None


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
    aim_list = ["UID_15698", "UID_17810"]

    tasks = []
    max_tasks = 6  # 每批次最大任务数

    for asset_name in asset_names:
        # asset_name 格式如 'users/nicexian0011/_DGS_GSV_Grids/20367'
        uid = asset_name.split('/')[-1]

        if uid in aim_list:
            # 直接传递完整的资产路径
            island_boundary = asset_name
            start_year = 2015  # 修改为你需要的年份
            gee_output_path = "_DGS_GSV_Landsat"
            task = crop_image_landsat(boundary=island_boundary, year=start_year, output_path=gee_output_path)

            # 如果返回有效任务，添加到任务列表
            if task:
                tasks.append(task)

            # 检查是否达到了最大任务数
            if len(tasks) >= max_tasks:
                print(f"Waiting for {len(tasks)} tasks to finish.")

                # 等待当前批次任务完成
                while any([t.active() for t in tasks]):
                    print('Tasks are running...')
                    time.sleep(60)  # 每60秒检查一次任务状态

                # 清空已完成的任务列表
                tasks = []

    # 如果还有未完成的任务，等待最后一批完成
    if tasks:
        print(f"Waiting for final {len(tasks)} tasks to finish.")
        while any([t.active() for t in tasks]):
            print('Tasks are running...')
            time.sleep(60)

    # 记录结束时间
    end_time = time.time()
    # 计算差值即为程序运行时间
    formatted_time = format_time(end_time - start_time)
    print(f"Task completed in: {formatted_time}")


if __name__ == '__main__':
    main()
