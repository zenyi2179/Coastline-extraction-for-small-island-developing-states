from dbfread import DBF


def get_dbf_row_count(dbf_file):
    try:
        # 打开 DBF 文件
        table = DBF(dbf_file)

        # 获取行数
        row_count = len(table)

        # if row_count != 100:

        print(f"DBF 文件 {dbf_file} 中的行数为：{row_count}")
        return row_count
    except Exception as e:
        print(f"读取 DBF 文件时出错：{e}")


def read_txt_to_list(file_path: str) -> list[str]:
    """
    读取文本文件内容为列表
    :param file_path: 文本文件路径
    :return: 行内容组成的字符串列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        print(f"[ERROR] 读取文件失败 {file_path}: {e}")
        return []


if __name__ == '__main__':
    list_year = ['2010', '2015', '2020']
    list_sids = read_txt_to_list(file_path=fr"SIDS_37.txt")

    for sid in list_sids:
        for year in list_year:
            dbf_file_path = \
                fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\_kml\{sid}\{sid}_match_{year}.dbf"
            get_dbf_row_count(dbf_file_path)