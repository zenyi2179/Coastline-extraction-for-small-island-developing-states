import os
import pandas as pd
from dbfread import DBF


def read_dbf_file(dbf_file_path, field_name):
    """
    读取指定的 DBF 文件并获取指定字段的第一个值。
    如果字段不存在或文件为空，则返回 0。

    参数:
        dbf_file_path (str): DBF 文件的路径。
        field_name (str): 需要读取的字段名称。

    返回:
        float: 指定字段的第一个值，或 0。
    """
    try:
        # 读取 DBF 文件
        table = DBF(dbf_file_path)
        # 获取指定字段的所有值
        values = [record[field_name] for record in table if field_name in record]
        # 返回第一个值，如果列表为空则返回 0
        return values[0] if values else 0
    except Exception as e:
        print(f"读取 {dbf_file_path} 时出错: {e}")
        return 0


def process_data(data_path, data_name_list, boundary_list):
    """
    处理数据并生成二维列表，用于后续转换为 DataFrame。

    参数:
        data_path (str): 数据文件夹的路径。
        data_name_list (list): 数据表名称列表。
        boundary_list (list): 边界名称列表。

    返回:
        list: 包含所有数据的二维列表。
    """
    # 初始化二维列表，第一行为字段名
    fields_list = ['ID', 'GID'] + data_name_list
    dbf_data = [fields_list]

    # 遍历每个边界
    row_count = 1
    for boundary in boundary_list:
        row_data = [row_count, boundary]  # 初始化行数据，包含 ID 和 GID
        # 遍历每个数据表
        for data_name in data_name_list:
            # 构造 DBF 文件路径
            dbf_file_path = os.path.join(data_path, data_name, f"{boundary}\_{boundary}_merge_BV.dbf")
            # 读取 DBF 文件并获取 'Leng_Geo' 字段的值
            # length_geo_value = read_dbf_file(dbf_file_path, 'Area_Geo')
            length_geo_value = read_dbf_file(dbf_file_path, 'Leng_Geo')
            row_data.append(length_geo_value)
        # 将当前行数据添加到总数据列表中
        dbf_data.append(row_data)
        row_count += 1

    return dbf_data


def save_to_excel(data, output_file):
    """
    将二维列表数据保存为 Excel 文件。

    参数:
        data (list): 二维列表数据。
        output_file (str): 输出的 Excel 文件路径。
    """
    # 将二维列表转换为 DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])
    # 保存为 Excel 文件
    df.to_excel(output_file, index=False)
    print(f"数据已成功导出到 {output_file}")


def main():
    # 数据路径和相关参数
    data_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation"
    data_name_list = ['SIDS_CL_10', 'SIDS_CL_15', 'SIDS_CL_20',]

    # 全 37 国家
    boundary_list = ["ATG",
                     "BHS",
                     "BLZ",
                     "BRB",
                     "COM",
                     "CPV",
                     "CUB",
                     "DMA",
                     "DOM",
                     "FJI",
                     "FSM",
                     "GNB",
                     "GRD",
                     "GUY",
                     "HTI",
                     "JAM",
                     "KIR",
                     "KNA",
                     "LCA",
                     "MDV",
                     "MHL",
                     "MUS",
                     "NRU",
                     "PLW",
                     "PNG",
                     "SGP",
                     "SLB",
                     "STP",
                     "SUR",
                     "SYC",
                     "TLS",
                     "TON",
                     "TTO",
                     "TUV",
                     "VCT",
                     "VUT",
                     "WSM",
                     ]

    # 处理数据并生成二维列表
    dbf_data = process_data(data_path, data_name_list, boundary_list)
    print("生成的二维列表数据：")
    print(dbf_data)

    # 保存数据到 Excel 文件
    # output_file = "SIDS_BV岛屿面积.xlsx"
    output_file = "SIDS_BV岛屿长度.xlsx"
    save_to_excel(dbf_data, output_file)


if __name__ == "__main__":
    main()