# -*- coding: utf-8 -*-
"""
由 ArcGIS ModelBuilder
此脚本通过 ArcPy 工具处理 GeoJSON 文件，生成平滑后的多边形 shapefile。
包括的步骤有：将 JSON 转为要素、平滑线条、创建多边形，以及计算几何属性。
"""
import arcpy
import os
from sys import argv


def geojson_to_polygon(extract_geojson, tolerance, coast_line_shp):
    """
    将包含折线要素的 GeoJSON 文件转换为平滑的多边形，并导出为 shapefile。

    参数：
    - extract_geojson: 输入的 GeoJSON 文件路径
    - tolerance: 平滑线条时使用的容差值（以米为单位）
    - coast_line_shp: 输出的多边形 shapefile 文件路径

    主要步骤：
    1. 将 JSON 转换为折线要素。
    2. 根据给定的容差值平滑线条。
    3. 将平滑后的线条转换为多边形。
    4. 通过缓冲区修复可能的多边形空洞或缺口。
    5. 融合多边形为单一的几何对象。
    6. 计算几何属性（面积、长度）。
    7. 导出包含计算属性的 shapefile。
    """

    # 允许覆盖现有输出文件
    arcpy.env.overwriteOutput = True

    # 步骤 1：将 GeoJSON 文件转换为内存中的临时折线要素类
    ISID_JSONToFeature = "in_memory\\ISID_JSONToFeature"
    arcpy.conversion.JSONToFeatures(in_json_file=extract_geojson,
                                    out_features=ISID_JSONToFeature,
                                    geometry_type="POLYLINE")

    # 步骤 2：使用 PAEK 算法，根据给定的容差平滑折线
    ISID_SmoothLine = "in_memory\\ISID_SmoothLine"
    with arcpy.EnvManager(transferGDBAttributeProperties="false"):
        arcpy.cartography.SmoothLine(in_features=ISID_JSONToFeature,
                                     out_feature_class=ISID_SmoothLine,
                                     algorithm="PAEK",
                                     tolerance=fr"{tolerance} Meters",
                                     endpoint_option="FIXED_CLOSED_ENDPOINT")

    # 步骤 3：将平滑后的折线要素转换为多边形
    ISID_Polygon = "in_memory\\ISID_Poly"
    arcpy.management.FeatureToPolygon(in_features=[ISID_SmoothLine],
                                      out_feature_class=ISID_Polygon,
                                      attributes="ATTRIBUTES")

    # 步骤 4：通过缓冲区修复小的空隙或缺口（30 米缓冲，然后反向缓冲）
    ISID_Polygon_Fixed = "in_memory\\ISID_Polygon_Fixed"
    arcpy.analysis.Buffer(in_features=ISID_Polygon,
                          out_feature_class="in_memory\\ISID_Polygon_Fixed_temp",
                          buffer_distance_or_field="30 Meters",
                          line_side="FULL",
                          line_end_type="ROUND",
                          dissolve_option="NONE",
                          method="PLANAR")

    # 步骤 5：融合多边形，确保结果为单一部分，并移除内部间隙
    ISID_Dissolve = fr"in_memory\ISID_Dissolve"
    arcpy.management.Dissolve(in_features="in_memory\\ISID_Polygon_Fixed_temp",
                              out_feature_class=ISID_Dissolve,
                              multi_part="SINGLE_PART",
                              unsplit_lines="UNSPLIT_LINES")

    # 反向缓冲以恢复到原始边界
    arcpy.analysis.Buffer(in_features=ISID_Dissolve,
                          out_feature_class=ISID_Polygon_Fixed,
                          buffer_distance_or_field="-30 Meters",
                          line_side="FULL",
                          line_end_type="ROUND",
                          dissolve_option="NONE",
                          method="PLANAR")

    # 步骤 6：计算多边形的面积（单位：平方公里）
    ISID_Polygon_Fixed_temp2 = arcpy.management.CalculateGeometryAttributes(
        in_features=ISID_Polygon_Fixed,
        geometry_property=[["Shape_Area", "AREA_GEODESIC"]],
        area_unit="SQUARE_KILOMETERS",
        coordinate_format="SAME_AS_INPUT"
    )[0]

    # 步骤 7：导出最终的多边形要素到输出的 shapefile
    arcpy.conversion.ExportFeatures(in_features=ISID_Polygon_Fixed_temp2,
                                    out_features=coast_line_shp)

    # 从 GeoJSON 文件名中提取唯一标识符，用于进一步计算
    temp_unique_id = extract_geojson.split("\\")[-1]
    unique_id = temp_unique_id.split('_')[1]

    # 步骤 8：根据提取的唯一标识符，向 shapefile 添加 UID_Grid 字段
    arcpy.management.CalculateField(in_table=coast_line_shp,
                                    field="UID_Grid",
                                    expression=unique_id,
                                    expression_type="PYTHON3",
                                    field_type="TEXT")

    # 步骤 9：为每个要素计算大地面积和周长
    arcpy.management.CalculateGeometryAttributes(
        in_features=coast_line_shp,
        geometry_property=[["Geo_Area", "AREA_GEODESIC"], ["Geo_Length", "PERIMETER_LENGTH_GEODESIC"]],
        length_unit="KILOMETERS",
        area_unit="SQUARE_KILOMETERS",
        coordinate_format="SAME_AS_INPUT"
    )

    print(f"GeoJSON export shapefile: {coast_line_shp}")


if __name__ == '__main__':
    # 全局环境设置
    geojson_to_polygon(
        extract_geojson=fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Geojson\UID_36584_extract.geojson",
        tolerance=15,  # 平滑的容差（米）
        coast_line_shp=fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Landsat_output\YY_2015\UID_36584_extract.shp"
    )
