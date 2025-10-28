# -*- coding:utf-8 -*-
"""
作者：23242
日期：2024年11月29日

功能：
1. 查找指定国家的 DBF 文件并提取影像列表。
2. 对影像列表中的每个影像执行矢量化处理，包括转线转面、空洞修复。
3. 根据指定国家边界进行空间筛选，生成有效范围内的矢量文件。
4. 计算矢量数据的面积和周长。
"""

import os
import time
import arcpy
from _tools import read_dbf_to_list
from _tools import downscaling_by_interpolation
from _tools import filter_valid_pixel_to_shp
from _tools import format_time

def select_valid_polygons(valid_pixel_shp, country_shp, output_shp):
    """
    按位置选择有效的像素多边形，并导出符合条件的结果。

    参数：
    valid_pixel_shp (str)：有效像素矢量文件路径。
    country_shp (str)：国家边界矢量文件路径。
    output_shp (str)：筛选后导出的矢量文件路径。
    """
    arcpy.env.overwriteOutput = True

    # 按位置选择中心点在国家边界内的有效像素:HAVE_THEIR_CENTER_IN | INTERSECT
    selected_layer = arcpy.management.SelectLayerByLocation(
        in_layer=[valid_pixel_shp],
        overlap_type="INTERSECT",
        select_features=country_shp,
        search_distance="1 Kilometers",
        selection_type="NEW_SELECTION"
    )

    # 导出符合条件的多边形
    arcpy.conversion.ExportFeatures(in_features=selected_layer, out_features=output_shp)

    # 清除选择
    arcpy.management.SelectLayerByAttribute(selected_layer, "CLEAR_SELECTION")

    print(f"- 有效多边形已导出至：{output_shp}")

def process_country_maps(year, country_code, threshold=5):
    """
    处理指定年份和国家的影像数据：
    1. 影像降尺度。
    2. 子像素提取。
    3. 转换为矢量文件。
    4. 筛选国家范围。

    参数：
    year (int)：处理年份。
    country_code (str)：国家代码（例如 'ABW'）。
    threshold (int)：像素有效性阈值。
    """
    arcpy.env.overwriteOutput = True

    # 获取影像文件列表
    dbf_path = rf"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\d_SIDS_Boundary\SIDS_Grids\SIDS_grid_link\{country_code}_grid.dbf"
    # dbf_path = rf"C:\Users\23242\Desktop\{country_code}_grid.dbf"
    records_list = read_dbf_to_list(dbf_path=dbf_path, if_print=0)
    print(f"读取到 {len(records_list)} 条记录。")

    for record in records_list:
        try:
            map_name = record[4]  # 地图名称

            # 步骤 1：影像降尺度
            input_tif = rf'E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\SIDs_Grid_Y{year % 100:02}\{map_name}_ls578_Index.tif'
            # input_tif = rf'E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\SIDs_Grid_Y{year % 100:02}_db\{map_name}_ls578_Index.tif'

            zoomed_tif = rf"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\bandInterpolation\{country_code}_{map_name}_zoom.tif"
            downscaling_by_interpolation(origin_tif=input_tif, zoom_tif=zoomed_tif)

            # 步骤 2：过滤有效像元并生成矢量
            valid_pixel_shp = rf"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\filterValidPixel\{country_code}_{map_name}_valid_pixel.shp"
            filter_valid_pixel_to_shp(input_tif_path=zoomed_tif, vector_output_path=valid_pixel_shp, threshold=threshold)

            # 步骤 3：创建输出文件夹
            output_folder = rf"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\e_SIDS_Shp\{country_code}\{year}"
            os.makedirs(output_folder, exist_ok=True)

            # 步骤 4：筛选国家范围
            country_shp = rf"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\d_SIDS_Boundary\SIDS\AdminDivision\{country_code}.shp"
            output_shp = rf"{output_folder}\{country_code}_{map_name}.shp"
            select_valid_polygons(valid_pixel_shp, country_shp, output_shp)

            # 删除临时文件
            if os.path.isfile(zoomed_tif):
                os.remove(zoomed_tif)
                print(f"临时文件已删除：{zoomed_tif}")

        except Exception as e:
            print(f"处理 {map_name} 时发生错误：{e}")

def main():
    """
    主函数：按年份和国家列表批量处理影像数据。
    """
    start_time = time.time()

    # 定义处理年份和国家列表
    years = [2015]
    # 57 国家
    country_codes = ["BMU",
"KNA",
"MSR",
"NRU",
"BRB",
"DMA",
"GUM",
"NIU",
"SGP",
"VCT",
"AIA",
"CYM",
"VGB",
"VIR",
"ABW",
"ASM",
"CUW",
"GRD",
"LCA",
"MTQ",
"SXM",
"ATG",
"GLP",
"STP",
"TCA",
"COM",
"WSM",
"TTO",
"MUS",
"TUV",
"PLW",
"MNP",
"JAM",
"PRI",
"CPV",
"TLS",
"TON",
"COK",
"BLZ",
"GNB",
"SYC",
"HTI",
"DOM",
"VUT",
"MDV",
"NCL",
"KIR",
"MHL",
"FSM",
"FJI",
"SUR",
"SLB",
"BHS",
"CUB",
"GUY",
"PYF",
"PNG",

]

    for year in years:
        for country_code in country_codes:
            elevation_threshold = 10

            print(f"开始处理 {year} 年 {country_code} 数据...")
            process_country_maps(year=year, country_code=country_code, threshold=elevation_threshold)

    # 记录总用时
    elapsed_time = time.time() - start_time
    print(f"任务完成，总耗时：{format_time(elapsed_time)}")


if __name__ == '__main__':
    main()
