# -*- coding:utf-8 -*-
"""
尝试 GEE 中直接跳过网格这一步骤，通过坐标框选有效范围

作者：23242
日期：2024年10月23日
"""
import geopandas as gpd
import pandas as pd
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


def read_dbf_to_list(dbf_file):
    """
    读取 .dbf 文件并将其转换为二维列表。

    :param dbf_file: .dbf 文件路径
    :return: 二维列表，包含文件中的数据
    """
    # 使用 geopandas 读取 dbf 文件
    gdf = gpd.read_file(dbf_file)

    # 将 GeoDataFrame 转换为 DataFrame
    df = pd.DataFrame(gdf)

    # 将 DataFrame 转换为二维列表
    data_list = df.values.tolist()

    return data_list


def create_feathered_image(image, boundary, feather_distance=500):
    """
    对影像应用边缘羽化处理，使得边界区域平滑过渡。

    参数:
    image (ee.Image): 输入的影像。
    boundary (ee.Geometry): 要应用羽化的几何边界。
    feather_distance (int): 羽化距离，单位为米，越大羽化效果越明显。

    返回:
    ee.Image: 应用羽化效果的影像。
    """
    # Step 1: 创建距离掩膜，以边界为中心计算距离，羽化距离为 feather_distance
    distance_mask = boundary.distance(feather_distance).clamp(0, feather_distance)

    # Step 2: 创建羽化权重掩膜，将距离映射到 0-1 的范围
    feathered_mask = ee.Image(1).subtract(distance_mask.divide(feather_distance))

    # Step 3: 应用羽化权重到图像，创建平滑的边界过渡
    feathered_image = image.updateMask(feathered_mask)

    return feathered_image


def crop_image_landsat(boundary, year, output_path):
    """
    裁剪 Landsat 8 图像，计算自定义指数并导出到 Google Drive。

    参数:
    boundary (list): 边界几何，表示为 [min_lon, min_lat, max_lon, max_lat] 格式
    year (int): 年份，用于过滤图像
    output_path (str): 导出到 Google Drive 的文件夹名称
    """
    # Step 0: 定义 img_name
    lon_list = f'{abs(boundary[0])}{"W" if boundary[0] < 0 else "E"}'
    lat_list = f'{abs(boundary[1])}{"S" if boundary[1] < 0 else "N"}'
    img_coordinates = lon_list + lat_list

    # Step 1: 定义静态的经纬度几何范围
    CoordinateMapBoundary = ee.Geometry.Rectangle(boundary)

    date_year = year
    img_folder = output_path
    img_name = img_coordinates

    try:
        if CoordinateMapBoundary:
            # Step 1: 定义云层和云影去除的掩膜函数
            def mask_l8_sr(image):
                qa_band = image.select('QA_PIXEL')
                cloud_shadow_bitmask = 1 << 3  # Cloud shadow
                clouds_bitmask = 1 << 4  # Clouds
                mask = qa_band.bitwiseAnd(cloud_shadow_bitmask).eq(0) \
                    .And(qa_band.bitwiseAnd(clouds_bitmask).eq(0))
                return image.updateMask(mask).divide(10000)

            # Step 2: 加载 Landsat 8 Level-2 影像集合，并应用云层去除
            ls8ImageCollection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                .filterBounds(CoordinateMapBoundary) \
                .filterDate(ee.Date.fromYMD(date_year - 1, 1, 1), ee.Date.fromYMD(date_year + 1, 12, 31)) \
                .map(mask_l8_sr)
            sorted_ls8 = ls8ImageCollection.sort('CLOUD_COVER').limit(150)

            # 检查图像集合的大小
            numImages = sorted_ls8.size().getInfo()
            if numImages > 0:
                # 计算图像集合的中值图像，并按边界裁剪
                clippedMedian = sorted_ls8.median().clip(CoordinateMapBoundary)

                # 计算自定义指数 (SR_B6 - SR_B3) / (SR_B6 + SR_B3)
                custom_index = clippedMedian.expression(
                    '(SR_B6 - SR_B3) / (SR_B6 + SR_B3)', {
                        'SR_B3': clippedMedian.select('SR_B3'),
                        'SR_B6': clippedMedian.select('SR_B6')
                    }
                ).rename('Custom_Index')

                # 应用边缘羽化掩膜
                feather_distance = 500  # 可以根据需要调整羽化距离
                custom_index_feathered = create_feathered_image(custom_index, CoordinateMapBoundary, feather_distance)

                # 处理无效值和限制比值范围
                custom_index_feathered = custom_index_feathered.unmask(0) \
                    .max(0).min(1) \
                    .multiply(255) \
                    .toByte()

                if img_name not in list_tif:
                    outputDescription = img_name + '_MNDWI_Feathered'
                    task = ee.batch.Export.image.toDrive(
                        image=custom_index_feathered,
                        folder=img_folder,
                        fileNamePrefix=outputDescription,
                        region=CoordinateMapBoundary.getInfo()['coordinates'],
                        scale=30,
                        maxPixels=1e13,
                        description=f'Download Landsat 8 {outputDescription}'
                    )
                    task.start()
                    print(f'Task started: {outputDescription}')
                    return task
                else:
                    print(f"Skipping file {img_name}, as it's in the draft list.")
                    return None
            else:
                print(f'No Landsat 8 images found for the defined boundary: {img_name}')
        else:
            print('Geometry is empty.')
    except ee.EEException as e:
        print(f'Error processing geometry: {e}')
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

    tasks = []
    max_tasks = 6  # 每批次最大任务数

    # .dbf 文件路径
    dbf_file = r'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\b_Global_Island_Grid\_DGS_GSV_SI_Grid_label.dbf'
    # 读取 dbf 文件为二维列表
    dbf_data = read_dbf_to_list(dbf_file)
    # 打印结果
    for row in dbf_data:
        # row: [0, '10953', 'UID_10953', 0, -27.5, -59.5, <POINT (-27.5 -59.5)>]
        temp_boundary_grid = [row[4] - 0.5, row[5] - 0.5, row[4] + 0.5, row[5] + 0.5]  # [-28.0, -60.0, -27.0, -59.0]
        boundary_grid = [int(i) for i in temp_boundary_grid]  # [-28, -60, -27, -59]
        # print(boundary_grid)

        # 直接传递完整的资产路径
        task = crop_image_landsat(
            boundary=boundary_grid,
            year=2015,  # 修改为你需要的年份
            output_path="_DGS_GSV_Landsat"
        )

        # 如果返回有效任务，添加到任务列表
        if task:
            tasks.append(task)

        # 检查是否达到了最大任务数
        if len(tasks) >= max_tasks:
            print(f"Waiting for {len(tasks)} tasks to finish.")

            # 等待当前批次任务完成
            while any([t.active() for t in tasks]):
                print('Tasks are running...')
                time.sleep(180)  # 每60秒检查一次任务状态

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
