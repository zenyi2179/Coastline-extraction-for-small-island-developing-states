import arcpy
import pandas as pd
import time
import os


def process_dbf_files(input_files: list, value_field: str, value_prefix: str) -> pd.DataFrame:
    """
    按 gid 汇总多个 .dbf 文件中的字段数据，并输出为 DataFrame。

    :param input_files: 输入的 .dbf 文件路径列表
    :param value_field: 需要汇总的字段名，例如 "area_geo" 或 "leng_geo"
    :param value_prefix: 输出列名前缀，例如 "area" 或 "leng"
    :return: 汇总后的 DataFrame
    """
    start_time = time.time()
    print(f"[INFO]  | 开始处理字段 {value_field}，PID={os.getpid()}")

    all_dataframes = []

    # 遍历所有 dbf 文件
    for dbf_file in input_files:
        file_name = os.path.basename(dbf_file).replace(".dbf", "")
        year = file_name.split("_")[-1]  # 提取年份

        # 读取 DBF 文件
        table_array = arcpy.da.TableToNumPyArray(dbf_file, ["gid", value_field])
        dataframe = pd.DataFrame(table_array)

        # 重命名字段，带上年份
        dataframe.rename(columns={value_field: f"{value_prefix}_{year}"}, inplace=True)

        all_dataframes.append(dataframe)

    # 按 gid 合并所有表
    final_dataframe = all_dataframes[0]
    for dataframe in all_dataframes[1:]:
        final_dataframe = pd.merge(final_dataframe, dataframe, on="gid", how="outer")

    end_time = time.time()
    elapsed_time = end_time - start_time
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"[TIME]  | 字段 {value_field} 处理完成，总耗时: {int(hours):02d}h{int(minutes):02d}m{int(seconds):02d}s")

    return final_dataframe


def main() -> None:
    """
    主函数：处理 polygon 和 polyline 的 .dbf 文件，并输出到同一个 Excel 文件的两个子表。
    """
    start_time = time.time()
    print(f"[INFO]  | 任务启动，PID={os.getpid()}")

    # 输入文件路径 - polygon
    polygon_files = [
        r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\SIDS_SV_polygon_2010.dbf",
        r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\SIDS_SV_polygon_2015.dbf",
        r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\SIDS_SV_polygon_2020.dbf"
    ]

    # 输入文件路径 - polyline
    polyline_files = [
        r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\SIDS_SV_polyline_2010.dbf",
        r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\SIDS_SV_polyline_2015.dbf",
        r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\SIDS_SV_polyline_2020.dbf"
    ]

    # 输出文件路径
    output_excel_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\汇总数据.xlsx"

    # 处理 polygon 数据
    polygon_dataframe = process_dbf_files(polygon_files, "area_geo", "area")

    # 处理 polyline 数据
    polyline_dataframe = process_dbf_files(polyline_files, "leng_geo", "leng")

    # 写入同一个 Excel，不同子表
    with pd.ExcelWriter(output_excel_path, engine="openpyxl") as writer:
        polygon_dataframe.to_excel(writer, sheet_name="SIDS_SV_polygon", index=False)
        polyline_dataframe.to_excel(writer, sheet_name="SIDS_SV_polyline", index=False)

    end_time = time.time()
    elapsed_time = end_time - start_time
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"[TIME]  | 全部任务完成，总耗时: {int(hours):02d}h{int(minutes):02d}m{int(seconds):02d}s")


if __name__ == "__main__":
    main()
