# -*- coding: utf-8 -*-
"""
此脚本用于批量将指定文件夹下的 Shapefile (.shp) 文件转换为 GeoJSON 文件。
生成的 GeoJSON 文件将保存在指定的目标文件夹中。

生成日期：2024-09-10 15:39:13
"""

import os
import arcpy


def Model(shp, json):  # a_Feature to json
    """
    将 Shapefile 转换为 GeoJSON 文件。

    参数:
    shp (str): 输入的 Shapefile 文件路径。
    json (str): 输出的 GeoJSON 文件路径。
    """
    # 允许覆盖输出文件
    arcpy.env.overwriteOutput = True

    # 转换 Shapefile 为 GeoJSON
    arcpy.conversion.FeaturesToJSON(
        in_features=shp,
        out_json_file=json,
        format_json="NOT_FORMATTED",
        geoJSON="GEOJSON",
        outputToWGS84="WGS84",
        use_field_alias="USE_FIELD_NAME"
    )
    print(f'{json} conversion completed！')


def get_files_with_extension(directory, extension):
    """
    获取指定文件夹中具有特定扩展名的所有文件名。

    参数:
    directory (str): 文件夹路径。
    extension (str): 文件扩展名（包括点，例如 '.shp'）。

    返回:
    list: 包含指定扩展名文件名的列表。
    """
    # 规范化目录路径
    directory = os.path.normpath(directory)

    # 获取文件夹中的所有文件
    all_files = os.listdir(directory)

    # 筛选出指定扩展名的文件
    files_with_extension = [file for file in all_files if file.endswith(extension)]

    # 返回结果
    return files_with_extension


if __name__ == '__main__':
    # 设置全局环境变量
    # shp_folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\temp"
    shp_folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\b_Global_Island_Grid\_DGS_GSV_Grids"
    # json_folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\Geojson"
    json_folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\b_Global_Island_Grid\_DGS_GSV_Geojson"

    # 获取指定文件夹下所有后缀为 .shp 的文件名列表
    shp_files = get_files_with_extension(directory=shp_folder_path, extension='.shp')
    print(f"find '.shp' file: {shp_files}")

    # 遍历所有 .shp 文件
    for shp_name in shp_files:
        # 生成对应的 GeoJSON 文件名
        geo_name = shp_name.split('.')[0] + '.geojson'

        # 构建完整的文件路径
        feature_shp = os.path.join(shp_folder_path, shp_name)
        feature_geojson = os.path.join(json_folder_path, geo_name)

        # 调用 Model 函数批量转换 Shapefile 为 GeoJSON
        Model(shp=feature_shp, json=feature_geojson)