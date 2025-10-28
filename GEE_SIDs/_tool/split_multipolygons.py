import geopandas as gpd
from shapely.geometry import MultiPolygon
import pandas as pd


def split_multipolygons(input_shp, output_shp):
    """
    读取Shapefile文件，将其中的MultiPolygon对象拆分为单独的Polygon，并保存为新的Shapefile文件。

    :param input_shp: 输入的Shapefile文件路径
    :param output_shp: 输出的Shapefile文件路径
    """
    # 读取输入Shapefile文件
    gdf = gpd.read_file(input_shp)

    # 创建一个空的列表，用于保存拆分后的数据行
    rows_list = []

    # 遍历每个几何对象，检查是否为MultiPolygon类型
    for idx, row in gdf.iterrows():
        geometry = row['geometry']
        if isinstance(geometry, MultiPolygon):
            # 将MultiPolygon拆分为单独的Polygon
            for poly in geometry.geoms:
                new_row = row.copy()
                new_row['geometry'] = poly
                rows_list.append(new_row)
        else:
            rows_list.append(row)

    # 将结果存储到新的GeoDataFrame中
    new_gdf = pd.concat([pd.DataFrame([row]) for row in rows_list], ignore_index=True)
    new_gdf = gpd.GeoDataFrame(new_gdf, geometry='geometry', crs=gdf.crs)

    # 保存为新的Shapefile文件
    new_gdf.to_file(output_shp)

    print(fr"Split multipolygons saved at {output_shp}")


def main():
    pass


if __name__ == '__main__':
    main()
