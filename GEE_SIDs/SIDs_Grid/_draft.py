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


def crop_image_ls5(boundary, year):
    """
    计算 Landsat 5 指数。
    """
    boundary = [float(coord) for coord in boundary]
    CoordinateMapBoundary = ee.Geometry.Rectangle(boundary)

    def mask_l5_sr(image):
        qa_band = image.select('QA_PIXEL')
        cloud_shadow_bitmask = 1 << 3
        clouds_bitmask = 1 << 5
        mask = qa_band.bitwiseAnd(cloud_shadow_bitmask).eq(0) \
            .And(qa_band.bitwiseAnd(clouds_bitmask).eq(0))
        return image.updateMask(mask).divide(10000)

    ls5_collection = ee.ImageCollection('LANDSAT/LT05/C02/T1_L2') \
        .filterBounds(CoordinateMapBoundary) \
        .filterDate(ee.Date.fromYMD(year - 1, 1, 1), ee.Date.fromYMD(year + 1, 12, 31)) \
        .filter(ee.Filter.lt('CLOUD_COVER', 30)) \
        .map(mask_l5_sr)

    num_images = ls5_collection.size().getInfo()
    print('ls5_collection', num_images)
    if num_images == 0:
        print('No Landsat 5 images found.')
        return None

    median_image = ls5_collection.median().clip(CoordinateMapBoundary)
    # 计算百分位数（2% 和 98%）来进行动态范围拉伸
    stats = median_image.reduceRegion(
        reducer=ee.Reducer.percentile([2, 98]),
        geometry=CoordinateMapBoundary,
        scale=30,
        bestEffort=True
    )

    # 获取每个波段的 2% 和 98% 百分位数值
    min_vals = stats.getInfo()
    # print("Percentile values:", min_vals)
    # 'SR_B3_p2': 0.817, 'SR_B3_p98': 1.324,
    # 'SR_B2_p2': 0.856, 'SR_B2_p98': 1.246,
    # 'SR_B1_p2': 0.885, 'SR_B1_p98': 1.083,

    # 根据百分位数对图像进行拉伸
    rgb_image = median_image.select(['SR_B3', 'SR_B2', 'SR_B1']).rename(['Red', 'Green', 'Blue'])

    # 对每个波段使用百分位数拉伸
    # rgb_image = rgb_image.subtract([min_vals['SR_B3_p2'], min_vals['SR_B2_p2'], min_vals['SR_B1_p2']]) \
    #     .divide([min_vals['SR_B3_p98'] - min_vals['SR_B3_p2'],
    #              min_vals['SR_B2_p98'] - min_vals['SR_B2_p2'],
    #              min_vals['SR_B1_p98'] - min_vals['SR_B1_p2']])
    rgb_image = rgb_image.subtract([min_vals['SR_B3_p2'], min_vals['SR_B2_p2'], min_vals['SR_B1_p2']]) \
        .divide([0.45, 0.35, 0.2])

    # 将拉伸后的图像像素值范围限制在 [0, 1]，并转换为 8 位数据（0-255）
    rgb_image = rgb_image.clamp(0, 1).multiply(255).toByte()

    return rgb_image

