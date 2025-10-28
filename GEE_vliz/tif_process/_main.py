# -*- coding:utf-8 -*-
"""
作者：23242
日期：2024年10月22日
"""
import arcpy
from time import time
from filter_image import filter_image
from subpixel_extraction import subpixel_extraction
from geojson_to_polygon_v2 import geojson_to_polygon
from list_files_with_extension import list_files_with_extension


def format_time(seconds):
    """
    格式化时间（秒）为 HH:MM:SS 格式。

    参数: seconds (float): 时间，单位为秒。

    返回: str: 格式化后的时间字符串。
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)

    return f"{hours:02}:{minutes:02}:{seconds:02}"

def main(uid, year):
    # step 0: 初始化要素
    uid_grid = uid
    gee_year = year
    # image_input_path = fr'E:\_GoogleDrive\SouthChinaSea\{uid_grid}_MNDWI.tif'
    image_input_path = fr'E:\_GoogleDrive\_draft\{uid_grid}_MNDWI.tif'

    # step 1: 过滤器处理 MNDWI
    temp_filter_image = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Filtering\{uid_grid}_filter.tif'
    filter_image(
        filter_input_path=image_input_path,
        filter_output_path=temp_filter_image
    )
    # step 2: 执行子像素提取，并生成 GeoJSON 文件
    temp_subpixel_extraction = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Geojson\{uid_grid}_extract.geojson"
    subpixel_extraction(
        input_tif=temp_filter_image,
        z_values=70,
        subpixel_tif=temp_subpixel_extraction
    )
    # step 3: 过滤及优化边界生成shp
    temp_geojson_to_polygon = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Landsat_output\YY_{gee_year}\{uid_grid}_extract.shp"
    geojson_to_polygon(
        extract_geojson=temp_subpixel_extraction,
        tolerance=15,  # 平滑的容差（米）
        coast_line_shp=temp_geojson_to_polygon
    )


if __name__ == "__main__":
    # 记录开始时间
    start_time = time()

    # 获取符合条件的文件名列表
    mndwi_files = list_files_with_extension(folder_path=r"E:\_GoogleDrive\SouthChinaSea", extension="_MNDWI.tif")
    # mndwi_files = list_files_with_extension(folder_path=r"E:\_GoogleDrive\_draft", extension="_MNDWI.tif")
    # ['108E18Nrb_MNDWI', '108E18Nru_MNDWI', '108E19Nrb_MNDWI',
    # list_uid = [filename.replace('.tif', '') for filename in mndwi_files]
    list_uid = ['2']

    for uid in list_uid:
        uid_num = uid.split('_')[0]
        # 处理图像
        try:
            main(uid=uid_num, year='2015')
        except Exception as e:
            print(e)
    # 记录结束时间
    end_time = time()
    # 计算程序运行时间
    formatted_time = format_time(end_time - start_time)
    print(f"All tasks completed, run time: {formatted_time}")
