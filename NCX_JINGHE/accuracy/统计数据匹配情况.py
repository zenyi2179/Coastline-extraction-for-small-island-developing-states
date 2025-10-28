#!/usr/bin/env python3
import os
import time
from typing import Any

import numpy as np
import pandas as pd


def calculate_statistics(sheet_data: pd.DataFrame, sheet_name: str) -> pd.DataFrame:
    """对 Excel 子表的每一列进行统计计算。

    Args:
        sheet_data: 当前子表的 DataFrame 数据
        sheet_name: 子表名称

    Returns:
        DataFrame: 包含当前子表统计结果的 DataFrame
    """
    statistics_results: pd.DataFrame = pd.DataFrame()
    columns_to_analyze = [col for col in sheet_data.columns if col != "kml_name"]

    for column in columns_to_analyze:
        column_values = sheet_data[column].dropna().values

        if len(column_values) == 0:
            continue

        column_array = np.array(column_values, dtype=float)

        count_30 = int(np.sum(column_array < 30))
        count_60 = int(np.sum(column_array < 60))
        count_90 = int(np.sum(column_array < 90))
        count_all = int(len(column_array))

        percent_30 = count_30 / count_all * 100
        percent_60 = count_60 / count_all * 100
        percent_90 = count_90 / count_all * 100

        mean_value = float(np.mean(column_array))
        std_dev = float(np.std(column_array))
        rmse = float(np.sqrt(np.mean(column_array**2)))

        temp_df = pd.DataFrame(
            {
                "mean_value": [f"{mean_value:.2f}m"],
                "std_dev": [f"{std_dev:.2f}m"],
                "rmse": [f"{rmse:.2f}m"],
                "percent_30": [f"{percent_30:.2f}%"],
                "percent_60": [f"{percent_60:.2f}%"],
                "count_all": [count_all],
                "count_30": [count_30],
                "count_60": [count_60],
                "count_90": [count_90],
                "percent_90": [f"{percent_90:.2f}%"],
            },
            index=[f"{sheet_name}_{column}"],
        )

        statistics_results = pd.concat([statistics_results, temp_df])

    return statistics_results


def main() -> None:
    """程序主入口：读取 Excel，计算统计值，并输出到新文件。

    Raises:
        FileNotFoundError: 输入文件不存在
    """
    start_time = time.time()
    input_file_path = (
        r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV"
        r"\SIDS_SV_v1_compile\_AccuracyEvaluation\_kml_to_std\all_test_check.xlsx"
    )
    output_file_path = (
        r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV"
        r"\SIDS_SV_v1_compile\_AccuracyEvaluation\_kml_to_std\all_test_statistic.xlsx"
    )
    sheets_to_read = ["Std_2010", "Std_2015", "Std_2020"]

    if not os.path.exists(input_file_path):
        raise FileNotFoundError(f"输入文件不存在: {input_file_path}")

    print(f"[INFO]  | 任务启动，PID={os.getpid()}")
    xls = pd.ExcelFile(input_file_path)

    all_results: pd.DataFrame = pd.DataFrame()

    for sheet_name in sheets_to_read:
        if sheet_name not in xls.sheet_names:
            print(f"[WARN]  | 子表 {sheet_name} 不存在，跳过")
            continue

        sheet_df: pd.DataFrame = pd.read_excel(io=xls, sheet_name=sheet_name)
        sheet_result = calculate_statistics(sheet_df, sheet_name)
        all_results = pd.concat([all_results, sheet_result])

    all_results.to_excel(output_file_path, sheet_name="Statistics")

    print(f"[INFO]  | 统计结果已保存到 {output_file_path}")
    elapsed = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - start_time))
    print(f"[TIME]  | 总耗时: {elapsed}")


if __name__ == "__main__":
    main()
