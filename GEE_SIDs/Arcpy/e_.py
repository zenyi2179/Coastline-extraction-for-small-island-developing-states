# -*- coding:utf-8 -*-
"""
作者：23242
日期：2024年12月05日
"""
from _tools import list_files_with_extension

# png_list = list_files_with_extension(
#     folder_path=fr"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\Tif_Thumbnail_check\threshold_5_5_10",
#     extension=fr".png", if_print=1)
#
# for png in png_list:
#     print(png.split('_')[0])

# import os
#
# def rename_files_in_folder(folder_path, substring_to_remove):
#     """
#     批量修改文件名，删除指定子字符串。
#
#     参数:
#     - folder_path (str): 文件夹路径。
#     - substring_to_remove (str): 要删除的子字符串。
#     """
#     # 遍历文件夹中的所有文件
#     for filename in os.listdir(folder_path):
#         # 检查文件名是否包含需要删除的子字符串
#         if substring_to_remove in filename:
#             # 新文件名
#             new_filename = filename.replace(substring_to_remove, "")
#             # 获取完整路径
#             old_file_path = os.path.join(folder_path, filename)
#             new_file_path = os.path.join(folder_path, new_filename)
#             # 重命名文件
#             os.rename(old_file_path, new_file_path)
#             print(f"Renamed: {filename} -> {new_filename}")
#
# if __name__ == "__main__":
#     # 文件夹路径
#     folder_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\Tif_Thumbnail_check\threshold_5_5_10"
#     # 要删除的子字符串
#     substring_to_remove = "_ls578_Index"
#
#     # 执行重命名
#     rename_files_in_folder(folder_path, substring_to_remove)


# import pandas as pd
# import dbf
#
#
# def excel_to_dbf(excel_path, sheet_name, dbf_path):
#     """
#     将Excel文件中的指定子表转换为DBF文件。
#
#     参数:
#     excel_path: str - Excel文件的路径。
#     sheet_name: str - 要转换的子表名称。
#     dbf_path: str - 输出DBF文件的路径。
#     """
#     try:
#         # 读取Excel文件中的指定子表
#         df = pd.read_excel(excel_path, sheet_name=sheet_name)
#
#         # 将DataFrame保存为DBF文件
#         # 创建DBF文件，不使用new参数
#         dbf_file = dbf.Dbf(dbf_path, codec='utf-8')
#         for column in df.columns:
#             if df[column].dtype == 'object':
#                 dbf_file.add_field(column, 'C', size=df[column].astype(str).apply(len).max())
#             elif df[column].dtype == 'int64':
#                 dbf_file.add_field(column, 'N', 10, 0)
#             elif df[column].dtype == 'float64':
#                 dbf_file.add_field(column, 'N', 18, 6)
#             else:
#                 # 其他数据类型可以根据需要添加
#                 pass
#
#         # 写入数据
#         for index, row in df.iterrows():
#             dbf_file.write_record(dict(row))
#
#         dbf_file.close()
#         print(f"成功将子表'{sheet_name}'转换为DBF文件，并保存到'{dbf_path}'。")
#     except Exception as e:
#         print(f"转换过程中发生错误: {e}")
#
#
# # 使用示例
# excel_path = r'E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\Tif_Thumbnail_check\_check.xlsx'
# sheet_name = 'fix_v1'
# dbf_path = r'E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\Tif_Thumbnail_check\_fix_v1.dbf'
#
# excel_to_dbf(excel_path, sheet_name, dbf_path)


# import os
#
# def rename_files(folder_path):
#     """
#     批量修改文件名，将指定子字符串从文件名中删除。
#
#     参数:
#     - folder_path (str): 文件夹路径。
#     - substring_to_remove (str): 要删除的子字符串，例如 "_43_DBNDWI.tif"。
#     """
#     for filename in os.listdir(folder_path):
#
#         # 获取新文件名
#         temp_name = filename.split('_')[0]
#         new_filename = temp_name + '.' + filename.split('.')[-1]
#         # 构造完整的文件路径
#         old_file_path = os.path.join(folder_path, filename)
#         new_file_path = os.path.join(folder_path, new_filename)
#         # 重命名文件
#         os.rename(old_file_path, new_file_path)
#         print(f"Renamed: {filename} -> {new_filename}")
#
#
#         # # 检查文件是否包含需要删除的子字符串
#         # if substring_to_remove in filename:
#         #     # 获取新文件名
#         #     new_filename = filename.replace(substring_to_remove, ".tif")
#         #     # 构造完整的文件路径
#         #     old_file_path = os.path.join(folder_path, filename)
#         #     new_file_path = os.path.join(folder_path, new_filename)
#         #     # 重命名文件
#         #     os.rename(old_file_path, new_file_path)
#         #     print(f"Renamed: {filename} -> {new_filename}")
#
# if __name__ == "__main__":
#     # 文件夹路径
#     folder_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\SIDs_Grid_Y20"
#
#     # 执行重命名
#     rename_files(folder_path)


import pandas as pd
import dbf


def excel_to_dbf(input_excel_path, sheet_name, output_dbf_path):
    """
    将 Excel 的指定工作表导出为 DBF 文件，保留数据类型和列名格式。

    参数:
        input_excel_path (str): 输入的 Excel 文件路径。
        sheet_name (str): 需要读取的工作表名称。
        output_dbf_path (str): 导出的 DBF 文件路径。
    """
    # 读取 Excel 的指定表
    df = pd.read_excel(input_excel_path, sheet_name=sheet_name)

    # 定义字段字符串列表，根据数据类型进行动态判断
    def get_field_definition(column):
        if df[column].dtype == 'object':  # 字符类型
            return f"{column} C(255)"
        elif pd.api.types.is_integer_dtype(df[column]):  # 整型
            return f"{column} N(10,0)"  # 整型无需小数位，最大宽度10
        elif pd.api.types.is_float_dtype(df[column]):  # 浮点型
            # 判断小数位数
            max_decimal_places = df[column].apply(
                lambda x: len(str(x).split(".")[1]) if pd.notnull(x) and "." in str(x) else 0
            ).max()
            return f"{column} N(18,{min(max_decimal_places, 5)})"  # 浮点型设置小数位，限制最大5位
        elif pd.api.types.is_datetime64_any_dtype(df[column]):  # 日期类型
            return f"{column} D"
        else:
            raise ValueError(f"Unsupported column type for {column}")

    # 生成字段定义，确保列名格式不变
    field_definitions = ";".join([get_field_definition(col) for col in df.columns])

    # 使用指定编码创建 DBF 表
    table = dbf.Table(output_dbf_path, field_definitions, codepage="utf8")
    table.open(dbf.READ_WRITE)

    # 写入数据
    for _, row in df.iterrows():
        row_data = tuple(row.fillna("").to_list())  # 用空值填充 NaN
        table.append(row_data)

    table.close()
    print(f"The table {sheet_name} exported to {output_dbf_path}.")


# 使用示例
if __name__ == "__main__":
    input_excel_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\Tif_Thumbnail_check\_check.xlsx"
    sheet_name = "Sheet1"
    output_dbf_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\Tif_Thumbnail_check\2Sheet1_v1.dbf"

    excel_to_dbf(input_excel_path, sheet_name, output_dbf_path)

# simpledbf


#    D:\ArcGISPro3\Pro\bin\Python\envs\arcgispro-py3\python.exe -m pip install --user simpledbf -i https://pypi.doubanio.com/simple/
