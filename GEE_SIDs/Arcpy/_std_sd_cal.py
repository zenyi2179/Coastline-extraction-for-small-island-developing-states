import arcpy
import numpy as np
from dbfread import DBF
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


def create_sample_points(StP_GID, S_CL, SP_GID):
    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    # Process: 复制要素 (复制要素) (management)
    StP_Copy_shp = fr"in_memory\StP_Copy"
    arcpy.management.CopyFeatures(in_features=StP_GID, out_feature_class=StP_Copy_shp)

    # Process: 邻近分析 (邻近分析) (analysis)
    Stp_Near = arcpy.analysis.Near(in_features=StP_Copy_shp, near_features=[S_CL], search_radius="90 Meters",
                                   location="LOCATION", method="GEODESIC",
                                   field_names=[["NEAR_FID", "NEAR_FID"], ["NEAR_DIST", "NEAR_DIST"],
                                                ["NEAR_X", "NEAR_X"], ["NEAR_Y", "NEAR_Y"]])[0]

    # Process: XY 表转点 (XY 表转点) (management)
    arcpy.management.XYTableToPoint(in_table=Stp_Near, out_feature_class=SP_GID,
                                    x_field="NEAR_X", y_field="NEAR_Y")
    print(SP_GID, 'finish')


def calculate_statistics(dbf_file_path):
    """
    计算DBF文件中 'NEAR_DIST' 列的统计数据：
    - 平均值
    - 值小于30的个数百分比
    - 值小于60的个数百分比
    - 标准差
    - 均方根误差 (RMSE)

    参数:
    dbf_file_path (str): DBF文件路径

    返回:
    dict: 包含上述统计数据的字典
    """

    # 读取DBF文件
    dbf = DBF(dbf_file_path, encoding='utf-8')

    # 提取'NEAR_DIST'列的数据
    # near_dist_values = [record['NEAR_DIST'] for record in dbf if 'NEAR_DIST' in record]
    near_dist_values = []
    for record in dbf:
        if 'NEAR_DIST' in record:
            value = record['NEAR_DIST']
            if value >= 0:
                near_dist_values.append(value)

    # 如果没有数据，返回None
    if not near_dist_values:
        return None

    # 将数据转化为numpy数组
    near_dist_values = np.array(near_dist_values)

    # 计算统计值

    count_30 = np.sum(near_dist_values < 30)
    count_60 = np.sum(near_dist_values < 60)
    count_all = len(near_dist_values)
    percent_30 = count_30 / count_all * 100
    percent_60 = count_60 / count_all * 100
    mean_value = np.mean(near_dist_values)
    std_dev = np.std(near_dist_values)
    rmse = np.sqrt(np.mean(near_dist_values ** 2))

    # 返回结果
    return {
        'count_30': count_30,
        'count_60': count_60,
        'count_all': count_all,
        'percent_30': percent_30,
        'percent_60': percent_60,
        'mean_value': mean_value,
        'std_dev': std_dev,
        'rmse': rmse
    }


if __name__ == '__main__':
    # year_list = [2010, 2020]
    # sids_cou_list = ["ATG",
    # "BHS",
    # "BLZ",
    # "BRB",
    # "COM",
    # "CPV",
    # "CUB",
    # "DMA",
    # "DOM",
    # "FJI",
    # "FSM",
    # "GNB",
    # "GRD",
    # "GUY",
    # "HTI",
    # "JAM",
    # "KIR",
    # "KNA",
    # "LCA",
    # "MDV",
    # "MHL",
    # "MUS",
    # "NRU",
    # "PLW",
    # "PNG",
    # "SGP",
    # "SLB",
    # "STP",
    # "SUR",
    # "SYC",
    # "TLS",
    # "TON",
    # "TTO",
    # "TUV",
    # "VCT",
    # "VUT",
    # "WSM",
    # ]

    year_list = [2010, 2020]
    sids_cou_list = ['BHS']
    for sid in sids_cou_list:
        for year in year_list:
            # 由 kml 创建 std.shp
            folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\{sid}"
            kml_file = os.path.join(folder_path, fr"{sid}_{str(year % 100).zfill(2)}.kml")
            os.makedirs(os.path.join(folder_path, str(year)), exist_ok=True)  # 确定是否存在文件夹
            shp_file = os.path.join(folder_path, fr"{year}\StP_{sid}_{str(year % 100).zfill(2)}.shp")
            convert_kml_to_shp(kml_file, shp_file)
            # print(fr'output std: {year} {sid}')

            # 创建样本点 sd.shp
            work_folder = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\{sid}\{year}"
            standard_points = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\\" \
                              fr"{sid}\{year}\StP_{sid}_{str(year)[-2:]}.shp"
            third_path_output = os.path.join(work_folder, fr"ThirdPartyDataSource")  # 初始化第三方文件夹
            os.makedirs(third_path_output, exist_ok=True)  # 确定是否存在文件夹
            sample_lines = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\\" \
                           fr"SIDS_CL_{str(year)[-2:]}\{sid}\{sid}_CL_{str(year)[-2:]}.shp"
            sample_points = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\\" \
                            fr"{sid}\{year}\SP_{sid}_{str(year)[-2:]}.shp"
            create_sample_points(standard_points, sample_lines, sample_points)
            # print(fr'output sd: {year} {sid}')

            # 精度评估
            folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\{sid}\{year}"
            near_table = os.path.join(folder_path, fr'SP_{sid}_{str(year)[-2:]}.dbf')
            # 计算DBF文件中 'NEAR_DIST' 列的统计数据
            statistics = calculate_statistics(near_table)
            if statistics:
                # print("统计结果:", statistics)
                print(
                    year, sid,
                    statistics['percent_30'], statistics['percent_60'],
                    statistics['mean_value'], statistics['std_dev'], statistics['rmse'],
                    statistics['count_30'], statistics['count_60'], statistics['count_all'],
                )
            else:
                print(year, sid, )
