# -*- coding:utf-8 -*-
"""
此代码的主要用途是批量上传本地 GeoJSON 文件到 Google Earth Engine (GEE) 资产存储。
将多个本地 GeoJSON 文件上传到 GEE 资产存储，并确保每次上传前都清除了同名的已有资产。

作者：23242
日期：2024年09月10日
"""

import ee
import os
import json
import time

# 构建网络代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:4780'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:4780'

# 设置环境变量以解决 OpenSSL 3.0 的兼容性问题
os.environ['CRYPTOGRAPHY_OPENSSL_NO_LEGACY'] = '1'

# 授权 Earth Engine 账户及初始化 Earth Engine API
ee.Authenticate()
ee.Initialize(project='ee-nicexian0011')


def delete_asset_if_exists(asset_path):
    """
    检查并删除指定的资产路径，如果存在的话。

    参数:
    asset_path (str): 资产路径。
    """
    try:
        asset = ee.data.getAsset(asset_path)
        ee.data.deleteAsset(asset_path)
        # print(f"Asset {asset_path} has been deleted.")
        pass
    except ee.EEException as e:
        if "not found" in str(e):
            # print(f"Asset {asset_path} does not exist.")
            pass
        else:
            raise


def get_files_with_extension(directory, extension):
    """
    获取指定文件夹中具有特定扩展名的所有文件名。

    参数:
    directory (str): 文件夹路径。
    extension (str): 文件扩展名（包括点，例如 '.shp'）。

    返回:
    list: 包含指定扩展名文件名的列表。
    """
    # 确保路径字符串是正确的格式
    directory = os.path.normpath(directory)

    # 获取文件夹中的所有文件
    all_files = os.listdir(directory)

    # 筛选出指定扩展名的文件
    files_with_extension = [file for file in all_files if file.endswith(extension)]

    # 返回结果
    return files_with_extension


def main():
    """
    主函数，用于批量上传 GeoJSON 文件到 Google Earth Engine (GEE) 资产存储。
    """
    # 确定裁剪的图像边界范围
    json_folder_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\b_continent_si_buffer\Africa_si_buffer_geojson'
    json_files = get_files_with_extension(directory=json_folder_path, extension='.geojson')

    for json_file in json_files:
        temp_name = json_file.split('_')[-1]
        json_name = temp_name.split('.')[0]

        local_geojson_path = os.path.join(json_folder_path, json_file)

        # 读取 GeoJSON 文件
        with open(local_geojson_path, 'r') as file:
            geojson_data = json.load(file)

        # 将 GeoJSON 数据转换为 GEE 的 FeatureCollection
        feature_collection = ee.FeatureCollection([
            ee.Feature(
                ee.Geometry(geojson_feature['geometry']),
                {**geojson_feature['properties'], 'system:index': str(index)}
            )
            for index, geojson_feature in enumerate(geojson_data['features'])
        ])

        # 指定上传到 GEE 资产的路径
        asset_path = fr'users/nicexian0011/Africa_si_buffer/UID_{json_name}'

        # 检查并删除资产，如果存在的话
        delete_asset_if_exists(asset_path)

        # 创建上传任务
        task = ee.batch.Export.table.toAsset(
            collection=feature_collection,
            description=fr'Upload_geojson_to_asset_{json_name}',
            assetId=asset_path,
            fileFormat='GeoJSON'
        )

        # 开始上传任务
        task.start()
        print(f"Upload task started for {json_file}.")

        # 等待任务完成
        while True:
            if not task.active():
                print("Task completed.")
                break
            else:
                # print("Task status:", task.status())
                time.sleep(1)


if __name__ == '__main__':
    main()