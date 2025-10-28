from dbfread import DBF


def read_dbf_to_list(dbf_path, if_print=0):
    """
    读取 DBF 文件并将内容存储为二维列表。

    参数:
    dbf_path (str): DBF 文件的路径。
    if_print (int): 是否打印二维列表的开关，0表示不打印，1表示打印。

    返回:
    list_of_records (list): 二维列表，每个子列表代表一条记录。
    """
    list_of_records = []
    dbf = DBF(dbf_path, encoding='utf-8')  # 打开 DBF 文件并设置编码为 'utf-8'

    # 获取并打印 DBF 文件的字段名称，即表头
    # print("Field names:", [field.name for field in dbf.fields])

    # 遍历 DBF 文件中的每条记录
    for record in dbf:
        # 将每条记录的值转换为列表，并添加到二维列表中
        list_of_records.append(list(record.values()))

    # 根据 if_print 参数决定是否打印二维列表
    if if_print:
        print("Records list:")
        print(list_of_records)

    return list_of_records


if __name__ == '__main__':
    # 使用示例
    dbf_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\b_Global_Island_Grid\_DGS_GSV_Grid_eez_v2.dbf"
    # 调用函数并传入 DBF 文件路径，设置 if_print 参数为 0 表示不打印记录列表
    records_list = read_dbf_to_list(dbf_path, if_print=1)
