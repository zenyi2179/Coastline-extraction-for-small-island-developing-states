import os

import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon


def fix_holes_in_shp(input_shp: str, output_shp: str, min_area: float = 0.0) -> None:
    """
    修复Shapefile面要素中的空洞。

    参数:
        input_shp (str): 输入Shapefile路径
        output_shp (str): 输出Shapefile路径
        min_area (float): 保留的最小空洞面积，小于此面积的空洞将被填充
    """
    # 读取Shapefile
    gdf = gpd.read_file(input_shp)

    # 处理每个几何对象
    fixed_geometries = []
    for geom in gdf.geometry:
        if geom.geom_type == 'Polygon':
            # 处理单个多边形
            exterior = geom.exterior
            interiors = [interior for interior in geom.interiors if interior.area > min_area]
            fixed_geom = Polygon(exterior, interiors)
            fixed_geometries.append(fixed_geom)
        elif geom.geom_type == 'MultiPolygon':
            # 处理多个多边形
            fixed_polygons = []
            for poly in geom.geoms:
                exterior = poly.exterior
                interiors = [interior for interior in poly.interiors if interior.area > min_area]
                fixed_poly = Polygon(exterior, interiors)
                fixed_polygons.append(fixed_poly)
            fixed_geom = MultiPolygon(fixed_polygons)
            fixed_geometries.append(fixed_geom)
        else:
            # 非面要素直接添加
            fixed_geometries.append(geom)

    # 更新几何列
    gdf.geometry = fixed_geometries

    # 保存结果
    gdf.to_file(output_shp)
    print(f"已修复空洞并保存至: {output_shp}")

input_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\b_shp_GeeData\ATG\2010\ATG_62W17Nlb.shp"
output_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\c_shp_fixed\ATG\2010\ATG_62W17Nlb.shp"
os.makedirs(os.path.dirname(output_shp), exist_ok=True)
fix_holes_in_shp(input_shp, output_shp)