#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
from typing import List, Dict, Any

import pandas as pd
from dbfread import DBF


def dbf_to_excel(dbf_folder: str, output_excel_path: str) -> None:
    """将文件夹中的所有DBF文件转换为Excel工作簿，每个DBF文件转为单独工作表。
    新增功能：
    1. 将值为 -1 或大于 90 的值替换为空。
    2. 增加子表 Std_all，将 Std_2010、Std_2015 和 Std_2020 三个子表按顺序合并。
    3. 调整 kml_name 列的内容，取 '_' 分割的第一个部分。

    Args:
        dbf_folder: 包含DBF文件的文件夹路径
        output_excel_path: 输出Excel文件的绝对路径

    Raises:
        FileNotFoundError: 当输入文件夹不存在时
        PermissionError: 当输出路径无写入权限时
        Exception: 处理DBF文件时发生的其他异常
    """
    start_time = time.time()
    print(f"[INFO]  | 任务启动: 转换 {dbf_folder} 中的DBF文件到 {output_excel_path}")

    if not os.path.exists(dbf_folder):
        error_message = f"输入文件夹不存在: {dbf_folder}"
        print(f"[ERROR] | {error_message}")
        raise FileNotFoundError(error_message)

    if not os.access(os.path.dirname(output_excel_path), os.W_OK):
        error_message = f"输出路径无写入权限: {output_excel_path}"
        print(f"[ERROR] | {error_message}")
        raise PermissionError(error_message)

    valid_files: List[str] = [
        f for f in os.listdir(dbf_folder)
        if f.lower().endswith(".dbf")
    ]

    if not valid_files:
        print(f"[WARN]  | 文件夹中没有找到DBF文件: {dbf_folder}")
        return

    print(f"[INFO]  | 发现 {len(valid_files)} 个DBF文件待处理")

    processed_count: int = 0
    dfs: Dict[str, pd.DataFrame] = {}  # 用于存储每个子表的数据
    with pd.ExcelWriter(output_excel_path, engine="openpyxl") as excel_writer:
        for filename in valid_files:
            sheet_name: str = os.path.splitext(filename)[0]
            dbf_path: str = os.path.join(dbf_folder, filename)

            try:
                file_start = time.time()
                with DBF(dbf_path) as dbf_table:
                    df: pd.DataFrame = pd.DataFrame(iter(dbf_table))

                    # 新增功能：将值为 -1 或大于 90 的值替换为空
                    for column in df.columns:
                        df[column] = df[column].apply(
                            lambda x: None if x == -1 or (isinstance(x, (int, float)) and x > 120) else x
                        )

                    # 调整 kml_name 列的内容
                    if 'kml_name' in df.columns:
                        df['kml_name'] = df['kml_name'].apply(lambda x: x.split('_')[0] if isinstance(x, str) else x)

                    # 保存到字典中
                    dfs[sheet_name] = df

                    df.to_excel(
                        excel_writer,
                        sheet_name=sheet_name[:31],  # Excel工作表名最大31字符
                        index=False
                    )
                file_elapsed = time.time() - file_start
                print(
                    f"[INFO]  | 转换成功: {filename} → {sheet_name} "
                    f"(记录数: {len(df)}, 耗时: {file_elapsed:.2f}s)"
                )
                processed_count += 1
            except Exception as error:
                print(
                    f"[ERROR] | 处理 {filename} 时出错: {error} ",
                    f"文件路径: {dbf_path}"
                )

        # 合并 Std_2010、Std_2015 和 Std_2020 为 Std_all
        if 'Std_2010' in dfs and 'Std_2015' in dfs and 'Std_2020' in dfs:
            std_all = pd.concat([dfs['Std_2010'], dfs['Std_2015'], dfs['Std_2020']], axis=1)
            std_all.to_excel(
                excel_writer,
                sheet_name='Std_all',
                index=False
            )
            print(f"[INFO]  | 成功创建子表 Std_all")

    total_elapsed = time.strftime(
        "%Hh%Mm%Ss",
        time.gmtime(time.time() - start_time)
    )
    print(
        f"[INFO]  | 任务完成: 成功转换 {processed_count}/{len(valid_files)} 个文件, "
        f"总耗时: {total_elapsed}"
    )
    print(f"[INFO]  | Excel文件已保存至: {output_excel_path}")


if __name__ == "__main__":
    DBF_FOLDER = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\_AccuracyEvaluation\_kml_to_std\all_test"
    OUTPUT_EXCEL_PATH = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\_AccuracyEvaluation\_kml_to_std\all_test_check.xlsx"

    dbf_to_excel(
        dbf_folder=DBF_FOLDER,
        output_excel_path=OUTPUT_EXCEL_PATH
    )