def crop_image_ls7(boundary, year):
    """
    计算 Landsat 7 指数。
    """
    boundary = [float(coord) for coord in boundary]
    CoordinateMapBoundary = ee.Geometry.Rectangle(boundary)

    def mask_l7_sr(image):
        qa_band = image.select('QA_PIXEL')
        cloud_shadow_bitmask = 1 << 3
        clouds_bitmask = 1 << 5
        mask = qa_band.bitwiseAnd(cloud_shadow_bitmask).eq(0) \
            .And(qa_band.bitwiseAnd(clouds_bitmask).eq(0))
        return image.updateMask(mask).divide(10000)

    ls7_collection = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2') \
        .filterBounds(CoordinateMapBoundary) \
        .filterDate(ee.Date.fromYMD(year - 1, 1, 1), ee.Date.fromYMD(year + 1, 12, 31)) \
        .map(mask_l7_sr).sort('CLOUD_COVER').limit(50)

    num_images = ls7_collection.size().getInfo()
    print('ls7_collection', num_images)
    if num_images == 0:
        print('No Landsat 7 images found.')
        return None

    median_image = ls7_collection.median().clip(CoordinateMapBoundary)

    # 计算百分位数（2% 和 98%）来进行动态范围拉伸
    stats = median_image.reduceRegion(
        reducer=ee.Reducer.percentile([2, 98]),
        geometry=CoordinateMapBoundary,
        scale=30,
        bestEffort=True
    )

    # 获取每个波段的 2% 和 98% 百分位数值
    min_vals = stats.getInfo()
    # print("Percentile values:", min_vals)
    # 'SR_B1_p2': 0.904, 'SR_B1_p98': 1.091,
    # 'SR_B2_p2': 0.869, 'SR_B2_p98': 1.240,
    # 'SR_B3_p2': 0.838, 'SR_B3_p98': 1.351,

    # 根据百分位数对图像进行拉伸
    rgb_image = median_image.select(['SR_B3', 'SR_B2', 'SR_B1']).rename(['Red', 'Green', 'Blue'])

    # 对每个波段使用百分位数拉伸
    # rgb_image = rgb_image.subtract([min_vals['SR_B3_p2'], min_vals['SR_B2_p2'], min_vals['SR_B1_p2']]) \
    #     .divide([min_vals['SR_B3_p98'] - min_vals['SR_B3_p2'],
    #              min_vals['SR_B2_p98'] - min_vals['SR_B2_p2'],
    #              min_vals['SR_B1_p98'] - min_vals['SR_B1_p2']])
    rgb_image = rgb_image.subtract([min_vals['SR_B3_p2'], min_vals['SR_B2_p2'], min_vals['SR_B1_p2']]) \
        .divide([0.45, 0.35, 0.2])

    # 将拉伸后的图像像素值范围限制在 [0, 1]，并转换为 8 位数据（0-255）
    rgb_image = rgb_image.clamp(0, 1).multiply(255).toByte()

    return rgb_image


def crop_image_ls8(boundary, year):
    """
    计算 Landsat 8 指数。
    """
    boundary = [float(coord) for coord in boundary]
    CoordinateMapBoundary = ee.Geometry.Rectangle(boundary)

    def mask_l8_sr(image):
        qa_band = image.select('QA_PIXEL')
        cloud_shadow_bitmask = 1 << 3
        clouds_bitmask = 1 << 4
        mask = qa_band.bitwiseAnd(cloud_shadow_bitmask).eq(0) \
            .And(qa_band.bitwiseAnd(clouds_bitmask).eq(0))
        return image.updateMask(mask).divide(10000)

    ls8_collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
        .filterBounds(CoordinateMapBoundary) \
        .filterDate(ee.Date.fromYMD(year - 1, 1, 1), ee.Date.fromYMD(year + 1, 12, 31)) \
        .map(mask_l8_sr).sort('CLOUD_COVER').limit(50)

    num_images = ls8_collection.size().getInfo()
    print('ls8_collection', num_images)
    if num_images == 0:
        print('No Landsat 8 images found.')
        return None

    median_image = ls8_collection.median().clip(CoordinateMapBoundary)

    # 计算百分位数（2% 和 98%）来进行动态范围拉伸
    stats = median_image.reduceRegion(
        reducer=ee.Reducer.percentile([2, 98]),
        geometry=CoordinateMapBoundary,
        scale=30,
        bestEffort=True
    )

    # 获取每个波段的 2% 和 98% 百分位数值
    min_vals = stats.getInfo()
    # print("Percentile values:", min_vals)
    # 'SR_B1_p2': 0.904, 'SR_B1_p98': 1.091,
    # 'SR_B2_p2': 0.869, 'SR_B2_p98': 1.240,
    # 'SR_B3_p2': 0.838, 'SR_B3_p98': 1.351,

    # 根据百分位数对图像进行拉伸
    rgb_image = median_image.select(['SR_B1', 'SR_B3', 'SR_B2']).rename(['Red', 'Green', 'Blue'])

    rgb_image = rgb_image.subtract([min_vals['SR_B1_p2'], min_vals['SR_B3_p2'], min_vals['SR_B2_p2']]) \
        .divide([0.45, 0.35, 0.2])

    # 将拉伸后的图像像素值范围限制在 [0, 1]，并转换为 8 位数据（0-255）
    rgb_image = rgb_image.clamp(0, 1).multiply(255).toByte()

    return rgb_image


