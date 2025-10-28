# -*- coding:utf-8 -*-
"""
作者：23242
日期：2024年11月29日

找到对应国家dbf：ABW.dbf 找到对应的影像列表
将列表影像逐一进行矢量化面要素，转线转面消除空洞
通过 ABW.shp 进行相交管理识别有效范围
融合输出计算面积及周长

"""
import os
import time
import arcpy
from _tools import read_dbf_to_list
from _tools import list_files_with_extension
from _tools import downscaling_by_interpolation
from _tools import filter_valid_pixel_to_shp
from _tools import split_multipolygons


def repair_shp_hole(valid_pixel, multipolygons):
    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    # Process: 要素转面 (要素转面) (management)
    FeatureToPoly = fr"in_memory\FeatureToPoly"
    arcpy.management.FeatureToPolygon(in_features=[valid_pixel], out_feature_class=FeatureToPoly,
                                      attributes="ATTRIBUTES")

    # Process: 缓冲区 (缓冲区) (analysis)
    Polygon_Buffer = fr"in_memory\Buffer"
    arcpy.analysis.Buffer(in_features=FeatureToPoly, out_feature_class=Polygon_Buffer,
                          buffer_distance_or_field="40 Meters", line_side="FULL", line_end_type="FLAT",
                          dissolve_option="ALL", method="GEODESIC")

    # Process: 缓冲区 (缓冲区) (analysis)
    arcpy.analysis.Buffer(in_features=Polygon_Buffer, out_feature_class=multipolygons,
                          buffer_distance_or_field="-40 Meters", line_side="FULL", line_end_type="FLAT",
                          dissolve_option="ALL", method="GEODESIC")

    # # Process: 成对融合 (成对融合) (analysis)
    # arcpy.analysis.PairwiseDissolve(in_features=FeatureToPoly, out_feature_class=multipolygons,
    #                                 multi_part="SINGLE_PART")

    print(fr"Split multipolygons saved at {multipolygons}")


def select_coun_poly(valid_pixel_after_shp, ABW_shp, coun_valid_poly):  # 模型6

    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    # Process: 按位置选择图层 (按位置选择图层) (management)
    select_layer = arcpy.management.SelectLayerByLocation(
        in_layer=[valid_pixel_after_shp], overlap_type="INTERSECT", select_features=ABW_shp,
        selection_type="NEW_SELECTION", invert_spatial_relationship="NOT_INVERT")

    # Process: 导出要素 (导出要素) (conversion)
    arcpy.conversion.ExportFeatures(in_features=select_layer, out_features=coun_valid_poly)

    # 清除选择
    arcpy.management.SelectLayerByAttribute(select_layer, "CLEAR_SELECTION")

    print(fr"Export valid country at {coun_valid_poly}")


def main():
    # 记录脚本开始执行的时间
    start_time = time.time()

    # 初始化任务配置参数
    year_crop = 2000  # 设置下载年份

    # 确定国家 GID
    sids_coun = 'ABW'

    # 调用函数读取DBF文件内容，并返回列表形式的数据
    # [['1158', 'sids_grid_1158', -69.25, 11.75, '70W11Nru'], ['1159', 'sids_grid_1159', -68.75, 11.75, '69W11Nlu'],
    records_list = read_dbf_to_list(
        dbf_path=fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\d_SIDS_Boundary\SIDS_Grids\SIDS_grid_link\{sids_coun}_grid.dbf',
        if_print=0)
    print(records_list)

    for record in records_list:
        map_name = record[4]  # '70W12Nlb'

        # 中值合成亚分辨率图像
        input_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\SIDs_Grid_Y{(year_crop % 100):02}\{map_name}_ls578_Index.tif'
        output_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\bandInterpolation\zoom_tif.tif'
        downscaling_by_interpolation(origin_tif=input_path, zoom_tif=output_path)

        # 过滤有效像元
        input_tif_path = output_path
        vector_output_path = r'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\filterValidPixel\valid_pixel.shp'
        filter_valid_pixel_to_shp(input_tif_path, vector_output_path, threshold=5)

        # 创建有效文件夹
        folder_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\e_SIDS_Shp\{year_crop}\{sids_coun}'
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        # 修复空洞并归类
        multi_polygon = r'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\filterValidPixel\valid_pixel_after.shp'
        repair_shp_hole(valid_pixel=vector_output_path, multipolygons=multi_polygon)

        # 筛选国家范围
        coun_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\d_SIDS_Boundary\SIDS\AdminDivision\{sids_coun}.shp'
        coun_valid_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\e_SIDS_Shp\{year_crop}\{sids_coun}\{sids_coun}_{map_name}.shp'
        select_coun_poly(valid_pixel_after_shp=multi_polygon, ABW_shp=coun_path, coun_valid_poly=coun_valid_path)


if __name__ == '__main__':
    main()
