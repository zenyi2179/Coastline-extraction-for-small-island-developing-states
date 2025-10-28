import os
import arcpy
import rasterio
import numpy as np
import geopandas as gpd
from shapely.geometry import shape
from rasterio.features import shapes
from scipy.ndimage import label

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


def tif_to_merged_regions_shp(input_tif: str, output_shp: str, threshold: float = 0.0):
    """
    将.tif中值大于指定阈值的连通区域合并为一个或多个面，并保存为shapefile。

    参数:
        input_tif (str): 输入的.tif文件路径。
        output_shp (str): 输出的.shp文件路径。
        threshold (float): 像元阈值，大于此值的区域将被合并为矢量面。
    """
    with rasterio.open(input_tif) as src:
        data = src.read(1)
        transform = src.transform
        crs = src.crs

        # 生成二值掩码（1 表示值 > 阈值）
        binary_mask = (data > threshold).astype(np.uint8)

        # 连通区域标记
        labeled_array, num_features = label(binary_mask)

        print(f"检测到 {num_features} 个连通区域")

        # 转换为矢量面
        shapes_gen = shapes(labeled_array, mask=binary_mask, transform=transform)
        geometries = [
            {"geometry": shape(geom), "properties": {"id": int(value)}}
            for geom, value in shapes_gen
            if value != 0
        ]

        # 构建 GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(geometries)
        gdf.crs = crs

        # 保存为 Shapefile
        gdf.to_file(output_shp, driver='ESRI Shapefile')

        print(f"成功输出为 shapefile：{output_shp}")

def read_txt_to_list(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    # 去除每行末尾的换行符
    lines = [line.strip() for line in lines]
    return lines

def get_files_absolute_paths(folder_path, suffix=None):
    """
    获取指定文件夹下所有指定后缀的文件的绝对路径名称

    :param folder_path: 指定文件夹的路径
    :param suffix: 文件后缀（可选），如 '.shp'。如果不指定，则获取所有文件的路径
    :return: 指定后缀的文件的绝对路径名称列表
    """
    files_paths = []
    # 遍历指定文件夹
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 如果指定了后缀，则判断文件后缀是否匹配
            if suffix is None or file.endswith(suffix):
                # 获取文件的绝对路径并添加到列表中
                files_paths.append(os.path.abspath(os.path.join(root, file)))
    return files_paths

def main():
    # 初始化处理的国家和年份
    list_year = ['2010', '2015', '2020']
    list_sids = read_txt_to_list(file_path=fr"SIDS_37.txt")

    for year in ['2010']:
    # for year in list_year:
        for sids in ['ATG']:
        # for sids in list_sids:
            # 示例使用
            path_folder = (
                fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp"
                fr"\a_tif_GeeData\{sids}\{year}")
            list_map_files = get_files_absolute_paths(path_folder, suffix=fr'.tif')
            for tif_file in list_map_files:
                temp1 = fr"E:\_OrderingProject\draft0621\temp9.shp"
                tif_to_merged_regions_shp(
                    input_tif=tif_file,
                    output_shp=temp1,
                )

                country_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\d_SIDS_Boundary\SIDS\AdminDivision\{sids}.shp"
                out_fea = r"E:\_OrderingProject\draft0621\temp10.shp"
                select_valid_polygons(valid_pixel_shp=temp1, country_shp=country_shp, output_shp=out_fea)


if __name__ == "__main__":
    main()
