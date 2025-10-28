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
from _tools import format_time
import subpixel_extraction
import geojson_to_polygon

# 输出路径
# output_mian_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData"

def repair_shp_hole(valid_pixel, multipolygons):
    """
    修复 shp 文件中的孔洞，步骤包括缓冲区分析、成对融合和反向缓冲。

    参数：
    valid_pixel (str)：输入有效像素的 shp 文件路径。
    multipolygons (str)：输出的修复后的多边形 shp 文件路径。
    """
    # 允许覆盖输出，设置为True
    arcpy.env.overwriteOutput = True

    # 处理：创建有效像素的缓冲区（扩展有效像素的边界）
    Polygon_Buffer = fr"in_memory\rhs_Buffer"  # 临时内存文件存储缓冲区结果
    arcpy.analysis.Buffer(
        in_features=valid_pixel,
        out_feature_class=Polygon_Buffer,
        buffer_distance_or_field="40 Meters",  # 设置缓冲区距离为 40 米
        line_side="FULL",  # 保证缓冲区生成完整边界
        line_end_type="FLAT",  # 缓冲区的端点类型为平坦
        dissolve_option="ALL",  # 合并所有缓冲区重叠部分
        method="GEODESIC"  # 使用大圆法计算缓冲区
    )

    # 处理：成对融合（对缓冲区结果进行成对融合，确保合并相邻区域）
    PairwiseDissolve = fr"in_memory\rhs_PairwiseDissolve"  # 临时内存文件存储融合结果
    arcpy.analysis.PairwiseDissolve(
        in_features=Polygon_Buffer,
        out_feature_class=PairwiseDissolve,
        multi_part="SINGLE_PART"  # 保证输出结果为单个部分
    )

    # 处理：反向缓冲（对融合结果进行反向缓冲，缩小边界）
    temp_Polygon_Buffer = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\filterValidPixel\rhs_buffer.shp"
    arcpy.analysis.Buffer(
        in_features=PairwiseDissolve,
        out_feature_class=temp_Polygon_Buffer,
        buffer_distance_or_field="-35 Meters",  # 设置反向缓冲区距离为 -35 米
        line_side="FULL",  # 保证反向缓冲区生成完整边界
        line_end_type="FLAT",  # 缓冲区的端点类型为平坦
        dissolve_option="ALL",  # 合并所有反向缓冲区重叠部分
        method="GEODESIC"  # 使用大圆法计算缓冲区
    )

    # 调用函数将多边形分割为单独的多边形
    split_multipolygons(input_shp=temp_Polygon_Buffer, output_shp=multipolygons)

def select_cou_poly(valid_pixel_after_shp, GID_shp, cou_valid_poly):
    """
    按位置选择有效的像素和给定的 ABW 边界，导出符合条件的要素，并清除选择。

    参数：
    valid_pixel_after_shp (str)：有效像素的输入 shp 文件路径。
    ABW_shp (str)：包含 ABW 边界的 shp 文件路径。
    coun_valid_poly (str)：导出符合条件的多边形结果的 shp 文件路径。
    """
    # 启用输出覆盖，允许文件覆盖
    arcpy.env.overwriteOutput = True

    # 按位置选择图层（选择那些其中心位于 ABW 边界内的有效像素） overlap_type="HAVE_THEIR_CENTER_IN" | INTERSECT
    select_layer = arcpy.management.SelectLayerByLocation(
        in_layer=[valid_pixel_after_shp], overlap_type="HAVE_THEIR_CENTER_IN", select_features=GID_shp,
        selection_type="NEW_SELECTION", invert_spatial_relationship="NOT_INVERT")
    # Process: 导出要素 (导出要素) (conversion)

    # 导出符合选择条件的要素到指定路径
    arcpy.conversion.ExportFeatures(in_features=select_layer, out_features=cou_valid_poly)

    # 清除当前图层选择
    arcpy.management.SelectLayerByAttribute(select_layer, "CLEAR_SELECTION")

    # 打印导出结果信息
    print(fr"- The polygon exported to {cou_valid_poly}")

