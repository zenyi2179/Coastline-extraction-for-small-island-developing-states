import arcpy
import os
import pandas as pd
import numpy as np

def calculate_statistics(dbf_path: str, sheet_name: str) -> pd.DataFrame:
    """对 DBF 文件的 NEAR_DIST 字段进行统计计算。

    Args:
        dbf_path: DBF 文件路径
        sheet_name: 文件名（不含扩展名）

    Returns:
        DataFrame: 包含当前 DBF 文件统计结果的 DataFrame
    """
    # 检查文件是否存在
    if not arcpy.Exists(dbf_path):
        raise FileNotFoundError(f"[ERROR] | 文件不存在：{dbf_path}")

    # 读取 DBF 文件
    try:
        table = arcpy.da.TableToNumPyArray(dbf_path, ["NEAR_DIST"])
    except Exception as e:
        print(f"[WARN]  | 文件 {sheet_name} 中没有 NEAR_DIST 字段，跳过此文件。")
        return pd.DataFrame()

    # 将 NumPy 数组转换为 Pandas DataFrame
    sheet_data = pd.DataFrame(table)

    # 提取 NEAR_DIST 字段
    if "NEAR_DIST" not in sheet_data.columns:
        print(f"[WARN]  | 文件 {sheet_name} 中没有 NEAR_DIST 字段，跳过此文件。")
        return pd.DataFrame()

    column_values = sheet_data["NEAR_DIST"].dropna().values

    if len(column_values) == 0:
        print(f"[WARN]  | 文件 {sheet_name} 中没有有效的 NEAR_DIST 数据，跳过此文件。")
        return pd.DataFrame()

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
            "Mean Offset": [f"{mean_value:.2f}m"],
            "RMSE": [f"{rmse:.2f}m"],
            "≤1(30m)": [f"{percent_30:.2f}%"],
            "≤2(60m)": [f"{percent_60:.2f}%"],
            "≤3(90m)": [f"{percent_90:.2f}%"],
            "Match Pt. Count": [count_all],
            "count_30": [count_30],
            "count_60": [count_60],
            "count_90": [count_90],
            "std_dev": [f"{std_dev:.2f}m"],
        },
        index=[sheet_name],
    )

    return temp_df

def process_dbf_files(folder_path: str, output_excel: str) -> None:
    """处理目标文件夹中的所有 DBF 文件，并将统计结果写入 Excel 文件。

    Args:
        folder_path: 目标文件夹路径
        output_excel: 输出 Excel 文件路径
    """
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"[ERROR] | 目标文件夹路径不存在：{folder_path}")

    # 遍历文件夹中的所有文件
    dbf_files = [f for f in os.listdir(folder_path) if f.endswith('.dbf')]

    # 初始化一个空的 DataFrame 用于保存所有统计结果
    all_statistics = pd.DataFrame()

    for dbf_file in dbf_files:
        dbf_path = os.path.join(folder_path, dbf_file)
        sheet_name = os.path.splitext(dbf_file)[0]

        try:
            # 计算统计信息
            statistics = calculate_statistics(dbf_path, sheet_name)
            all_statistics = pd.concat([all_statistics, statistics])
        except Exception as e:
            print(f"[ERROR] | 处理文件 {dbf_file} 时发生错误：{e}")

    # 调整列的顺序
    all_statistics = all_statistics[
        ["Mean Offset", "≤1(30m)", "≤2(60m)", "≤3(90m)", "Match Pt. Count", "count_30", "count_60", "count_90", "std_dev", "RMSE"]
    ]

    # 将所有统计结果写入 Excel 文件
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        all_statistics.to_excel(writer, sheet_name='Summary')

    print(f"[INFO]  | 统计结果已保存到：{output_excel}")

if __name__ == "__main__":
    folder_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\Analyze\consistency_check\neighborhood"
    output_excel = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\Statistics\consistency_check\result_summary.xlsx"

    print(f"[INFO]  | 任务启动，PID={os.getpid()}")
    try:
        process_dbf_files(folder_path, output_excel)
        print(f"[INFO]  | 任务完成")
    except Exception as err:
        print(f"[ERROR] | 发生错误：{err}")