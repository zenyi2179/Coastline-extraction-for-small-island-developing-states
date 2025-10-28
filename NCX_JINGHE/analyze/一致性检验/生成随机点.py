#!/usr/bin/env python3
import arcpy
import geopandas as gpd
from shapely.geometry import Point
import random
import time
import os
from concurrent.futures import ProcessPoolExecutor

arcpy.env.overwriteOutput = True


# 定义函数：在一条线段上随机生成点
def random_points_on_line(line: gpd.GeoSeries, num_points: int) -> list[Point]:
    """
    在一条线段上随机生成指定数量的点。

    Args:
        line: 输入的线段
        num_points: 需要生成的点的数量

    Returns:
        生成的点的列表
    """
    points = []
    for _ in range(num_points):
        length = line.length
        random_length = random.uniform(0, length)
        point = line.interpolate(random_length)
        points.append(point)
    return points


# 定义函数：并行生成点
def generate_points_for_line(line: gpd.GeoSeries, total_length: float, total_points: int) -> list[Point]:
    """
    并行生成点的函数。

    Args:
        line: 输入的线段
        total_length: 所有线段的总长度
        total_points: 需要生成的点的总数

    Returns:
        生成的点的列表
    """
    line_length = line.length
    num_points_on_line = int(total_points * (line_length / total_length))
    return random_points_on_line(line, num_points_on_line)


def generate_random_points_on_lines(
        input_layer: str, output_layer: str, total_points: int
) -> str:
    """
    在线shp文件的线段上随机生成点，并将结果保存为新的shp文件。

    Args:
        input_layer: 输入的线shp文件路径
        output_layer: 输出的点shp文件路径
        total_points: 需要生成的点的总数

    Returns:
        输出的点shp文件路径

    Raises:
        FileNotFoundError: 输入的线shp文件路径不存在
    """
    # 检查输入文件是否存在
    if not os.path.exists(input_layer):
        raise FileNotFoundError(f"[ERROR] | 输入的线shp文件路径不存在：{input_layer}")

    # 读取线shp文件
    start_time = time.time()
    print(f"[INFO]  | 开始读取线shp文件：{input_layer}")
    line_gdf = gpd.read_file(input_layer)
    elapsed = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - start_time))
    print(f"[INFO]  | 读取线shp文件完成，耗时：{elapsed}")

    # 计算所有线段的总长度
    total_length = line_gdf.geometry.length.sum()

    # 使用多进程并行生成点
    start_time = time.time()
    print(f"[INFO]  | 开始在所有线段上随机生成点，总数：{total_points}")
    with ProcessPoolExecutor() as executor:
        points_lists = list(
            executor.map(generate_points_for_line, line_gdf.geometry, [total_length] * len(line_gdf.geometry),
                         [total_points] * len(line_gdf.geometry)))
    points = [point for sublist in points_lists for point in sublist]
    elapsed = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - start_time))
    print(f"[INFO]  | 随机生成点完成，耗时：{elapsed}")

    # 将生成的点转换为GeoDataFrame
    start_time = time.time()
    print(f"[INFO]  | 开始将生成的点转换为GeoDataFrame")
    point_gdf = gpd.GeoDataFrame(geometry=points, crs=line_gdf.crs)
    elapsed = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - start_time))
    print(f"[INFO]  | 转换为GeoDataFrame完成，耗时：{elapsed}")

    # 保存点为shp文件
    start_time = time.time()
    print(f"[INFO]  | 开始保存点为shp文件：{output_layer}")
    point_gdf.to_file(output_layer)
    elapsed = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - start_time))
    print(f"[INFO]  | 保存点为shp文件完成，耗时：{elapsed}")

    return output_layer


def add_lon_lat_fields_to_shp(input_shp: str) -> None:
    """
    使用arcpy为shp文件添加lon和lat字段，并计算几何。

    Args:
        input_shp: 输入的shp文件路径
    """
    # 检查输入文件是否存在
    if not os.path.exists(input_shp):
        raise FileNotFoundError(f"[ERROR] | 输入的shp文件路径不存在：{input_shp}")

    # 重新投影到GCS_WGS_1984
    wgs84_shp = input_shp.replace(".shp", "_WGS84.shp")
    arcpy.Project_management(input_shp, wgs84_shp, arcpy.SpatialReference(4326))

    # 添加字段
    arcpy.AddField_management(wgs84_shp, "lon", "DOUBLE")
    arcpy.AddField_management(wgs84_shp, "lat", "DOUBLE")

    # 计算几何
    arcpy.CalculateGeometryAttributes_management(
        wgs84_shp,
        [["lon", "POINT_X"], ["lat", "POINT_Y"]],
        coordinate_system="GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]"
    )

    # 删除原始文件，重命名投影后的文件
    arcpy.Delete_management(input_shp)
    arcpy.Rename_management(wgs84_shp, input_shp)


def main():
    path_datasets = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\_third_party_dataset'
    path_poi = fr'E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\Analyze\consistency_check\third_dataset_poi'
    list_datasets = [
        'GCL_FCS30_2010', 'GCL_FCS30_2015', 'GCL_FCS30_2020',
        'GMSSD_2015', 'GSV_2015', 'OSM_2020'
    ]
    dict_datasets = {
        "GCL_FCS30_2010": 1500,
        "GSV_2015": 5000,
        "GMSSD_2015": 5000,
        "GCL_FCS30_2015": 1500,
        "OSM_2020": 3000,
        "GCL_FCS30_2020": 1500,
    }
    for dataset in list_datasets:
        input_layer = os.path.join(path_datasets, fr'{dataset}.shp')
        output_layer = os.path.join(path_poi, fr'{dataset}.shp')
        total_points = dict_datasets.get(dataset, 0)

        print(f"[INFO]  | 任务启动，PID={os.getpid()}")
        try:
            # 生成随机点并保存为shp文件
            result = generate_random_points_on_lines(input_layer, output_layer, total_points)
            print(f"[INFO]  | 随机生成的点已保存到：{result}")

            # 使用arcpy添加lon和lat字段并计算几何
            add_lon_lat_fields_to_shp(output_layer)
            print(f"[INFO]  | 已为shp文件添加lon和lat字段并计算几何：{output_layer}")
        except Exception as err:
            print(f"[ERROR] | 发生错误：{err}")


if __name__ == "__main__":
    main()
    #
    # # -----------------------------
    # input_layer = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\temp\_analyze\GSV_37.shp"
    # output_layer = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\temp\_analyze\output_points.shp"
    # total_points = 3700
    #
    # print(f"[INFO]  | 任务启动，PID={os.getpid()}")
    # try:
    #     # 生成随机点并保存为shp文件
    #     result = generate_random_points_on_lines(input_layer, output_layer, total_points)
    #     print(f"[INFO]  | 随机生成的点已保存到：{result}")
    #
    #     # 使用arcpy添加lon和lat字段并计算几何
    #     add_lon_lat_fields_to_shp(output_layer)
    #     print(f"[INFO]  | 已为shp文件添加lon和lat字段并计算几何：{output_layer}")
    # except Exception as err:
    #     print(f"[ERROR] | 发生错误：{err}")
