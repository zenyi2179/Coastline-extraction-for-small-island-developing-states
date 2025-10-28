import arcpy
arcpy.env.overwriteOutput = True


def line_to_polygon(input_shp, output_shp):
    """
    将线要素 Shapefile 转换为面要素 Shapefile。
    :param input_shp: 输入的线要素 Shapefile
    :param output_shp: 输出的面要素 Shapefile
    """
    temp_shp = r"in_memory\temp"

    # 线转换为面
    arcpy.management.FeatureToPolygon(
        in_features=[input_shp],
        out_feature_class=temp_shp,
        cluster_tolerance="0.001 Meters",  # 设置容差
        attributes="ATTRIBUTES",
        label_features=""
    )

    # 对面要素进行 Dissolve（可选）
    arcpy.management.Dissolve(
        in_features=temp_shp,
        out_feature_class=output_shp,
        dissolve_field=[],
        statistics_fields=[],
        multi_part="SINGLE_PART",
        unsplit_lines="DISSOLVE_LINES",
        concatenation_separator=""
    )

    print(f"[INFO] Line to Polygon 并保存: {output_shp}")
#
# def line_to_polygon(input_shp, output_shp):
#     """
#     将线要素 Shapefile 转换为面要素 Shapefile。
#     :param input_shp: 输入的线要素 Shapefile
#     :param output_shp: 输出的面要素 Shapefile
#     """
#
#     # 线转换为面
#     arcpy.management.FeatureToPolygon(
#         in_features=[input_shp],
#         out_feature_class=output_shp,
#         cluster_tolerance="0.001 Meters",  # 设置容差
#         attributes="ATTRIBUTES",
#         label_features=""
#     )
#
#     print(f"[INFO] Line to Polygon 并保存: {output_shp}")

def geojson_to_polygon(input_geojson, output_shp):
    temp_shp_line = fr'in_memory\temp_line'

    arcpy.conversion.JSONToFeatures(
        in_json_file=input_geojson, out_features=temp_shp_line, geometry_type='POLYLINE')

    line_to_polygon(input_shp=temp_shp_line, output_shp=output_shp)

def main():
    json_input = fr"C:\Users\23042\Desktop\test\43E13Sru_ls578_re_fi.geojson"
    polygon_output = fr"C:\Users\23042\Desktop\test\43E13Sru_ls578_polygon.shp"

    geojson_to_polygon(json_input, polygon_output)

if __name__ == '__main__':
    main()