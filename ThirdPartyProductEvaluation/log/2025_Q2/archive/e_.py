import arcpy
import os
import geopandas as gpd


def geojson_to_shp(input_geojson, output_shp):
    """
    将 GeoJSON 文件转换为 Shapefile 文件。
    :param input_geojson: 输入的 GeoJSON 文件路径
    :param output_shp: 输出的 Shapefile 文件路径
    """
    gdf = gpd.read_file(input_geojson)
    gdf.to_file(output_shp, driver='ESRI Shapefile')
    print(f"[INFO] GeoJSON to Line: {output_shp}")


def line_to_polygon(input_shp, output_shp):
    """
    将线要素 Shapefile 转换为面要素 Shapefile。
    :param input_shp: 输入的线要素 Shapefile
    :param output_shp: 输出的面要素 Shapefile
    """
    temp_shp = r"in_memory\temp"
    arcpy.env.overwriteOutput = True

    # 线转换为面
    arcpy.management.FeatureToPolygon(
        in_features=[input_shp],
        out_feature_class=temp_shp,
        cluster_tolerance="",
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


def read_txt_to_list(file_path: str) -> list[str]:
    """
    读取文本文件内容为列表
    :param file_path: 文本文件路径
    :return: 行内容组成的字符串列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        print(f"[ERROR] 读取文件失败 {file_path}: {e}")
        return []


def get_files_absolute_paths(folder_path, suffix=None):
    """
    获取指定文件夹中所有指定后缀文件的绝对路径列表
    :param folder_path: 文件夹路径
    :param suffix: 文件后缀（如 '.shp'），若为 None 则返回所有文件
    :return: 文件路径列表
    """
    files_paths = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if suffix is None or file.endswith(suffix):
                files_paths.append(os.path.abspath(os.path.join(root, file)))
    return files_paths


def process_geojson_to_shp(sids, year, base_dir):
    """
    将指定国家和年份的 GeoJSON 批量转换为线状 Shapefile
    """
    input_dir = os.path.join(base_dir, "e_geojson", sids, year)
    output_dir = os.path.join(base_dir, "f_shp_line", sids, year)
    os.makedirs(output_dir, exist_ok=True)

    geojson_files = get_files_absolute_paths(input_dir, suffix=".geojson")

    for geojson_file in geojson_files:
        output_shp = os.path.join(output_dir, os.path.splitext(os.path.basename(geojson_file))[0] + ".shp")
        geojson_to_shp(geojson_file, output_shp)


def process_line_to_polygon(sids, year, base_dir):
    """
    将线状 Shapefile 批量转换为面状 Shapefile
    """
    input_dir = os.path.join(base_dir, "f_shp_line", sids, year)
    output_dir = os.path.join(base_dir, "g_shp_polygon", sids, year)
    os.makedirs(output_dir, exist_ok=True)

    shp_files = get_files_absolute_paths(input_dir, suffix=".shp")

    for shp_file in shp_files:
        output_shp = os.path.join(output_dir, os.path.basename(shp_file))
        line_to_polygon(shp_file, output_shp)


def main():
    # 设置基本路径（可修改）
    base_dir = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp"

    # 国家和年份列表（可自定义）
    years = ['2010', '2015']
    sids_list = read_txt_to_list("SIDS_37.txt")  # 读取国家 ID 列表

    for year in years:
        for sids in ['ATG']:  # 用于测试，或替换为 sids_list 遍历所有
            print(f"\n[INFO] 开始处理: 国家 = {sids}, 年份 = {year}")
            process_geojson_to_shp(sids, year, base_dir)
            process_line_to_polygon(sids, year, base_dir)


if __name__ == '__main__':
    main()
