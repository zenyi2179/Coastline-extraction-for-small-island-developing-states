# -*- coding: utf-8 -*-
"""
作者：23242
日期：2024年09月18日

功能描述：
- 从栅格图像中提取子像素轮廓线（Subpixel Contours）
- 自动闭合线段（MultiLineString → 封闭 LineString）
- 自动构面（polygonize）
- 全流程仅输出最终结果（面状 Shapefile），不保存中间文件
"""

import os
import rasterio
import rioxarray
import xarray as xr
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString
from shapely.ops import polygonize
from dea_tools.spatial import subpixel_contours
from tempfile import NamedTemporaryFile


def process_multilinestring(geometry):
    """
    封闭 MultiLineString 中的所有 LineString 线段（若未闭合，则闭合）。

    参数:
        geometry (MultiLineString): 输入几何对象

    返回:
        生成器: 闭合后的 LineString 对象
    """
    if isinstance(geometry, MultiLineString):
        for component in geometry.geoms:
            coords = list(component.coords)
            if coords[0] != coords[-1]:  # 若未闭合，则闭合
                coords.append(coords[0])
            yield LineString(coords)
    else:
        return []


def extract_and_close_subpixel_contours(input_tif, z_values):
    """
    从栅格图像中提取子像素轮廓，并闭合线段，返回 GeoDataFrame。

    参数:
        input_tif (str): 输入 GeoTIFF 文件路径
        z_values (float or int): 提取轮廓的等值线值

    返回:
        gpd.GeoDataFrame: 封闭后的线状要素集
    """
    # 打开栅格并构建 DataArray（含空间信息）
    with rasterio.open(input_tif) as src:
        raster_data = src.read(1)
        transform = src.transform
        crs = src.crs
        height, width = raster_data.shape

        x_coords = [transform * (col, 0) for col in range(width)]
        y_coords = [transform * (0, row) for row in range(height)]
        x_coords = [x[0] for x in x_coords]
        y_coords = [y[1] for y in y_coords]

        data_array = xr.DataArray(
            raster_data,
            coords=[y_coords, x_coords],
            dims=["y", "x"],
            attrs={'crs': str(crs), 'transform': transform}
        )

    data_array.rio.write_crs("EPSG:4326", inplace=True)

    # 使用 NamedTemporaryFile 创建临时输出路径，不保存文件
    with NamedTemporaryFile(suffix='.geojson', delete=True) as tmpfile:
        # 提取子像素轮廓并输出为 GeoJSON（临时文件）
        subpixel_contours(da=data_array, z_values=z_values, attribute_df=None, output_path=tmpfile.name)

        # 读取并处理 MultiLineString（闭合线段）
        gdf = gpd.read_file(tmpfile.name)
        for idx, row in gdf.iterrows():
            geometry = row.geometry
            if isinstance(geometry, MultiLineString):
                closed_lines = list(process_multilinestring(geometry))
                gdf.at[idx, 'geometry'] = MultiLineString(closed_lines)

    return gdf


def polygonize_from_lines(gdf_line: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    从 GeoDataFrame 中的 LineString/MultiLineString 自动构面。

    参数:
        gdf_line (GeoDataFrame): 包含线要素的 GDF

    返回:
        GeoDataFrame: 构面后的 Polygon GDF
    """
    # 收集所有线段用于 polygonize
    all_lines = []
    for geom in gdf_line.geometry:
        if isinstance(geom, LineString):
            all_lines.append(geom)
        elif isinstance(geom, MultiLineString):
            all_lines.extend(geom.geoms)

    # 自动闭合并构建多边形
    polygons = list(polygonize(all_lines))
    if not polygons:
        raise ValueError("❌ 无法从线要素构建闭合面，请检查轮廓提取结果。")

    return gpd.GeoDataFrame(geometry=polygons, crs=gdf_line.crs)


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

def shp_subpixel_contours(input_tif, output_shp, z_value):
    # 1️⃣ 提取子像素轮廓，并自动闭合线段
    print("⏳ 提取并闭合子像素轮廓线 ...")
    line_gdf = extract_and_close_subpixel_contours(input_tif=input_tif, z_values=z_value)

    # 2️⃣ 从闭合线段自动构面
    # print("⏳ 构建闭合多边形 ...")
    polygon_gdf = polygonize_from_lines(line_gdf)

    # 3️⃣ 输出为最终面状 Shapefile
    polygon_gdf.to_file(output_shp)
    print(f"✅ 面要素提取完成：{output_shp}")

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
                fr"\d_tif_fixed\{sids}\{year}")
            list_map_files = get_files_absolute_paths(path_folder, suffix=fr'.tif')
            for tif_file in list_map_files:

                # 输入与输出路径
                polygon_output = (
                    fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp"
                    fr"\e_shp_subpixel\{sids}\{year}\{os.path.splitext(os.path.basename(tif_file))[0]}.shp")
                # 创建路径
                path_folder = os.path.dirname(polygon_output)
                os.makedirs(path_folder, exist_ok=True)
                print(polygon_output)

                contour_z_value = 0  # 提取子像素轮廓的值
                # 转shp
                try:
                    shp_subpixel_contours(input_tif=tif_file, output_shp=polygon_output, z_value=contour_z_value)
                except Exception as e:
                    pass


if __name__ == '__main__':
    main()
