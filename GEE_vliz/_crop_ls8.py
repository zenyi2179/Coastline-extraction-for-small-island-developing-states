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
    """
    # 将边界转换为浮点数列表，确保格式正确
    boundary = [float(coord) for coord in boundary]
    CoordinateMapBoundary = ee.Geometry.Rectangle(boundary)

    date_year = year
    img_folder = output_path

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

                # 应用高斯模糊以进行边缘羽化
                # 选择羽化半径（根据图像的分辨率进行调整）
                blur_radius = 500  # 适当选择羽化半径
                blurredMedian = clippedMedian.convolve(ee.Kernel.gaussian(radius=blur_radius, sigma=blur_radius / 2))

                # 计算自定义指数 (SR_B6 - SR_B3) / (SR_B6 + SR_B3)
                custom_index = blurredMedian.expression(
                    '(SR_B6 - SR_B3) / (SR_B6 + SR_B3)', {
                        'SR_B3': clippedMedian.select('SR_B3'),
                        'SR_B6': clippedMedian.select('SR_B6')
                    }
                ).rename('Custom_Index')

                # 处理无效值和限制比值范围
                custom_index_feathered = custom_index.unmask(0) \
                    .max(0).min(1) \
                    .multiply(255) \
                    .toByte()

                # 开始处理任务
                outputDescription = img_name + '_MNDWI'
                task = ee.batch.Export.image.toDrive(
                    image=custom_index_feathered,
                    folder=img_folder,
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
        dbf_path=fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\SouthChinaSea.dbf',
        if_print=0)
    records_list_exist_temp = list_files_with_extension(
        folder_path=fr'E:\_GoogleDrive\SouthChinaSea',
        extension=fr'_MNDWI.tif',
        if_print=0)
    # 去除每个文件名的 "_MNDWI.tif" 后缀
    records_list_exist = [filename.replace('_MNDWI.tif', '') for filename in records_list_exist_temp]

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
        position = determine_map_position(longitude=longitude, latitude=latitude, if_print=0)

        if position not in records_list_exist:  # position: 113E8Nlb
            print(boundary_grid)  # [113.5, 7.0, 114.0, 7.5]
            # 直接传递完整的资产路径
            task = crop_image_landsat(
                boundary=boundary_grid,
                year=2015,  # 修改为你需要的年份
                output_path="SouthChinaSea",
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
