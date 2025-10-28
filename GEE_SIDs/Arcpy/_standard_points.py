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


if __name__ == '__main__':
    year_list = [2010, 2020]
    sids_cou_list = ["ATG",
"BHS",
"BLZ",
"BRB",
"COM",
"CPV",
"CUB",
"DMA",
"DOM",
"FJI",
"FSM",
"GNB",
"GRD",
"GUY",
"HTI",
"JAM",
"KIR",
"KNA",
"LCA",
"MDV",
"MHL",
"MUS",
"NRU",
"PLW",
"PNG",
"SGP",
"SLB",
"STP",
"SUR",
"SYC",
"TLS",
"TON",
"TTO",
"TUV",
"VCT",
"VUT",
"WSM",
]
    year_list = [2015]
    sids_cou_list = ["ATG",
"BHS",
"BLZ",
"BRB",
"COM",
"CPV",
"CUB",
"DMA",
"DOM",
"FJI",
"FSM",
"GNB",
"GRD",
"GUY",
"HTI",
"JAM",
"KIR",
"LCA",
"MDV",
"MHL",
                     "MUS",
                     ]
    for sid in sids_cou_list:
        for year in year_list:

            # 示例使用
            folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\{sid}"
            kml_file = os.path.join(folder_path, fr"{sid}_{str(year % 100).zfill(2)}.kml")
            # if os.path.exists(os.path.join(folder_path, str(year))):
            #     pass
            # else:
            #     os.makedirs(os.path.join(folder_path, str(year)))
            # 确定是否存在文件夹
            os.makedirs(os.path.join(folder_path, str(year)), exist_ok=True)
            shp_file = os.path.join(folder_path, fr"{year}\StP_{sid}_{str(year % 100).zfill(2)}.shp")

            convert_kml_to_shp(kml_file, shp_file)
