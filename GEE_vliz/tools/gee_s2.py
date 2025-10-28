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
from determine_map_position import determine_map_position

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


def crop_image_sentinel(boundary, year, output_path, img_name, exist_tif):
    """
    裁剪 Sentinel-2 图像，计算自定义指数并导出到 Google Drive。

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
            # Step 1: 定义云层去除的掩膜函数
            def mask_s2_sr(image):
                qa_band = image.select('QA60')
                cloud_bitmask = 1 << 10  # High-probability clouds
                cirrus_bitmask = 1 << 11  # Cirrus clouds
                mask = qa_band.bitwiseAnd(cloud_bitmask).eq(0) \
                    .And(qa_band.bitwiseAnd(cirrus_bitmask).eq(0))
                return image.updateMask(mask).divide(10000)  # 标准化至 0-1

            # Step 2: 加载 Sentinel-2 影像集合，并应用云层去除
            s2ImageCollection = ee.ImageCollection('COPERNICUS/S2_HARMONIZED') \
                .filterBounds(CoordinateMapBoundary) \
                .filterDate(ee.Date.fromYMD(date_year - 1, 1, 1), ee.Date.fromYMD(date_year + 1, 12, 31)) \
                .map(mask_s2_sr)
            sorted_s2 = s2ImageCollection.sort('CLOUDY_PIXEL_PERCENTAGE').limit(150)

            # 检查图像集合的大小
            numImages = sorted_s2.size().getInfo()
            if numImages > 0:
                # 计算图像集合的中值图像，并按边界裁剪
                clippedMedian = sorted_s2.median().clip(CoordinateMapBoundary)

                # 应用高斯模糊以进行边缘羽化
                blur_radius = 200  # 适当选择羽化半径
                blurredMedian = clippedMedian.convolve(ee.Kernel.gaussian(radius=blur_radius, sigma=blur_radius / 2))

                # 计算自定义指数 (B11 - B3) / (B11 + B3)
                custom_index = blurredMedian.expression(
                    '(B11 - B3) / (B11 + B3)', {
                        'B3': clippedMedian.select('B3'),
                        'B11': clippedMedian.select('B11')
                    }
                ).rename('Custom_Index')

                # 处理无效值和限制比值范围
                custom_index_feathered = custom_index.unmask(0) \
                    .max(0).min(1) \
                    .multiply(255) \
                    .toByte()

                if img_name not in exist_tif:
                    outputDescription = img_name + '_MNDWI'
                    task = ee.batch.Export.image.toDrive(
                        image=custom_index_feathered,
                        folder=img_folder,
                        fileNamePrefix=outputDescription,
                        region=CoordinateMapBoundary.getInfo()['coordinates'][0],  # 使用 Geometry 对象
                        scale=10,  # Sentinel-2 默认分辨率为 10 米
                        maxPixels=1e13,
                        description=f'Download Sentinel-2 {outputDescription}',
                    )

                    task.start()
                    print(f'Task started: {outputDescription}')
                    return task
                else:
                    print(f"Skipping file {img_name}, as it's in the draft list.")
                    return None
            else:
                print(f'No Sentinel-2 images found for the defined boundary: {img_name}')
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


def get_grid_coordinates(longitude, latitude):
    # 计算经度的网格左下角坐标
    grid_longitude = math.floor(longitude * 2) / 2
    # 计算纬度的网格左下角坐标
    grid_latitude = math.floor(latitude * 2) / 2

    return grid_longitude, grid_latitude


def find_exist_tif(folder_path):
    # 创建一个空列表来存放文件名
    tif_files = []
    # 遍历指定的文件夹
    for filename in os.listdir(folder_path):
        if filename.endswith('_MNDWI.tif'):  # 判断文件是否以 .tif 结尾
            tif_files.append(filename.split('_MNDWI')[0])  # 将符合条件的文件名添加到列表中
    # 定义已经处理的文件名列表
    # list_tif = ["UID_10000", "UID_10233"]  # 文件名示例
    return tif_files


def main():
    # 记录开始时间
    start_time = time.time()

    # 初始化要素
    longitude = 32.75
    latitude = -25.75
    # 确定格网范围
    lb_lon, lb_lat = get_grid_coordinates(longitude, latitude)  # 获取网格的左下角坐标
    rt_lon = lb_lon + 0.5
    rt_lat = lb_lat + 0.5
    boundary_grid = [lb_lon, lb_lat, rt_lon, rt_lat]
    print(boundary_grid)

    # 确定格网名称
    position = determine_map_position(longitude, latitude, if_print=1)

    # 已有的tif列表: ['10W41S', '110W28S', '112E26S', '113E25S', '113E26S',
    list_tif = find_exist_tif(folder_path=r'E:\_GoogleDrive\_DGS_GSV_Landsat')

    # 直接传递完整的资产路径
    task = crop_image_sentinel(
        boundary=boundary_grid,
        year=2015,  # 修改为你需要的年份
        output_path="_DGS_GSV_eez_Grids",
        img_name=position,
        exist_tif=list_tif,
    )

    # 记录结束时间
    end_time = time.time()
    # 计算差值即为程序运行时间
    formatted_time = format_time(end_time - start_time)
    print(f"Task completed in: {formatted_time}")


if __name__ == '__main__':
    main()