def sel_val_cou_map(year, country, z_value=5):
    """
    选择并处理指定年份和国家的亚分辨率地图数据，包括图像降尺度、子像素提取、转换为多边形、修复空洞及筛选国家范围。

    参数：
    year (int)：年份。
    country (str)：国家代码（例如 'SIDS'）。
    """
    # 允许输出文件覆盖
    arcpy.env.overwriteOutput = True

    # 初始化年份和国家
    year_crop = year
    sids_cou = country

    # 读取 DBF 文件中的数据，返回记录列表（示例：[['1158', 'sids_grid_1158', -69.25, 11.75, '70W11Nru'], ...]）
    records_list = read_dbf_to_list(
        dbf_path=fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\d_SIDS_Boundary\SIDS_Grids\SIDS_grid_link\{sids_cou}_grid.dbf",
        if_print=0)
    print(records_list)

    # 遍历每条记录，进行后续处理
    for record in records_list:
        try:
            map_name = record[4]  # 获取地图名称（例如 '70W12Nlb'）

            # 步骤 1：中值合成亚分辨率图像
            input_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\SIDs_Grid_Y{(year_crop % 100):02}\{map_name}_ls578_Index.tif'
            output_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\bandInterpolation\{sids_cou}_{map_name}_zoom.tif"
            downscaling_by_interpolation(origin_tif=input_path, zoom_tif=output_path)

            # 步骤 2：过滤有效像元并执行子像素提取
            subpixel_tif_geojson = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Geojson\{sids_cou}_{map_name}_extract.geojson"
            subpixel_extraction.subpixel_extraction(
                input_tif=output_path,
                z_values=z_value,
                subpixel_tif=subpixel_tif_geojson
            )

            # 步骤 3：将 GeoJSON 文件转换为内存中的临时折线要素类
            ISID_JSONToFeature = fr"in_memory\svcm_JSONToFeature"
            arcpy.conversion.JSONToFeatures(in_json_file=subpixel_tif_geojson,
                                            out_features=ISID_JSONToFeature,
                                            geometry_type="POLYLINE")

            # 步骤 4：将折线要素转换为多边形
            ISID_Polygon = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\filterValidPixel\{sids_cou}_{map_name}_Polygon.shp"
            arcpy.management.FeatureToPolygon(in_features=[ISID_JSONToFeature],
                                              out_feature_class=ISID_Polygon,
                                              attributes="ATTRIBUTES")

            # 步骤 5：创建有效像素文件夹
            folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\e_SIDS_Shp\{year_crop}\{sids_cou}"
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            # 步骤 6：修复多边形中的空洞并生成修复后的多边形
            multi_polygon = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\filterValidPixel\{sids_cou}_{map_name}_after.shp"
            repair_shp_hole(valid_pixel=ISID_Polygon, multipolygons=multi_polygon)

            # 步骤 7：筛选国家范围
            cou_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\d_SIDS_Boundary\SIDS\AdminDivision\{sids_cou}.shp"
            cou_valid_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\e_SIDS_Shp\{year_crop}\{sids_cou}\{sids_cou}_{map_name}.shp"
            select_cou_poly(valid_pixel_after_shp=multi_polygon, GID_shp=cou_path, cou_valid_poly=cou_valid_path)

            # 打印处理完的路径
            print(f"- Countries processed {sids_cou}, results are saved in {cou_valid_path}")
        except Exception as e:
            print(e)

def mer_val_cou_map(GID_shp_list, merge_output):
    """
    合并指定的多个矢量图层并进行平滑处理，生成最终的合并结果。

    参数：
    GID_shp_list (list)：包含要合并的 shp 文件路径的列表。
    merge_output (str)：最终合并后的输出文件路径。
    """
    # 允许输出文件覆盖
    arcpy.env.overwriteOutput = True

    # 步骤 1：合并输入的多个图层（使用 Merge 工具）
    merge_layer = fr"in_memory\mvcm_merge"  # 创建临时内存图层用于存储合并结果
    arcpy.management.Merge(inputs=GID_shp_list, output=merge_layer, add_source="NO_SOURCE_INFO")

    # 步骤 2：对合并后的图层进行成对融合（使用 Pairwise Dissolve 工具）
    temp_merge_output = fr"in_memory\mvcm_temp_merge"  # 临时存储融合后的结果
    arcpy.analysis.PairwiseDissolve(
        in_features=merge_layer,
        out_feature_class=temp_merge_output,
        multi_part="MULTI_PART"  # 输出多个部分，而不是单一的几何部分
    )
    # 步骤 3：对融合后的面进行平滑处理（使用 SmoothPolygon 工具）
    temp_polygon = fr"in_memory\mvcm_temp_polygon"
    arcpy.management.FeatureToPolygon(in_features=[temp_merge_output],
                                      out_feature_class=temp_polygon,
                                      attributes="ATTRIBUTES")
    # 步骤 4：对合并后的图层进行成对融合（使用 Pairwise Dissolve 工具）
    temp_merge_output_2 = fr"in_memory\mvcm_temp_merge_2"  # 临时存储融合后的结果
    arcpy.analysis.PairwiseDissolve(
        in_features=temp_polygon,
        out_feature_class=temp_merge_output_2,
        multi_part="MULTI_PART"  # 输出多个部分，而不是单一的几何部分
    )

    # 步骤 5：对融合后的面进行平滑处理（使用 SmoothPolygon 工具）
    arcpy.cartography.SmoothPolygon(
        in_features=temp_merge_output_2,
        out_feature_class=merge_output,  # 输出平滑处理后的图层
        algorithm="PAEK",  # 使用 PAEK 算法进行平滑
        tolerance="60 Meters",  # 平滑的容忍度为 50 米
        endpoint_option="FIXED_ENDPOINT",  # 固定端点
        error_option="NO_CHECK"  # 不检查错误
    )

    # 打印平滑后的合并图层保存路径
    print(f"- The merged layer saved to {merge_output}\n")

def main():
    # 记录脚本开始执行的时间
    start_time = time.time()

    # 初始化任务配置参数
    for year in [2000]:
        year_crop = year  # 设置处理年份
        sids_cou = 'PRI'  # 确定国家 GID（例如：'ABW' 是国家的 GID）
        elevation = 10   # 指数高程

        # 设置路径，存放国家数据
        sids_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\e_SIDS_Shp\{year_crop}\{sids_cou}"
        # 步骤 1：构建副图幅（进行地图裁剪和子像素提取等操作）
        sel_val_cou_map(year=year_crop, country=sids_cou, z_value=elevation)
        # 步骤 2：列出指定文件夹中的所有国家图幅文件（.shp）
        map_names = list_files_with_extension(folder_path=sids_path, extension='.shp', if_print=0)
        # 创建包含文件路径的列表
        list_map_sids = [os.path.join(sids_path, var) for var in map_names]
        # 步骤 3：合并国家有效图幅
        sids_cou_output = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\e_SIDS_Shp\{year_crop}\{sids_cou}_{(year_crop % 100):02}.shp"
        mer_val_cou_map(GID_shp_list=list_map_sids, merge_output=sids_cou_output)

    # 记录脚本结束执行的时间，并计算执行时长
    end_time = time.time()
    formatted_time = format_time(end_time - start_time)
    print(f"Task completed in: {formatted_time}")


if __name__ == '__main__':
    main()