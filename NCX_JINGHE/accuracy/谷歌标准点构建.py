import geopandas as gpd
import warnings
import os

def convert_kml_to_shp(kml_file, shp_file):
    """
    将KML文件转换为SHP文件，处理列名和警告。

    参数:
    kml_file (str): 输入的KML文件路径。
    shp_file (str): 输出的SHP文件路径。
    """
    # 关闭警告
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)

    try:
        # 读取KML文件
        gdf = gpd.read_file(kml_file, driver='KML')

        # 可选：修改列名，确保不超过10个字符
        gdf.columns = [col[:10] for col in gdf.columns]

        # 将读取的数据保存为SHP文件
        gdf.to_file(shp_file, driver='ESRI Shapefile')

        print(f"Shapefile saved to {shp_file}")

    except Exception as e:
        print(f"An error occurred: {e}")


def find_kml_files(root_folder):
    """
    在指定文件夹及其子文件夹中查找所有KML文件。

    参数:
    root_folder (str): 根文件夹路径。

    返回:
    list: 找到的KML文件路径列表。
    """
    kml_files = []
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file.endswith('.kml'):
                kml_files.append(os.path.join(root, file))
    return kml_files


def merge_shp_files(year_folder, output_shp_file):
    """
    合并指定文件夹中的所有SHP文件，并添加一个字段 kml_name 来标记原始KML文件名。

    参数:
    year_folder (str): 包含SHP文件的文件夹路径。
    output_shp_file (str): 输出的合并SHP文件路径。
    """
    try:
        # 获取文件夹中的所有SHP文件
        shp_files = [os.path.join(year_folder, f) for f in os.listdir(year_folder) if f.endswith('.shp')]

        if not shp_files:
            print(f"No SHP files found in {year_folder}")
            return

        # 读取所有SHP文件并添加 kml_name 字段
        gdfs = []
        for shp_file in shp_files:
            temp_gdf = gpd.read_file(shp_file)
            # 提取国家代码和年份
            kml_name = os.path.basename(shp_file).replace('.shp', '').split('_')[0] + '_' + os.path.basename(shp_file).replace('.shp', '').split('_')[-1]
            temp_gdf['kml_name'] = kml_name
            gdfs.append(temp_gdf)

        # 合并所有GeoDataFrame
        merged_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=gdfs[0].crs)

        # 保存合并后的SHP文件
        merged_gdf.to_file(output_shp_file, driver='ESRI Shapefile')
        print(f"Merged Shapefile saved to {output_shp_file}")

    except Exception as e:
        print(f"An error occurred while merging SHP files: {e}")


if __name__ == '__main__':
    import pandas as pd  # 导入 pandas 模块

    kml_root_folder = fr"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\_AccuracyEvaluation\_kml"
    kml_files = find_kml_files(kml_root_folder)

    for kml_file in kml_files:
        # 获取KML文件名（不含路径和扩展名）
        kml_file_name = os.path.basename(kml_file)
        kml_file_name_without_ext = os.path.splitext(kml_file_name)[0]

        # 提取年份
        year = kml_file_name.split('_')[-1].split('.')[0]

        # 输出文件夹路径
        folder_output_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\_AccuracyEvaluation\_kml_to_std\{year}"

        # 输出SHP文件路径
        shp_file = os.path.join(folder_output_path, f"{kml_file_name_without_ext}.shp")

        # 确保输出文件夹存在
        os.makedirs(folder_output_path, exist_ok=True)

        # 转换KML到SHP
        convert_kml_to_shp(kml_file, shp_file)

    # 合并每个年份文件夹中的SHP文件
    for year in [2010, 2015, 2020]:
        year_folder = fr"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\_AccuracyEvaluation\_kml_to_std\{year}"
        output_shp_file = fr"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\_AccuracyEvaluation\_kml_to_std\all\Std_{year}.shp"
        os.makedirs(os.path.dirname(output_shp_file), exist_ok=True)
        merge_shp_files(year_folder, output_shp_file)