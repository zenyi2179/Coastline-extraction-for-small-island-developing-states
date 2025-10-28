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
import math
from _tools import determine_map_position
from _tools import read_dbf_to_list
from _tools import get_grid_coordinates
from _tools import list_files_with_extension

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


def crop_image_landsat(boundary, year, output_path, img_name):
    """
    裁剪 Landsat 8 图像，计算自定义指数并导出到 Google Drive。

    参数:
    boundary (list): 边界几何，表示为 [min_lon, min_lat, max_lon, max_lat] 格式
    year (int): 年份，用于过滤图像
    output_path (str): 导出到 Google Drive 的文件夹名称
    img_name (str): 输出文件的前缀名称
    """
    # 将边界转换为浮点数列表，确保格式正确
    boundary = [float(coord) for coord in boundary]
    CoordinateMapBoundary = ee.Geometry.Rectangle(boundary)
    tif_num = 150

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

            # Step 2: 加载 Landsat 8 图像集合，优先使用目标年份
            ls8ImageCollection_main_year = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                .filterBounds(CoordinateMapBoundary) \
                .filterDate(ee.Date.fromYMD(year, 1, 1), ee.Date.fromYMD(year, 12, 31)) \
                .map(mask_l8_sr)

            # 获取主年份图像数量
            num_main_year_images = ls8ImageCollection_main_year.size().getInfo()

            if num_main_year_images < tif_num:  # 如果图像数量不足
                # 补充相邻年份图像
                additional_images_needed = tif_num - num_main_year_images
                ls8ImageCollection_adjacent_years = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                    .filterBounds(CoordinateMapBoundary) \
                    .filterDate(ee.Date.fromYMD(year - 1, 1, 1), ee.Date.fromYMD(year + 1, 12, 31)) \
                    .map(mask_l8_sr)

                # 合并主年份和相邻年份的图像
                ls8ImageCollection = ls8ImageCollection_main_year.merge(ls8ImageCollection_adjacent_years) \
                    .sort('CLOUD_COVER').limit(tif_num)
            else:
                # 如果主年份图像足够，直接使用
                ls8ImageCollection = ls8ImageCollection_main_year.sort('CLOUD_COVER').limit(tif_num)

            # 检查图像集合的大小
            numImages = ls8ImageCollection.size().getInfo()
            if numImages > 0:
                # 计算图像集合的中值图像，并按边界裁剪
                clippedMedian = ls8ImageCollection.median().clip(CoordinateMapBoundary)

                # 计算自定义指数 (SR_B5 - SR_B3) / (SR_B5 + SR_B3)
                custom_index = clippedMedian.expression(
                    '(0.25 * (SR_B3 - SR_QA_AEROSOL) + 0.75 * (SR_B5 - SR_B3)) / (SR_QA_AEROSOL + SR_B5)', {
                        'SR_B3': clippedMedian.select('SR_B3'),
                        'SR_B5': clippedMedian.select('SR_B5'),
                        'SR_QA_AEROSOL': clippedMedian.select('SR_QA_AEROSOL')
                    }
                ).rename('Custom_Index')

                # 处理无效值和限制比值范围
                custom_index_feathered = custom_index.unmask(0) \
                    .max(0).min(1) \
                    .multiply(255) \
                    .toByte()

                # Step 3: 计算 NDSI（Normalized Difference Snow Index）
                ndsi = clippedMedian.normalizedDifference(['SR_B3', 'SR_B6']).rename('NDSI')

                # Step 4: 创建单波段融合图像
                # 对于 NDSI > 0.4 的区域赋值为 100，其他区域保持 custom_index_feathered
                fused_image = custom_index_feathered.where(ndsi.gt(0.4), 300)

                # Step 5: 导出结果到 Google Drive
                outputDescription = img_name + f'_{numImages}_DBNDWI'
                task = ee.batch.Export.image.toDrive(
                    image=fused_image,
                    folder=output_path,
                    fileNamePrefix=outputDescription,
                    region=CoordinateMapBoundary.getInfo()['coordinates'][0],  # 使用 Geometry 对象
                    scale=30,
                    maxPixels=1e13,
                    description=f'Download Landsat 8 {outputDescription}',
                )
                task.start()
                print(f'Task started: {outputDescription}')
                return task
            else:
                print(f'No Landsat 8 images found for the defined boundary: {img_name}')
        else:
            print('Geometry is empty.')
    except ee.EEException as e:
        print(f'Error processing geometry: {e}')
        return None


def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)

    return f"{hours:02}:{minutes:02}:{seconds:02}"


def main():
    # 记录开始时间
    start_time = time.time()

    # 初始化任务设置
    tasks = []
    max_tasks = 6  # 每批次最大任务数

    # 调用函数并传入 DBF 文件路径，设置 if_print 参数为 0 表示不打印记录列表
    # [[140268, 'UID_140268', 113.75, 7.25], [140986, 'UID_140986', 112.75, 7.75],
    records_list = read_dbf_to_list(
        dbf_path=fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\Chile.dbf',
        if_print=0)
    records_list = [[1, 'UID_140268', -70.25, -54.75]]
    google_drive_path = 'Chile'
    records_list_exist_temp = list_files_with_extension(
        folder_path=fr'E:\_GoogleDrive',
        extension=fr'_DBNDWI.tif',
        if_print=0)
    # 去除每个文件名的 "_DBNDWI.tif" 后缀: '65W17Nlu', '65W18Nlb', '65W18Nrb', '65W18Nru',
    records_list_exist = [filename.split('_')[0] for filename in records_list_exist_temp]

    # 逐一运行
    for record in records_list:
        # 初始化要素
        longitude = record[2]
        latitude = record[3]

        # 确定格网范围
        lb_lon, lb_lat = get_grid_coordinates(longitude, latitude)  # 获取网格的左下角坐标
        rt_lon = lb_lon + 0.5
        rt_lat = lb_lat + 0.5
        boundary_grid = [lb_lon, lb_lat, rt_lon, rt_lat]

        # 确定格网名称
        position = determine_map_position(longitude=longitude, latitude=latitude, if_print=0)  # 84W17Nlb

        if position not in records_list_exist:  # position: 113E8Nlb
            print(boundary_grid)  # [113.5, 7.0, 114.0, 7.5]
            # 直接传递完整的资产路径
            task = crop_image_landsat(
                boundary=boundary_grid,
                year=2015,  # 修改为你需要的年份
                output_path=google_drive_path,
                img_name=position,
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
