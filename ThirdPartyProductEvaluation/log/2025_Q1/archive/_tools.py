# -*- coding:utf-8 -*-
import os
import math
from dbfread import DBF
import rasterio
from rasterio.warp import calculate_default_transform
from rasterio.enums import Resampling
from pyproj import CRS
from scipy.ndimage import zoom
import rasterio
import numpy as np
from rasterio import mask
from rasterio.enums import Resampling
import rasterio
from rasterio import features
import numpy as np
import fiona
from fiona.crs import from_epsg
import geopandas as gpd
from shapely.geometry import MultiPolygon
import pandas as pd


def determine_map_position(longitude, latitude, if_print=1):
    """
    根据给定的经度和纬度确定地图上的位置，并返回一个格式化的字符串。

    参数:
    - longitude (float): 经度值
    - latitude (float): 纬度值
    - if_print (int): 是否打印结果，默认为1（打印）

    返回:
    - str: 格式化的地图位置字符串

    示例:
    - determine_map_position(-73.997826, 40.744754)
    coordinate [-73.997826, 40.744754] translate to: 74W40Nr.
    """

    # 初始化经度的整数部分
    abs_var_lon = int(abs(longitude - 1)) if longitude < 0 else int(abs(longitude))
    var_lon = -abs_var_lon if longitude < 0 else abs_var_lon

    # 初始化纬度的整数部分
    abs_var_lat = int(abs(latitude - 1)) if latitude < 0 else int(abs(latitude))
    var_lat = -abs_var_lat if latitude < 0 else abs_var_lat

    # 确定东西方向标识符
    var_WE = 'W' if longitude < 0 else 'E'

    # 确定南北方向标识符
    var_NS = 'N' if latitude > 0 else 'S'

    # 根据输入值和整数部分计算左右方向标识符
    var_lr = 'l' if longitude < var_lon + 0.5 else 'r'

    # 根据输入值和整数部分计算上下方向标识符
    var_ub = 'b' if latitude < var_lat + 0.5 else 'u'

    # 格式化输出为所需的字符串格式
    map_position = fr'{abs_var_lon}{var_WE}{abs_var_lat}{var_NS}{var_lr}{var_ub}'

    # 如果 if_print 为 1，则打印结果
    if if_print:
        print(fr"coordinate [{longitude}, {latitude}] translate to: {map_position}.")

    return map_position


def get_grid_coordinates(longitude, latitude):
    # 计算经度的网格左下角坐标
    grid_longitude = math.floor(longitude * 2) / 2
    # 计算纬度的网格左下角坐标
    grid_latitude = math.floor(latitude * 2) / 2

    return grid_longitude, grid_latitude


def read_dbf_to_list(dbf_path, if_print=0):
    """
    读取 DBF 文件并将内容存储为二维列表。

    参数:
    dbf_path (str): DBF 文件的路径。
    if_print (int): 是否打印二维列表的开关，0表示不打印，1表示打印。

    返回:
    list_of_records (list): 二维列表，每个子列表代表一条记录。
    """
    list_of_records = []
    dbf = DBF(dbf_path, encoding='utf-8')  # 打开 DBF 文件并设置编码为 'utf-8'

    # 获取并打印 DBF 文件的字段名称，即表头
    # print("Field names:", [field.name for field in dbf.fields])

    # 遍历 DBF 文件中的每条记录
    for record in dbf:
        # 将每条记录的值转换为列表，并添加到二维列表中
        list_of_records.append(list(record.values()))

    # 根据 if_print 参数决定是否打印二维列表
    if if_print:
        print("Records list:")
        print(list_of_records)

    return list_of_records


def list_files_with_extension(folder_path, extension, if_print=0):
    """
    获取指定文件夹中所有以指定扩展名结尾的文件名称，并返回文件名列表。

    参数:
        folder_path (str): 文件夹的路径。
        extension (str): 需要筛选的文件扩展名，例如 '_MNDWI.tif'。

    返回:
        list: 文件名列表，包含所有符合条件的文件名称。
    """
    matching_files = []

    # 检查文件夹是否存在
    if not os.path.isdir(folder_path):
        raise ValueError(f"指定的路径不存在或不是文件夹: {folder_path}")

    # 遍历文件夹中的文件，筛选符合扩展名的文件
    for filename in os.listdir(folder_path):
        if filename.endswith(extension):
            matching_files.append(filename)

    if if_print:
        print(matching_files)

    return matching_files


