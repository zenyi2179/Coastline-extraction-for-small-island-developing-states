# -*- coding:utf-8 -*-
"""
作者：23242
日期：2024年12月04日

尝试利用 图幅tif 构建缩略图进行检查图幅问题所在

"""
# 1. 构建缩略图
# E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\Tif_Thumbnail_check
# E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\SIDs_Grid_Y00\6E0Nlb_ls578_Index.tif

import os
from osgeo import gdal
import numpy as np
from PIL import Image
from _tools import list_files_with_extension


def create_thumbnail(input_tif, output_png, threshold, thumbnail_size):
    """
    从单波段 GeoTIFF 创建栅格缩略图，筛选像元值大于阈值的像元。

    参数:
    input_tif (str): 输入 GeoTIFF 文件路径。
    output_png (str): 输出 PNG 文件路径。
    threshold (float): 像元值的阈值，大于该值的像元保留。
    thumbnail_size (tuple): 缩略图的尺寸 (宽, 高)。
    """
    # 打开 TIFF 文件
    dataset = gdal.Open(input_tif)
    if dataset is None:
        raise FileNotFoundError(f"无法打开文件: {input_tif}")

    # 读取栅格数据
    band = dataset.GetRasterBand(1)
    raster_data = band.ReadAsArray()

    # 筛选像元值大于阈值的部分
    binary_mask = np.where(raster_data > threshold, 255, 0).astype(np.uint8)

    # 使用 PIL 缩放栅格到指定大小
    image = Image.fromarray(binary_mask)
    image = image.resize(thumbnail_size, Image.Resampling.LANCZOS)  # 使用 LANCZOS 重采样

    # 保存为 PNG 文件
    image.save(output_png, format="PNG")
    print(f"Thumbnail has been saved to: {output_png}")


if __name__ == "__main__":
    # 输入和输出路径
    tif_year_list = [2000, 2010]
    # tif_year_list = [2020]
    for tif_year in tif_year_list:
        tif_folder = fr"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\SIDs_Grid_Y{(tif_year % 100):02}"
        png_folder = fr"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\Tif_Thumbnail_check\{tif_year}_5"
        tif_name_list = list_files_with_extension(folder_path=tif_folder, extension='.tif', if_print=1)
        for tif_name in tif_name_list:
            # tif 绝对路径
            tif_path = os.path.join(tif_folder, tif_name)
            temp_png_name = tif_name.split('_')[0]
            png_name = temp_png_name + '.png'
            png_path = os.path.join(png_folder, png_name)

            # input_tif = r"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\SIDs_Grid_Y00\6E0Nlb_ls578_Index.tif"
            # output_png = r"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\Tif_Thumbnail_check\6E0Nlb_ls578_Index.png"
            #
            # # 像元值阈值和缩略图大小
            # threshold = 10
            # thumbnail_size = (512, 512)

            # 创建缩略图
            create_thumbnail(input_tif=tif_path, output_png=png_path, threshold=5, thumbnail_size=(512, 512))
