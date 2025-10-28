import requests
from tqdm import tqdm
import os

os.environ['HTTP_PROXY'] = 'http://127.0.0.1:4780'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:4780'


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
    url = 'https://download2391.mediafire.com/pwotrxid1fwgZWmSbVO-ta6Q_FX83OqYECkCnkf06qgCj6z3bcr3AQVM5HS-dzDgIRI63IQuef7vFZEUc7gdA1ERg7uH1T0XGiUXVtB6vuA31UBtDEr_plB0Mguq2uS8Fs0eF6AZ0Loo_8JphTygqcl44Fnh7OpWlFefWgHZ1eEKNQ/dr030ut2e7uqwkh/ChatTTS-UI-0.84.rar'

    filename = r'E:\ChatTTS\ChatTTS-UI-0.84.rar'
    download_file(url, filename)


if __name__ == '__main__':
    main()

