# -*- coding:utf-8 -*-
"""
作者：23242
日期：2024年10月22日
"""
import arcpy
from time import time
from C_v3 import filter_image
from D_v2 import subpixel_extraction
from E_v2 import geojson_to_polygon


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
    image_input_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\c_YY_{gee_year}\UID_{uid_grid}_MNDWI.tif'

    # step 1: 过滤器处理 MNDWI
    temp_filter_image = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Filtering\UID_{uid_grid}_filtered.tif'
    filter_image(
        filter_input_path=image_input_path,
        filter_output_path=temp_filter_image
    )
    # step 2: 执行子像素提取，并生成 GeoJSON 文件
    temp_subpixel_extraction = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Geojson\UID_{uid_grid}_extract.geojson"
    subpixel_extraction(
        input_tif=temp_filter_image,
        z_values=10,
        subpixel_tif=temp_subpixel_extraction
    )
    # step 3: 过滤及优化边界生成shp
    temp_geojson_to_polygon = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Landsat_output\YY_{gee_year}\UID_{uid_grid}_extract.shp"
    geojson_to_polygon(
        extract_geojson=temp_subpixel_extraction,
        tolerance=15,  # 平滑的容差（米）
        coast_line_shp=temp_geojson_to_polygon
    )


if __name__ == "__main__":
    # 记录开始时间
    start_time = time()

    list_uid = ["UID_29714", "UID_29740", "UID_29753", "UID_30073", "UID_30099", "UID_30100",
                "UID_30113", "UID_30114", "UID_30433", "UID_30434", "UID_30459", "UID_30460", "UID_30474", "UID_30792",
                "UID_30820", "UID_30834", "UID_30836", "UID_31151", "UID_31152", "UID_31180", "UID_31181", "UID_31196",
                "UID_31510", "UID_31511", "UID_31541"]
    list_uid = ["38020"]
    for uid in list_uid:
        uid_num = uid.split('_')[-1]
        # 处理图像
        try:
            main(uid=uid_num, year='2015')
            # main(uid='36584', year='2015')
        except Exception as e:
            print(e)
    # 记录结束时间
    end_time = time()
    # 计算程序运行时间
    formatted_time = format_time(end_time - start_time)
    print(f"All tasks completed, run time: {formatted_time}")
