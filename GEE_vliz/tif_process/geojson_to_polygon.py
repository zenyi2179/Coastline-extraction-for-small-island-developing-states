# -*- coding: utf-8 -*-
"""
此脚本由 ArcGIS ModelBuilder 自动生成，用于处理 GeoJSON 文件，生成平滑的多边形 shapefile。
包括的步骤有：将 JSON 转换为要素、平滑线条、创建多边形，以及计算几何属性。
"""

import arcpy
import os
from sys import argv


def geojson_to_polygon(extract_geojson, tolerance, coast_line_shp):
    """
    将包含折线要素的 GeoJSON 文件转换为平滑的多边形，并导出为 shapefile。

    参数：
    - extract_geojson (str): 输入的 GeoJSON 文件路径。
    - tolerance (float): 平滑线条时使用的容差值（单位：米）。
    - coast_line_shp (str): 输出的多边形 shapefile 文件路径。

    主要步骤：
    1. 将 GeoJSON 转换为折线要素。
    2. 根据给定的容差值平滑线条。
    3. 将平滑后的线条转换为多边形。
    4. 通过缓冲区修复可能的多边形空洞或缺口。
    5. 融合多边形为单一的几何对象。
    6. 计算几何属性（面积、长度）。
    7. 导出包含计算属性的 shapefile。
    """

    # 设置环境变量，允许覆盖输出文件
    arcpy.env.overwriteOutput = True

    # 步骤 1：将 GeoJSON 文件转换为临时折线要素类
    ISID_JSONToFeature = "in_memory\\ISID_JSONToFeature"
    arcpy.conversion.JSONToFeatures(
        in_json_file=extract_geojson,
        out_features=ISID_JSONToFeature,
        geometry_type="POLYLINE"
    )

    # 步骤 2：使用 PAEK 算法进行平滑
    ISID_SmoothLine = "in_memory\\ISID_SmoothLine"
    arcpy.cartography.SmoothLine(
        in_features=ISID_JSONToFeature,
        out_feature_class=ISID_SmoothLine,
        algorithm="PAEK",
        tolerance=f"{tolerance} Meters",
        endpoint_option="FIXED_CLOSED_ENDPOINT"
    )

    # 步骤 3：将平滑后的折线转换为多边形
    ISID_Polygon = "in_memory\\ISID_Polygon"
    arcpy.management.FeatureToPolygon(
        in_features=[ISID_SmoothLine],
        out_feature_class=ISID_Polygon,
        attributes="ATTRIBUTES"
    )

    # 步骤 4：缓冲处理，修复多边形中的小空隙（例如 20 米缓冲后再反向缓冲）
    ISID_Polygon_Fixed = "in_memory\\ISID_Polygon_Fixed"
    arcpy.analysis.Buffer(
        in_features=ISID_Polygon,
        out_feature_class="in_memory\\ISID_Polygon_Fixed_temp",
        buffer_distance_or_field="20 Meters",
        line_side="FULL",
        line_end_type="ROUND",
        dissolve_option="NONE",
        method="PLANAR"
    )

    # 步骤 5：融合多边形，确保结果为单一部分
    ISID_Dissolve = "in_memory\\ISID_Dissolve"
    arcpy.management.Dissolve(
        in_features="in_memory\\ISID_Polygon_Fixed_temp",
        out_feature_class=ISID_Dissolve,
        multi_part="SINGLE_PART",
        unsplit_lines="UNSPLIT_LINES"
    )

    # 反向缓冲恢复到原始边界
    arcpy.analysis.Buffer(
        in_features=ISID_Dissolve,
        out_feature_class=ISID_Polygon_Fixed,
        buffer_distance_or_field="-20 Meters",
        line_side="FULL",
        line_end_type="ROUND",
        dissolve_option="NONE",
        method="PLANAR"
    )

    # 步骤 6：计算多边形的面积（单位：平方公里）
    ISID_Polygon_Fixed_temp2 = arcpy.management.CalculateGeometryAttributes(
        in_features=ISID_Polygon_Fixed,
        geometry_property=[["Shape_Area", "AREA_GEODESIC"]],
        area_unit="SQUARE_KILOMETERS",
        coordinate_format="SAME_AS_INPUT"
    )[0]

    # 步骤 7：导出最终的多边形要素到指定的 shapefile 文件
    arcpy.conversion.ExportFeatures(
        in_features=ISID_Polygon_Fixed_temp2,
        out_features=coast_line_shp
    )

    # 从 GeoJSON 文件名中提取唯一标识符（UID），用于进一步处理
    temp_unique_id = os.path.basename(extract_geojson)
    unique_id = f"'{temp_unique_id.split('_')[0]}'"

    # 步骤 8：在 shapefile 中添加 UID_Grid 字段，并赋予唯一标识符
    arcpy.management.CalculateField(
        in_table=coast_line_shp,
        field="UID_Grid",
        expression_type="PYTHON3",
        expression=unique_id,
        field_type="TEXT"
    )

    # 步骤 9：计算每个要素的大地面积和周长
    arcpy.management.CalculateGeometryAttributes(
        in_features=coast_line_shp,
        geometry_property=[["Geo_Area", "AREA_GEODESIC"], ["Geo_Length", "PERIMETER_LENGTH_GEODESIC"]],
        length_unit="KILOMETERS",
        area_unit="SQUARE_KILOMETERS",
        coordinate_format="SAME_AS_INPUT"
    )

    print(f"GeoJSON export shapefile: {coast_line_shp}")


if __name__ == '__main__':
    # 将包含折线要素的 GeoJSON 文件转换为平滑的多边形，并导出为 shapefile。
    geojson_to_polygon(
        extract_geojson=r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Geojson\114E22Nlb_extract.geojson",
        tolerance=15,  # 平滑容差，单位：米
        coast_line_shp=r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Landsat_output\YY_2015\114E22Nlb_extract.shp"
    )