def merge_ls_indices(boundary, year, output_path, img_name):
    """
    融合 Landsat 5, Landsat 7 和 Landsat 8 指数，并导出到 Google Drive。
    """
    boundary = [float(coord) for coord in boundary]
    CoordinateMapBoundary = ee.Geometry.Rectangle(boundary)

    # 计算 Landsat 7 和 Landsat 8 指数
    ls5_index = crop_image_ls5(boundary, year)
    ls7_index = crop_image_ls7(boundary, year)
    ls8_index = crop_image_ls8(boundary, year)

    # 筛选有效数据源
    origin_index_list = [ls5_index, ls7_index, ls8_index]
    valid_index_list = []
    for index in origin_index_list:
        if index:
            valid_index_list.append(index)

    if valid_index_list:
        # 融合 Landsat 7 和 Landsat 8 指数
        merged_image = ee.ImageCollection(valid_index_list).median().clip(CoordinateMapBoundary)

        # 导出融合影像
        task = ee.batch.Export.image.toDrive(
            image=merged_image.round(),
            folder=output_path,
            fileNamePrefix=f'{img_name}_rgb_{(year % 100):02}',
            region=CoordinateMapBoundary.getInfo()['coordinates'][0],
            scale=30,
            maxPixels=1e13,
            description=f'Export {img_name}_rgb_{(year % 100):02}'
        )
        task.start()
        print(f'Task started for Merged Index: {img_name}')
        return task
    else:
        return None


def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)

    return f"{hours:02}:{minutes:02}:{seconds:02}"


def main():
    # 记录脚本开始执行的时间
    start_time = time.time()
    tasks = []
    max_tasks = 6  # 定义每批次最大任务数

    # 初始化任务配置参数
    year_crop = 2000  # 设置下载年份
    dbf_name = '_draft'  # 设置dbf文件的基础名称
    # 根据年份和dbf名称构造Google Drive中的文件夹路径
    google_drive_path = dbf_name  # 例如: Glo_Div_10_Y20

    # 调用函数读取DBF文件内容，并返回列表形式的数据
    # 参数if_print设置为0表示不打印记录列表  [[140268, 'UID_140268', 113.75, 7.25], [140986, 'UID_140986', 112.75, 7.75],
    # records_list = read_dbf_to_list(
    #     dbf_path=fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\d_SIDS_Boundary\SIDS_Grids\_glo_sids_grids.dbf',
    #     if_print=0)
    records_list = read_dbf_to_list(
        dbf_path=fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\d_SIDS_Boundary\SIDS_Grids\SIDS_grid_link\ABW_grid.dbf',
        if_print=0)
    # records_list = [[1, 'UID_140268', -70.25, -54.75]]
    # records_list = [[1, 'UID_140268', 73.25, 2.25]]
    # 确定已存在的数据集
    # 列出指定文件夹中所有以特定扩展名结尾的文件 records_list = [[1, 'UID_140268', -70.25, -54.75], [1, 'UID_140268', 54.75, 25.75]]
    records_list_exist_temp = list_files_with_extension(
        folder_path=fr'E:\_GoogleDrive\{google_drive_path}',
        extension=fr'_Index.tif',
        if_print=0)
    # 从文件名中提取前缀，去除"_DBNDWI.tif"后缀  '65W17Nlu', '65W18Nlb', '65W18Nrb', '65W18Nru',
    records_list_exist = [filename.split('_')[0] for filename in records_list_exist_temp]

    # 逐一运行
    for record in records_list:
        # 初始化地理要素
        longitude = record[2]  # 记录中的经度值
        latitude = record[3]  # 记录中的纬度值

        # 确定格网范围
        lb_lon, lb_lat = get_grid_coordinates(longitude, latitude)  # 获取网格的左下角坐标
        rt_lon = lb_lon + 0.5
        rt_lat = lb_lat + 0.5
        # 构建表示网格边界的列表
        boundary_grid = [lb_lon, lb_lat, rt_lon, rt_lat]

        # 确定格网名称
        position = determine_map_position(longitude=longitude, latitude=latitude, if_print=0)  # 84W17Nlb

        if position not in records_list_exist:  # position: 113E8Nlb
            print(boundary_grid)  # [113.5, 7.0, 114.0, 7.5]
            # 直接传递完整的资产路径
            task = merge_ls_indices(
                boundary=boundary_grid,
                year=year_crop,
                output_path=google_drive_path,
                img_name=position
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
