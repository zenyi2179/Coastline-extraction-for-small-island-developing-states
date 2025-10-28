import os
import dbf

def read_dbf_column(dbf_path, column_index):
    """
    读取 .dbf 文件指定列的内容并输出为列表。
    :param dbf_path: .dbf 文件的路径
    :param column_index: 列的索引（从0开始计数）
    :return: 指定列的内容列表
    """
    try:
        # 打开 .dbf 文件
        table = dbf.Table(dbf_path)
        table.open()

        # 获取表的列名
        column_names = table.field_names

        # 检查列索引是否有效
        if column_index < 0 or column_index >= len(column_names):
            raise ValueError(f"无效的列索引：{column_index}。有效范围是 0 到 {len(column_names) - 1}。")

        # 获取指定列的列名
        target_column_name = column_names[column_index]

        # 读取指定列的内容，并去除多余的空格
        column_data = [record[target_column_name].strip() for record in table]

        # 关闭表
        table.close()

        return column_data

    except Exception as e:
        print(f"[ERROR] 读取 .dbf 文件时出错：{e}")
        return []

def delete_unmatched_files(folder_path, valid_prefixes):
    """
    删除文件夹中不匹配的文件。
    :param folder_path: 文件夹路径
    :param valid_prefixes: 有效的文件名前缀列表
    """
    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        # 提取文件名中 '_' 分割后的第一部分
        prefix = filename.split('_')[0]
        # 检查前缀是否在有效前缀列表中
        if prefix not in valid_prefixes:
            # 删除不匹配的文件
            file_path = os.path.join(folder_path, filename)
            os.remove(file_path)
            print(f"[INFO] 删除文件：{file_path}")

def main():
    dbf_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\d_SIDS_Boundary\SIDS_Grids\_sids_grids_shoreline_37.dbf"
    folder_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\GEE_1_12_neg_mndwi\SIDs_Grid_2020"
    column_index = 4  # 第四列的索引（从0开始计数）

    # 读取第四列的内容
    valid_prefixes = read_dbf_column(dbf_path, column_index)

    # 输出有效前缀列表
    print(f"[INFO] 有效的文件名前缀列表：{valid_prefixes}")

    # 删除不匹配的文件
    delete_unmatched_files(folder_path, valid_prefixes)

if __name__ == '__main__':
    main()