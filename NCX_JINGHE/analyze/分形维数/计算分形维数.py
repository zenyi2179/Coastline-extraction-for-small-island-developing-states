#!/usr/bin/env python3
import os
import time
import uuid
from typing import Dict, List, Tuple

import arcpy
import numpy as np
import pandas as pd


def load_and_validate_shapefile(file_path: str) -> str:
    """读取并验证 Shapefile 文件，只返回路径。"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"输入文件不存在: {file_path}")

    desc = arcpy.Describe(file_path)
    if desc.spatialReference is None:
        raise ValueError(f"缺少投影坐标系: {file_path}")

    return file_path


def count_occupied_grids(grids_path: str, coastline_path: str) -> int:
    """统计被海岸线占用的格网数量。"""
    # 给临时图层取唯一名，避免重复
    grids_tmp = f"grids_{uuid.uuid4().hex}"
    coast_tmp = f"coast_{uuid.uuid4().hex}"

    arcpy.MakeFeatureLayer_management(grids_path, grids_tmp)
    arcpy.MakeFeatureLayer_management(coastline_path, coast_tmp)

    arcpy.SelectLayerByLocation_management(
        grids_tmp, "INTERSECT", coast_tmp, "", "NEW_SELECTION"
    )
    count = int(arcpy.GetCount_management(grids_tmp).getOutput(0))

    # 清理选择 & 删除临时图层
    arcpy.SelectLayerByAttribute_management(grids_tmp, "CLEAR_SELECTION")
    arcpy.Delete_management(grids_tmp)
    arcpy.Delete_management(coast_tmp)

    return count


def calculate_fractal_dimension(
    epsilons: List[int], counts: List[int]
) -> Tuple[float, np.ndarray, np.ndarray]:
    """基于 Box-counting 方法计算分形维数。"""
    eps_arr = np.array(epsilons)
    counts_arr = np.array(counts)

    mask = counts_arr > 0
    eps_arr = eps_arr[mask]
    counts_arr = counts_arr[mask]

    log_eps = -np.log(eps_arr)
    log_counts = np.log(counts_arr)

    coef = np.polyfit(log_eps, log_counts, 1)
    fractal_dimension = float(coef[0])

    return fractal_dimension, log_eps, log_counts


def export_results(
    output_path: str, epsilons: List[int], counts: List[int], fractal_dimension: float
) -> None:
    """导出计算结果为 CSV。"""
    df_result = pd.DataFrame(
        {
            "grid_size_m": epsilons,
            "occupied_grids": counts,
        }
    )
    df_result["fractal_dimension"] = fractal_dimension
    df_result.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[INFO]  | 结果已保存到 {output_path}")


def main() -> None:
    """程序主入口，计算海岸线分形维数。"""
    start_time = time.time()

    list_coastline_fp = [
        r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData"
        r"\_ThirdProductEvaluation\_third_party_dataset\SIDS_SV_polyline_2010.shp",
        r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData"
        r"\_ThirdProductEvaluation\_third_party_dataset\SIDS_SV_polyline_2015.shp",
        r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData"
        r"\_ThirdProductEvaluation\_third_party_dataset\SIDS_SV_polyline_2020.shp",
        r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData"
        r"\_ThirdProductEvaluation\_third_party_dataset\GCL_FCS30_2010.shp",
        r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData"
        r"\_ThirdProductEvaluation\_third_party_dataset\GCL_FCS30_2015.shp",
        r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData"
        r"\_ThirdProductEvaluation\_third_party_dataset\GCL_FCS30_2020.shp",
        r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData"
        r"\_ThirdProductEvaluation\_third_party_dataset\GMSSD_2015.shp",
        r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData"
        r"\_ThirdProductEvaluation\_third_party_dataset\GSV_2015.shp",
        r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData"
        r"\_ThirdProductEvaluation\_third_party_dataset\OSM_2020.shp",
    ]

    for coastline_fp in list_coastline_fp:
        print(f"[INFO]  | 任务启动，PID={os.getpid()}")
        name_coastline_fp = os.path.splitext(os.path.basename(coastline_fp))[0]

        grid_files: Dict[int, str] = {
            12000: (
                r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV"
                r"\SIDS_SV_v1_compile\Analyze\fractal_dimension\grids\grids_12000m.shp"
            ),
            4800: (
                r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV"
                r"\SIDS_SV_v1_compile\Analyze\fractal_dimension\grids\grids_4800m.shp"
            ),
            2400: (
                r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV"
                r"\SIDS_SV_v1_compile\Analyze\fractal_dimension\grids\grids_2400m.shp"
            ),
            900: (
                r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV"
                r"\SIDS_SV_v1_compile\Analyze\fractal_dimension\grids\grids_900m.shp"
            ),
            300: (
                r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV"
                r"\SIDS_SV_v1_compile\Analyze\fractal_dimension\grids\grids_300m.shp"
            ),
        }

        print(f"[INFO]  | 加载海岸线数据 {coastline_fp}")
        coastline_path = load_and_validate_shapefile(coastline_fp)

        epsilons: List[int] = []
        counts: List[int] = []

        for res, fp in grid_files.items():
            print(f"[INFO]  | 处理格网: {res}m ({os.path.basename(fp)})")
            grids_path = load_and_validate_shapefile(fp)
            occupied = count_occupied_grids(
                grids_path=grids_path, coastline_path=coastline_path
            )
            print(f"[INFO]  | 占有格网数: {occupied}")

            epsilons.append(res)
            counts.append(occupied)

        fractal_dimension, log_eps, log_counts = calculate_fractal_dimension(
            epsilons=epsilons, counts=counts
        )

        print("\n====== 结果 ======")
        for e, c in zip(epsilons, counts):
            print(f"尺度 {e:>6} m : 占有格网数 = {c}")
        print(f"\n估计分形维数: {fractal_dimension:.3f}")

        export_results(
            output_path=fr"FD_{name_coastline_fp}.csv",
            epsilons=epsilons,
            counts=counts,
            fractal_dimension=fractal_dimension,
        )

        elapsed = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - start_time))
        print(f"[TIME]  | 总耗时: {elapsed}")


if __name__ == "__main__":
    main()