def downscaling_by_interpolation(origin_tif, zoom_tif, zoom_ratio=2):
    # 设置输入输出路径
    input_path = origin_tif
    output_path = zoom_tif

    # 指定输出的坐标系 WGS 84
    target_crs = CRS.from_epsg(4326)  # WGS 84 EPSG:4326

    # 打开输入图像
    with rasterio.open(input_path) as src:
        # 读取原始图像的元数据
        src_crs = src.crs  # 原始坐标系
        transform = src.transform  # 原始的地理变换矩阵
        band_count = src.count  # 波段数量

        # 使用双线性插值法降尺度，提高分辨率（例如2倍分辨率）
        scale_factor = zoom_ratio

        # 创建用于存储重采样后数据的空列表
        resampled_bands = []

        # 对每个波段进行处理
        for band in range(1, band_count + 1):
            data = src.read(band)  # 读取每个波段的数据
            resampled_data = zoom(data, scale_factor, order=1)  # 双线性插值
            resampled_bands.append(resampled_data)  # 将重采样后的波段数据添加到列表中

        # 计算新的地理变换矩阵
        new_transform, new_width, new_height = calculate_default_transform(
            src_crs, target_crs, src.width * scale_factor, src.height * scale_factor, *src.bounds
        )

        # 写入新的图像文件
        with rasterio.open(
                output_path,
                'w',
                driver='GTiff',
                height=new_height,
                width=new_width,
                count=band_count,  # 保持波段数量不变
                dtype=resampled_bands[0].dtype,
                crs=target_crs,
                transform=new_transform,
        ) as dst:
            # 将每个波段写入新的文件
            for band in range(1, band_count + 1):
                dst.write(resampled_bands[band - 1], band)

    print(f"Resampled image saved at {output_path}")


def filter_valid_pixel_to_shp(input_tif_path, vector_output_path, threshold=5):
    """
    提取栅格中像元值大于等于阈值的部分，并直接输出为矢量面要素 (SHP 文件)。

    :param input_tif_path: 输入栅格文件路径
    :param vector_output_path: 输出矢量文件路径 (.shp)
    :param threshold: 像元值的阈值，默认值为 5
    """
    # 打开输入栅格文件
    with rasterio.open(input_tif_path) as src:
        # 读取栅格数据
        band = src.read(1)  # 假设处理的是单波段栅格
        mask = band >= threshold  # 创建掩膜

        # 获取矢量化后的 shapes
        shapes = features.shapes(mask.astype(np.int16), transform=src.transform)

        # 定义 SHP 文件的 schema 和坐标系
        schema = {
            'geometry': 'Polygon',
            'properties': {'value': 'int'},
        }
        crs = CRS.from_epsg(src.crs.to_epsg())  # 使用新版本的 CRS.from_epsg

        # 写入 SHP 文件
        with fiona.open(vector_output_path, 'w', driver='ESRI Shapefile',
                        crs=crs, schema=schema) as shp:
            for shape, value in shapes:
                if value == 1:  # 保留有效区域
                    shp.write({
                        'geometry': shape,
                        'properties': {'value': int(threshold)},
                    })

        print(f"Vector file saved at {vector_output_path}")

#
def split_multipolygons(input_shp, output_shp):
    """
    读取Shapefile文件，将其中的MultiPolygon对象拆分为单独的Polygon，并保存为新的Shapefile文件。

    :param input_shp: 输入的Shapefile文件路径
    :param output_shp: 输出的Shapefile文件路径
    """
    # 读取输入Shapefile文件
    gdf = gpd.read_file(input_shp)

    # 创建一个空的列表，用于保存拆分后的数据行
    rows_list = []

    # 遍历每个几何对象，检查是否为MultiPolygon类型
    for idx, row in gdf.iterrows():
        geometry = row['geometry']
        if isinstance(geometry, MultiPolygon):
            # 将MultiPolygon拆分为单独的Polygon
            for poly in geometry.geoms:
                new_row = row.copy()
                new_row['geometry'] = poly
                rows_list.append(new_row)
        else:
            rows_list.append(row)

    # 将结果存储到新的GeoDataFrame中
    new_gdf = pd.concat([pd.DataFrame([row]) for row in rows_list], ignore_index=True)
    new_gdf = gpd.GeoDataFrame(new_gdf, geometry='geometry', crs=gdf.crs)

    # 保存为新的Shapefile文件
    new_gdf.to_file(output_shp)

    print(fr"Split multipolygons saved at {output_shp}")

# def split_multipolygons(input_shp, output_shp):
#     """
#     读取Shapefile文件，将其中的MultiPolygon对象拆分为单独的Polygon，并保存为新的Shapefile文件。
#
#     :param input_shp: 输入的Shapefile文件路径
#     :param output_shp: 输出的Shapefile文件路径
#     """
#     # 读取输入Shapefile文件
#     gdf = gpd.read_file(input_shp)
#
#     # 创建一个列表，用于保存拆分后的数据行
#     rows_list = []
#
#     # 遍历每个几何对象，检查是否为MultiPolygon类型
#     for _, row in gdf.iterrows():
#         geometry = row['geometry']
#         if isinstance(geometry, MultiPolygon):
#             # 将MultiPolygon拆分为单独的Polygon
#             for poly in geometry.geoms:
#                 # 使用row.copy()来保持原始属性
#                 new_row = row.copy()
#                 new_row['geometry'] = poly
#                 rows_list.append(new_row)
#         else:
#             rows_list.append(row)
#
#     # 将结果转换为GeoDataFrame，避免逐行拼接
#     new_gdf = gpd.GeoDataFrame(rows_list, geometry='geometry', crs=gdf.crs)
#
#     # 保存为新的Shapefile文件
#     new_gdf.to_file(output_shp)
#
#     print(f"Split multipolygons saved at {output_shp}")


def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)

    return f"{hours:02}:{minutes:02}:{seconds:02}"


def main():
    pass


if __name__ == '__main__':
    main()
