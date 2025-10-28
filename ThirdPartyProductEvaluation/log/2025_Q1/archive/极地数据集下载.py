# -*- coding:utf-8 -*-
"""
https://www.nature.com/articles/s41597-025-05180-9
A global high resolution coastline database from satellite imagery
数据集
https://arcticdata.io/data/10.18739/A2610VT7V/
"""
import requests
from tqdm import tqdm
import os

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
    response = requests.get(url, stream=True, headers=headers)

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


def main():
    # 下载文件示例
    url = 'https://arcticdata.io/data/10.18739/A2610VT7V/filelist.txt'
    filename = r'E:\ArcData\Arcticdata\filelist.txt'
    download_file(url, filename)


if __name__ == '__main__':
    main()
