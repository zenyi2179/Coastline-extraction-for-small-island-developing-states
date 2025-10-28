from dbfread import DBF


def read_dbf_to_list(dbf_path, columns=None, if_print=0):
    """
    读取 DBF 文件并将内容存储为二维列表。

    参数:
    dbf_path (str): DBF 文件的路径。
    columns (list): 需要读取的列名列表，若为 None 则读取所有列。
    if_print (int): 是否打印二维列表的开关，0表示不打印，1表示打印。

    返回:
    list_of_records (list): 二维列表，每个子列表代表一条记录。
    """
    list_of_records = []
    dbf = DBF(dbf_path, encoding='utf-8')  # 打开 DBF 文件并设置编码为 'utf-8'

    # 获取 DBF 文件的字段名称，即表头
    field_names = [field.name for field in dbf.fields]

    # 遍历 DBF 文件中的每条记录
    for record in dbf:
        # 若指定了需要读取的列，则只提取这些列的值
        if columns is not None:
            record_values = [record[field_name] for field_name in columns if field_name in field_names]
        else:
            record_values = list(record.values())

        # 将记录的值添加到二维列表中
        list_of_records.append(record_values)

    # 根据 if_print 参数决定是否打印二维列表
    if if_print:
        print("Records list:")
        print(list_of_records)

    return list_of_records


def main():
    pass


if __name__ == '__main__':
    main()