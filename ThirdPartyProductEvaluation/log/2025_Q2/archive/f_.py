import arcpy
import geopandas as gpd
import pandas as pd  # ← 你漏掉的部分
import os
from shapely.ops import unary_union

def merge_shapefiles_gpd(input_folder, extra_shp, output_shp):
    gdf_list = []

    for fname in os.listdir(input_folder):
        if fname.endswith('.shp'):
            gdf = gpd.read_file(os.path.join(input_folder, fname))
            gdf_list.append(gdf)

    gdf_extra = gpd.read_file(extra_shp)
    gdf_list.append(gdf_extra)

    # 合并属性表 + 保留地理信息
    merged_gdf = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True), crs=gdf_list[0].crs)

    # Dissolve 合并所有几何体，解决边界空洞
    dissolved = unary_union(merged_gdf.geometry)

    # 将合并后结果包装成 GeoDataFrame 并保存
    cleaned_gdf = gpd.GeoDataFrame(geometry=[dissolved], crs=merged_gdf.crs)
    os.makedirs(os.path.dirname(output_shp), exist_ok=True)
    cleaned_gdf.to_file(output_shp)

    print(f"[GPD] Polygon Merge: {output_shp}")

def fix_shapefiles(shp_input, shp_fixed):
    arcpy.env.overwriteOutput = True
    # 转线
    shp_temp_line = "in_memory/shp_temp_line"
    arcpy.management.FeatureToLine(
        in_features=[shp_input],
        out_feature_class=shp_temp_line, cluster_tolerance="", attributes="ATTRIBUTES")
    # 转面
    shp_temp_polygon = "in_memory/shp_temp_polygon"
    arcpy.FeatureToPolygon_management(
        in_features=[shp_temp_line],
        out_feature_class=shp_temp_polygon)
    # 融合分要素
    shp_dissolved = shp_fixed
    # MULTI_PART—输出中将包含多部件要素。 这是默认设置。
    # SINGLE_PART—输出中不包含多部件要素。 系统将为各部件创建单独的要素。
    arcpy.analysis.PairwiseDissolve(
        in_features=shp_temp_polygon,
        out_feature_class=shp_dissolved,
        multi_part="SINGLE_PART")
    print(f"[INFO] Polygon Fixed: {shp_dissolved}")

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


if __name__ == '__main__':
    list_year = ['2010', '2015', '2020']
    list_sids = read_txt_to_list(file_path=fr"SIDS_37.txt")

    for year in ['2010', '2015']:
        # for year in list_year:
        for sids in ['ATG']:
            folder = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\g_shp_polygon\{sids}\{year}"
            extra = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\g_shp_polygon\{sids}\{sids}_add.shp"
            output = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\_draft\{sids}_{year}.shp"

            merge_shapefiles_gpd(folder, extra, output)

            shp_input = output
            shp_fixed = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\h_shp_merge\{sids}\{sids}_{year}.shp"

            os.makedirs(os.path.dirname(shp_fixed), exist_ok=True)
            fix_shapefiles(shp_input, shp_fixed)

