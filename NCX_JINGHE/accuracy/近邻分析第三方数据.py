#!/usr/bin/env python3
import os
import shutil
import time
from typing import Dict, List

import arcpy


def perform_model_analysis(
        input_features: str, output_features: str, dataset_name: str
) -> None:
    """
    执行地理空间分析模型，包括近邻分析。

    Args:
        input_features: 输入要素类路径
        output_features: 近邻要素类路径
        dataset_name: 用于NEAR_DIST字段命名的数据集标识符

    Returns:
        None

    Raises:
        FileNotFoundError: 输入路径不存在
        arcpy.ExecuteError: 地理处理工具执行失败
    """
    start_time = time.time()
    process_id = os.getpid()
    print(f"[INFO]  | 任务启动，PID={process_id}")
    print(f"[INFO]  | 输入要素: {input_features}")
    print(f"[INFO]  | 近邻要素: {output_features}")
    print(f"[INFO]  | 数据集标识: {dataset_name}")

    # 检查输入路径是否存在
    if not arcpy.Exists(input_features):
        error_msg = f"输入要素不存在: {input_features}"
        print(f"[ERROR] | {error_msg}")
        raise FileNotFoundError(error_msg)

    if not arcpy.Exists(output_features):
        error_msg = f"近邻要素不存在: {output_features}"
        print(f"[ERROR] | {error_msg}")
        raise FileNotFoundError(error_msg)

    try:
        # 设置环境变量
        arcpy.env.overwriteOutput = True

        # 执行近邻分析
        arcpy.analysis.Near(
            in_features=input_features,
            near_features=output_features,
            search_radius="150 Meters",
            method="GEODESIC",
            field_names=[["NEAR_DIST", dataset_name]],
            distance_unit="Meters",
        )
        print(f"[INFO]  | 近邻分析完成: {dataset_name}")

    except arcpy.ExecuteError as gp_error:
        error_details = arcpy.GetMessages(2)
        print(f"[ERROR] | 地理处理失败: {error_details}")
        raise arcpy.ExecuteError(error_details) from gp_error

    except Exception as unexpected_error:
        print(f"[ERROR] | 未预期的错误: {unexpected_error}")
        raise

    finally:
        elapsed_seconds = time.time() - start_time
        formatted_time = time.strftime("%Hh%Mm%Ss", time.gmtime(elapsed_seconds))
        print(f"[TIME]  | 总耗时: {formatted_time}")


def main() -> None:
    """主函数：协调整个分析流程"""
    base_folder = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile"
    base_dataset_folder = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\_third_party_dataset"

    # 数据集名称映射
    dataset_name_mapping: Dict[str, str] = {
        "SIDS_SV_polyline_2010": "SV_2010",
        "SIDS_SV_polyline_2015": "SV_2015",
        "SIDS_SV_polyline_2020": "SV_2020",
        "GCL_FCS30_10_37": "FCS30_2010",
        "GCL_FCS30_15_37": "FCS30_2015",
        "GCL_FCS30_20_37": "FCS30_2020",
        "GMSSD_2015_37": "GMSSD_2015",
        "GSV_37": "GSV_2015",
        "OSM_37": "OSM_2020",
    }

    # 按年份组织数据集
    datasets_by_year: Dict[int, List[str]] = {
        2010: ["SIDS_SV_polyline_2010", "GCL_FCS30_10_37"],
        2015: ["SIDS_SV_polyline_2015", "GCL_FCS30_15_37", "GMSSD_2015_37", "GSV_37"],
        2020: ["SIDS_SV_polyline_2020", "GCL_FCS30_20_37", "OSM_37"],
    }

    # 选择要处理的年份
    target_years = [2010, 2015, 2020]
    # target_years = [2020]

    # 准备测试目录
    source_dir = os.path.join(base_folder, r"_AccuracyEvaluation\_kml_to_std\all")
    dest_dir = os.path.join(base_folder, r"_AccuracyEvaluation\_kml_to_std\all_test")

    # if os.path.exists(dest_dir):
    #     shutil.rmtree(dest_dir)
    # shutil.copytree(source_dir, dest_dir)
    # print(f"[INFO]  | 复制测试数据: {source_dir} -> {dest_dir}")


    # 处理每个选定的年份
    for year in target_years:
        standard_shapefile = os.path.join(dest_dir, f"Std_{year}.shp")
        year_datasets = datasets_by_year.get(year, [])

        if not year_datasets:
            print(f"[WARN]  | {year}年无可用数据集")
            continue

        for dataset in year_datasets:
            near_dataset = os.path.join(base_dataset_folder, f"{dataset}.shp")
            dataset_id = dataset_name_mapping.get(dataset, "UNKNOWN")

            perform_model_analysis(
                input_features=standard_shapefile,
                output_features=near_dataset,
                dataset_name=dataset_id,
            )

        arcpy.management.DeleteField(
            in_table=standard_shapefile,
            drop_field=["Name", "Descriptio", "NEAR_FID"],
            method="DELETE_FIELDS")


if __name__ == "__main__":
    main_start = time.time()
    main()
    total_elapsed = time.time() - main_start
    total_time = time.strftime("%Hh%Mm%Ss", time.gmtime(total_elapsed))
    print(f"[TIME]  | 程序总运行时间: {total_time}")