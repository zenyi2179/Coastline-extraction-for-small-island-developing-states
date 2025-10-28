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
            max_length = df[column].apply(lambda x: len(str(x)) if pd.notnull(x) else 0).max()
            # 为避免溢出，确保至少 30 个字符
            max_length = max(max_length, 30)
            return f"{column} C({max_length})"
        elif pd.api.types.is_integer_dtype(df[column]):  # 整型
            max_int = df[column].max()
            width = len(str(abs(max_int)))  # 根据最大整数的位数设置宽度
            # 为避免溢出，确保至少 12 位宽度
            width = max(width, 12)
            return f"{column} N({width},0)"  # 整型宽度
        elif pd.api.types.is_float_dtype(df[column]):  # 浮点型
            max_decimal_places = df[column].apply(
                lambda x: len(str(x).split(".")[1]) if pd.notnull(x) and "." in str(x) else 0
            ).max()
            max_float = df[column].max()
            integer_part_width = len(str(abs(int(max_float))))
            # 为避免溢出，确保至少 15 位宽度（整数+小数）
            total_width = integer_part_width + max_decimal_places + 1
            total_width = max(total_width, 15)  # 确保宽度至少为 15
            return f"{column} N({total_width},{min(max_decimal_places, 5)})"  # 整数位+小数位
        elif pd.api.types.is_datetime64_any_dtype(df[column]):  # 日期类型
            return f"{column} D"
        else:
            raise ValueError(f"Unsupported column type for {column}")

    # 生成字段定义，确保列名格式不变
    field_definitions = ";".join([get_field_definition(col) for col in df.columns])

    # 使用指定编码创建 DBF 表，使用 'cp936' 作为中文编码
    table = dbf.Table(output_dbf_path, field_definitions, codepage="cp936")
    table.open(dbf.READ_WRITE)

    # 写入数据
    for _, row in df.iterrows():
        row_data = tuple(row.fillna("").to_list())  # 用空值填充 NaN
        table.append(row_data)

    table.close()
    print(f"The table {sheet_name} exported to {output_dbf_path}.")


def main():
    input_excel_path = r"C:\Users\23242\Desktop\PNG_grid.xlsx"
    sheet_name = "Sheet1"
    output_dbf_path = r"C:\Users\23242\Desktop\PNG_grid.dbf"

    excel_to_dbf(input_excel_path, sheet_name, output_dbf_path)
    pass


# 使用示例
if __name__ == "__main__":
    main()
