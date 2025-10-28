# -*- coding: utf-8 -*-
"""
作者：23242
更新日期：2025年06月21日

功能：
- 从 GeoTIFF 栅格图像中提取子像素轮廓线
- 封闭并偏移 MultiLineString 几何
- 自动构面并输出面 Shapefile
"""

import os
import tempfile
import numpy as np
import rasterio
from affine import Affine
import xarray as xr
import rioxarray
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from shapely.ops import polygonize
from dea_tools.spatial import subpixel_contours


def add_zero_buffer_array(data, buffer_size=1):
    """
    为栅格数组四周添加一圈 0 值缓冲区。

    :param data: 原始二维数组
    :param buffer_size: 缓冲宽度（单位：像元）
    :return: 扩展后的二维数组
    """
    return np.pad(data, pad_width=buffer_size, mode='constant', constant_values=0)


def extract_subpixel_geometry(input_tif, z_values):
    """
    提取子像素轮廓线，闭合 MultiLineString，返回 GeoDataFrame。

    :param input_tif: 输入的 .tif 路径
    :param z_values: 等值线提取值（如 0）
    :return: GeoDataFrame，包含封闭处理后的 MultiLineString
    """
    with rasterio.open(input_tif) as src:
        data = src.read(1)
        transform = src.transform
        crs = src.crs

        # 添加一圈缓冲像元
        data = add_zero_buffer_array(data, buffer_size=1)
        transform = transform * Affine.translation(-1, -1)

        # 计算偏移量（用于封闭线恢复坐标）
        x_offset = transform[0] / 2
        y_offset = transform[4] / 2

        # 构建 xarray DataArray
        height, width = data.shape
        x_coords = [transform * (col, 0) for col in range(width)]
        y_coords = [transform * (0, row) for row in range(height)]
        x_coords = [x[0] for x in x_coords]
        y_coords = [y[1] for y in y_coords]

        da = xr.DataArray(
            data,
            coords=[y_coords, x_coords],
            dims=["y", "x"],
            attrs={'transform': transform, 'crs': str(crs)}
        ).rio.write_crs(crs)

    # 创建临时 geojson 路径，避免文件锁
    fd, geojson_path = tempfile.mkstemp(suffix=".geojson")
    os.close(fd)

    # 提取子像素轮廓线并写入
    subpixel_contours(da=da, z_values=z_values, attribute_df=None, output_path=geojson_path)

    # 读取轮廓线结果
    gdf = gpd.read_file(geojson_path)
    os.remove(geojson_path)

    # 封闭每个 MultiLineString 并应用坐标偏移
    for idx, row in gdf.iterrows():
        geometry = row.geometry
        if isinstance(geometry, MultiLineString):
            closed_lines = []
            for line in geometry.geoms:
                coords = [(x + x_offset, y + y_offset) for x, y in line.coords]
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                closed_lines.append(LineString(coords))
            gdf.at[idx, 'geometry'] = MultiLineString(closed_lines)
    return gdf


def polygonize_lines(gdf_line):
    """
    将封闭的线要素构面。

    :param gdf_line: GeoDataFrame（LineString 或 MultiLineString）
    :return: Polygon GeoDataFrame
    """
    lines = []
    for geom in gdf_line.geometry:
        if isinstance(geom, LineString):
            lines.append(geom)
        elif isinstance(geom, MultiLineString):
            lines.extend(geom.geoms)

    polygons = list(polygonize(lines))
    if not polygons:
        raise ValueError("未能构建任何闭合面。")

    return gpd.GeoDataFrame(geometry=polygons, crs=gdf_line.crs)


def main():
    tif_file = r'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\d_tif_fixed\ATG\2010\ATG_62W17Nlb.tif'
    polygon_shp_output = r'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\e_shp_subpixel\ATG\2010\ATG_62W17Nlb.shp'

    # Step 1: 提取封闭的子像素轮廓线
    gdf_lines = extract_subpixel_geometry(input_tif=tif_file, z_values=0)

    # Step 2: 构面
    gdf_polygons = polygonize_lines(gdf_lines)

    # Step 3: 保存面要素
    gdf_polygons.to_file(polygon_shp_output)
    print(f"✅ 面要素保存成功：{polygon_shp_output}")


if __name__ == '__main__':
    main()
