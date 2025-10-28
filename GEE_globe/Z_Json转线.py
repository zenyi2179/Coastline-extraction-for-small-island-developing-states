import geopandas as gpd
import os


def geojson_to_shp(input_geojson, output_shp):
    """
    将 GeoJSON 文件转换为 Shapefile 文件。

    :param input_geojson: 输入的 GeoJSON 文件路径
    :param output_shp: 输出的 Shapefile 文件路径
    """
    # 读取 GeoJSON 文件
    gdf = gpd.read_file(input_geojson)

    # 保存为 Shapefile 文件
    gdf.to_file(output_shp, driver='ESRI Shapefile')
    print(f"GeoJSON to Shapefile, saved as: {output_shp}")

def main():
    # 初始 57 国家
    sids_cou_list = ["BHS","GUY",
                     ]
    for sids_cou in sids_cou_list:
        for year in [2000, 2010, 2020]:
            # 示例用法
            input_geojson = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Geojson\{sids_cou}\{sids_cou}_{str(year)[-2:]}.geojson"  # 替换为你的 GeoJSON 文件路径
            output_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\i_SIDS_Line\{sids_cou}\{sids_cou}_{str(year)[-2:]}.shp"  # 替换为你希望保存的 Shapefile 文件路径
            # 新建文件夹
            os.makedirs(name=fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\i_SIDS_Line\{sids_cou}",
                        exist_ok=True)
            geojson_to_shp(input_geojson, output_shp)


if __name__ == '__main__':
    main()
