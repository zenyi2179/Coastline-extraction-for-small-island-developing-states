# -*- coding: utf-8 -*-
"""
将沿海国家的图幅依据最新的国家范围进行裁剪
"""

import os
import arcpy


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


if __name__ == '__main__':
    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    # 获得文件夹下所有后缀名称为 .shp 的文件名称
    # year_list = [2000, 2010, 2020]
    gid_sids = 'GUY'
    year_list = [2015]

    for year in year_list:
        folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\e_SIDS_Shp\{gid_sids}\{year}"
        map_shps = list_files_with_extension(folder_path, extension='.shp', if_print=0)
        map_path = [os.path.join(folder_path, map_shp) for map_shp in map_shps]

        boundary_GID = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\e_SIDS_Shp\{gid_sids}\boundary_{gid_sids}.shp"

        for sids_map in map_path:
            map_shp_name = sids_map.split(str(year))[-1]
            folder_path_new = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\e_SIDS_Shp\{gid_sids}_new\{year}"
            map_new = folder_path_new + map_shp_name

            arcpy.analysis.Clip(in_features=sids_map, clip_features=boundary_GID, out_feature_class=map_new)
            print(map_new, 'success!')
