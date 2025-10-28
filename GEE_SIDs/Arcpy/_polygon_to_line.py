import geopandas as gpd
import os


def polygon_to_line(input_shapefile: str, output_shapefile: str) -> None:
    """
    将面要素 Shapefile 转换为线要素，并保存为新的 Shapefile 文件。

    :param input_shapefile: 输入面要素文件路径（Shapefile 格式）
    :param output_shapefile: 输出线要素的 Shapefile 文件路径
    """
    # 读取输入 Shapefile 文件
    gdf = gpd.read_file(input_shapefile)

    # 提取每个面的边界，转换为线要素
    gdf['geometry'] = gdf['geometry'].boundary

    # 保存为新的 Shapefile 文件
    gdf.to_file(output_shapefile, driver='ESRI Shapefile')

    print(f"转换完成，线要素已保存到 {output_shapefile}")


# 示例调用
if __name__ == "__main__":
    year_list = [2000, 2010, 2020]
    sids_cou_list = ['DMA',
                     'GUM',
                     'NIU',
                     'SGP',
                     'VCT',
                     ]
    # year_list = [2020]
    # sids_cou_list = ['BRB']

    for sid in sids_cou_list:
        for year in year_list:
            # 输入面要素文件路径
            input_file = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\k_SIDS_Smooth\{sid}\{sid}_{str(year)[-2:]}.shp"
            # 输出线要素文件路径
            folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\{sid}\{year}"
            if os.path.exists(folder_path):
                pass
            else:
                os.makedirs(folder_path)
            output_file = os.path.join(folder_path, fr"SL_{sid}_{str(year)[-2:]}.shp")

            # 调用函数将面要素转换为线要素
            polygon_to_line(input_file, output_file)
