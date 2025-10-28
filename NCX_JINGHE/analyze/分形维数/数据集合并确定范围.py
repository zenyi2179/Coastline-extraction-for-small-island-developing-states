#!/usr/bin/env python3

import os
import time
import geopandas as gpd
import pandas as pd
from pyproj import CRS
from typing import List

# 常量定义
INPUT_FOLDER: str = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\_third_party_dataset"
OUTPUT_FOLDER: str = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\Analyze\fractal_dimension\polyline_merge"
OUTPUT_FILE: str = os.path.join(OUTPUT_FOLDER, "polyline_merge.shp")


def merge_shapefiles(input_folder: str, output_folder: str, output_file: str) -> str:
    """
    合并指定文件夹中的所有 .shp 文件，并将其保存为一个新的 Shapefile。

    Args:
        input_folder: 包含 .shp 文件的输入文件夹路径
        output_folder: 输出文件夹路径
        output_file: 合并后的 Shapefile 输出路径

    Returns:
        合并后的 Shapefile 路径

    Raises:
        FileNotFoundError: 输入文件夹不存在
        ValueError: 输入文件夹中没有找到任何 .shp 文件
    """
    start_time = time.time()
    print(f"[INFO]  | 任务启动，PID={os.getpid()}")

    # 检查输入文件夹是否存在
    if not os.path.exists(input_folder):
        raise FileNotFoundError(f"[ERROR] | 输入文件夹不存在：{input_folder}")

    # 获取文件夹中所有的 .shp 文件
    shp_files: List[str] = [os.path.join(input_folder, f) for f in os.listdir(input_folder) if f.endswith(".shp")]

    if not shp_files:
        raise ValueError(f"[ERROR] | 输入文件夹中没有找到任何 .shp 文件：{input_folder}")

    # 读取所有 .shp 文件并转换为 WGS84 投影
    gdfs = [gpd.read_file(shp_file).to_crs(CRS.from_epsg(4326)) for shp_file in shp_files]

    # 合并所有 GeoDataFrame
    merged_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))

    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)

    # 保存合并后的文件
    merged_gdf.to_file(output_file, driver="ESRI Shapefile")
    elapsed = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - start_time))
    print(f"[INFO]  | 合并完成，文件已保存到：{output_file}")
    print(f"[TIME]  | 总耗时: {elapsed}")

    return output_file


def main() -> None:
    """
    主函数，负责调用合并 Shapefile 的功能。

    Returns:
        None
    """
    try:
        merge_shapefiles(INPUT_FOLDER, OUTPUT_FOLDER, OUTPUT_FILE)
    except Exception as err:
        print(f"[ERROR] | 发生错误：{err}")


if __name__ == "__main__":
    main()