# -*- coding:utf-8 -*-
"""
此代码的主要用途是批量删除 Google Earth Engine (GEE) 资产存储中的指定文件夹及其所有内容。
递归删除指定文件夹中的所有资产（包括子文件夹和文件），并最终删除目标文件夹本身。

作者：23242
日期：2024年09月10日
"""

import ee
import os
import time

# 设置网络代理（如有需要）
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:4780'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:4780'

# 设置环境变量以解决 OpenSSL 3.0 的兼容性问题
os.environ['CRYPTOGRAPHY_OPENSSL_NO_LEGACY'] = '1'

# 授权并初始化 Earth Engine API
ee.Authenticate()
ee.Initialize(project='ee-nicexian0011')


def delete_asset_folder(delete_path):
    """
    递归删除指定的资产文件夹及其所有内容。

    参数:
    delete_path (str): 要删除的文件夹路径，例如 'users/nicexian0011/_DGS_GSV_Grids'
    """
    try:
        print(f"正在处理删除路径: {delete_path}")

        # 获取该文件夹下的所有资产
        assets = ee.data.getList({'id': delete_path})
        for asset in assets:
            asset_id = asset['id']
            asset_type = asset['type']
            if asset_type == 'FOLDER':
                # 递归删除子文件夹
                delete_asset_folder(asset_id)
            else:
                # 删除文件资产
                ee.data.deleteAsset(asset_id)
                print(f"已删除资产: {asset_id}")

            # 为避免触发速率限制，添加短暂延时
            time.sleep(1)

        # 删除空文件夹
        ee.data.deleteAsset(delete_path)
        print(f"已删除文件夹: {delete_path}")

    except ee.EEException as e:
        if "not found" in str(e):
            print(f"资产 {delete_path} 不存在，无需删除。")
        else:
            print(f"删除资产 {delete_path} 时出错: {e}")
            raise  # 重新抛出异常以便进一步处理或终止脚本


def main():
    """
    主函数，删除指定的 GEE 资产文件夹及其所有内容。
    """
    # 要删除的文件夹路径（确保不以斜杠结尾）
    folder_delete_path = 'users/nicexian0011/_DGS_GSV_Grids'

    # 调用删除函数
    delete_asset_folder(folder_delete_path)


if __name__ == '__main__':
    main()
