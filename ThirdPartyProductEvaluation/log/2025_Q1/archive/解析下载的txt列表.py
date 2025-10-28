# -*- coding: utf-8 -*-
"""
从 txt 文件中解析出 'earthdem/' 开头、指定后缀（.shp, .shx, .dbf）的文件名称
作者：朱昱
日期：2025-06-17
"""

import os

def extract_target_filenames(txt_path):
    """
    从指定 txt 文件中提取特定前缀和后缀的文件名

    参数:
        txt_path (str): 输入 txt 文件路径

    返回:
        List[str]: 符合条件的文件名列表（不含路径）
    """
    # 定义目标后缀
    target_suffixes = {'.shp', '.shx', '.dbf'}
    result_list = []

    with open(txt_path, 'r', encoding='utf-8') as file:
        for line in file:
            parts = line.strip().split('\t')
            if len(parts) != 2:
                continue  # 跳过格式异常行

            path = parts[1]

            # 检查前缀是否为 'earthdem/' 且后缀匹配
            if path.startswith('earthdem/') and os.path.splitext(path)[1] in target_suffixes:
                # filename = os.path.basename(path)
                filename = path
                result_list.append(filename)

    return result_list


# 示例调用
if __name__ == '__main__':
    txt_file = fr'E:\ArcData\Arcticdata\filelist.txt'  # 替换为实际路径
    file_names = extract_target_filenames(txt_file)
    print("提取的文件名列表：", txt_file, len(file_names))
    for name in file_names[:6]:
        # 文件路径 earthdem/earthdem_02_southeast_canada/utm20n_53_02_2_2/output/utm20n_53_02_2_2_coast_tide_thre50_v1.0.dbf
        file_path = name
        # 文件名称 utm20n_53_02_2_2_coast_tide_thre50_v1.0.dbf
        file_name = os.path.basename(name)
        # 子文件名称
        folder_name = file_path.split('/')[1]
        print(file_path, file_name)
        print(folder_name)
