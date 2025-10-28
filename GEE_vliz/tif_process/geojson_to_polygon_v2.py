# -*- coding: utf-8 -*-
"""
此脚本由 ArcGIS ModelBuilder 自动生成，用于处理 GeoJSON 文件，生成平滑的多边形 shapefile。
包括的步骤有：将 JSON 转换为要素、平滑线条、创建多边形，以及计算几何属性。
"""

import arcpy
import time
import os
from sys import argv
import json
import fiona
from shapely.geometry import shape, mapping


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

    # 步骤 1：将 GeoJSON 文件转换为临时折线要素类  2.0756096839904785
    ISID_JSONToFeature = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\ISID_JSONToFeature.shp"
    # 读取GeoJSON文件
    with open(extract_geojson) as geojson_file:
        geojson_data = json.load(geojson_file)

    # 准备Shapefile的schema
    schema = {
        'geometry': 'LineString',
        'properties': [('z_value', 'float')]
    }

    # 写入Shapefile
    with fiona.open(ISID_JSONToFeature, 'w',
                    driver='ESRI Shapefile',
                    crs='EPSG:4326',  # 根据实际情况选择合适的CRS
                    schema=schema) as output:
        for feature in geojson_data['features']:
            geom = mapping(shape(feature['geometry']))
            output.write({
                'properties': feature['properties'],
                'geometry': geom
            })

    # 步骤 2：使用 PAEK 算法进行平滑   11.393041133880615
    ISID_SmoothLine = "in_memory\\ISID_SmoothLine"
    arcpy.cartography.SmoothLine(
        in_features=ISID_JSONToFeature,
        out_feature_class=ISID_SmoothLine,
        algorithm="PAEK",
        tolerance=f"{tolerance} Meters",
        endpoint_option="FIXED_CLOSED_ENDPOINT"
    )

    # 步骤 3：将平滑后的折线转换为多边形    11.723710060119629
    ISID_Polygon = "in_memory\\ISID_Polygon"
    arcpy.management.FeatureToPolygon(
        in_features=[ISID_SmoothLine],
        out_feature_class=ISID_Polygon,
        attributes="ATTRIBUTES"
    )

    # 步骤 5：融合多边形，确保结果为单一部分  10.05530047416687
    ISID_Dissolve = "in_memory\\ISID_Dissolve"
    arcpy.management.Dissolve(
        in_features=ISID_Polygon,
        out_feature_class=ISID_Dissolve,
        multi_part="SINGLE_PART",
        unsplit_lines="UNSPLIT_LINES"
    )

    # 步骤 6：计算多边形的面积（单位：平方公里）
    ISID_Polygon_Fixed_temp2 = arcpy.management.CalculateGeometryAttributes(
        in_features=ISID_Dissolve,
        geometry_property=[["Shape_Area", "AREA_GEODESIC"]],
        area_unit="SQUARE_KILOMETERS",
        coordinate_format="SAME_AS_INPUT"
    )[0]

    # 步骤 7：导出最终的多边形要素到指定的 shapefile 文件
    coast_line_shp_temp = "in_memory\\coast_line_shp_temp"
    arcpy.conversion.ExportFeatures(
        in_features=ISID_Polygon_Fixed_temp2,
        out_features=coast_line_shp_temp
    )

    # 从 GeoJSON 文件名中提取唯一标识符（UID），用于进一步处理
    temp_unique_id = os.path.basename(extract_geojson)
    unique_id = f"'{temp_unique_id.split('_')[0]}'"

    # 步骤 8：在 shapefile 中添加 UID_Grid 字段，并赋予唯一标识符
    arcpy.management.CalculateField(
        in_table=coast_line_shp_temp,
        field="UID_Grid",
        expression_type="PYTHON3",
        expression=unique_id,
        field_type="TEXT"
    )

    # 步骤 9：计算每个要素的大地面积和周长
    arcpy.management.CalculateGeometryAttributes(
        in_features=coast_line_shp_temp,
        geometry_property=[["Geo_Area", "AREA_GEODESIC"], ["Geo_Length", "PERIMETER_LENGTH_GEODESIC"]],
        length_unit="KILOMETERS",
        area_unit="SQUARE_KILOMETERS",
        coordinate_format="SAME_AS_INPUT"
    )

    # 步骤 10：导出要素
    arcpy.conversion.ExportFeatures(
        in_features=coast_line_shp_temp,
        out_features=coast_line_shp,
        where_clause="Geo_Area >= 0.0036")

    print(f"GeoJSON export shapefile: {coast_line_shp}")


if __name__ == '__main__':
    # 将包含折线要素的 GeoJSON 文件转换为平滑的多边形，并导出为 shapefile。
    # geojson_to_polygon(
    #     extract_geojson=r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Geojson\112E22Nrb_extract.geojson",
    #     tolerance=20,  # 平滑容差，单位：米
    #     coast_line_shp=r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Landsat_output\YY_2015\112E22Nrb_extract.shp"
    # )
    geojson_to_polygon(
        extract_geojson=r'C:\Users\23242\Desktop\draft1108\unet_resnet_2020_Band_1.geojson',
        tolerance=100,  # 平滑容差，单位：米
        coast_line_shp=r'C:\Users\23242\Desktop\draft1108\unet_resnet_2020_Band_1.shp'
    )
