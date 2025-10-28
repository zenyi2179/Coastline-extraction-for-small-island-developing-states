# -*- coding: utf-8 -*-
"""
从 txt 文件中解析出 'earthdem/' 开头、指定后缀（.shp, .shx, .dbf）的文件名称
作者：朱昱
日期：2025-06-17
"""

import os
import requests
from tqdm import tqdm

os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7897'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7897'


def download_file(url, filename):
    """
    从指定的URL下载文件，并显示下载进度条。

    :param url: 文件的URL地址
    :param filename: 下载文件保存的路径和文件名
    """
    # 检查文件是否存在，如果存在则获取文件大小
    if os.path.exists(filename):
        file_size = os.path.getsize(filename)
    else:
        file_size = 0

    # 发送HTTP请求，设置Range头部以支持断点续传
    headers = {'Range': 'bytes=%d-' % file_size}
    response = requests.get(url, stream=True, headers=headers, timeout=6000)

    # 获取文件总大小
    total_size = int(response.headers.get('content-length', 0)) + file_size

    # 使用tqdm显示下载进度条
    progress_bar = tqdm(total=total_size, initial=file_size, unit='B', unit_scale=True, desc=filename)

    # 以二进制方式写入文件
    with open(filename, 'ab') as file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)
                progress_bar.update(len(chunk))

    # 关闭进度条
    progress_bar.close()


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
    for name in file_names:
        # 文件路径 earthdem/earthdem_02_southeast_canada/utm20n_53_02_2_2/output/utm20n_53_02_2_2_coast_tide_thre50_v1.0.dbf
        file_path = name
        # 文件名称 utm20n_53_02_2_2_coast_tide_thre50_v1.0.dbf
        file_name = os.path.basename(name)
        # 子文件名称
        folder_name = file_path.split('/')[1]

        # 下载文件示例
        # https://arcticdata.io/data/10.18739/A2610VT7V/earthdem/earthdem_05_mexico_and_caribbean/utm11n_32_03_2_1/output/utm11n_32_03_2_1_coast_tide_thre50_v1.0.shp
        url_ex = fr'https://arcticdata.io/data/10.18739/A2610VT7V/'
        url_final = url_ex + file_path

        output_folder = os.path.join(fr'E:\ArcData\Arcticdata', folder_name)
        os.makedirs(output_folder, exist_ok=True)
        output_filename = os.path.join(output_folder, file_name)
        if os.path.exists(output_filename):
            print(output_filename, fr"已存在")
        else:
            download_file(
                url=url_final,
                filename=output_filename
            )
