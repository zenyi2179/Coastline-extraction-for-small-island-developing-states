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
from itertools import islice

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
        ee.data.getAsset(asset_path)
        ee.data.deleteAsset(asset_path)
        print(f"Asset {asset_path} 已删除。")
    except ee.EEException as e:
        if "not found" in str(e):
            # Asset 不存在，无需删除
            pass
        else:
            print(f"删除资产 {asset_path} 时出错: {e}")
            raise


def get_files_with_extension(directory, extension):
    """
    获取指定文件夹中具有特定扩展名的所有文件名。

    参数:
    directory (str): 文件夹路径。
    extension (str): 文件扩展名（包括点，例如 '.geojson'）。

    返回:
    list: 包含指定扩展名文件名的列表。
    """
    # 确保路径字符串是正确的格式
    directory = os.path.normpath(directory)

    # 获取文件夹中的所有文件
    try:
        all_files = os.listdir(directory)
    except FileNotFoundError:
        print(f"文件夹路径不存在: {directory}")
        return []

    # 筛选出指定扩展名的文件
    files_with_extension = [file for file in all_files if file.endswith(extension)]

    # 返回结果
    return files_with_extension


def batch(iterable, n=1):
    """
    将可迭代对象分割成长度为 n 的块。

    参数:
    iterable (iterable): 要分割的可迭代对象。
    n (int): 每个批次的大小。

    返回:
    generator: 分批次的生成器。
    """
    it = iter(iterable)
    while True:
        batch = list(islice(it, n))
        if not batch:
            break
        yield batch


def upload_geojson_to_asset(json_file, json_folder_path, output_folder):
    """
    上传单个 GeoJSON 文件到 GEE 资产存储。

    参数:
    json_file (str): GeoJSON 文件名。
    json_folder_path (str): 本地 GeoJSON 文件夹路径。
    output_folder (str): 目标 GEE 资产文件夹路径。
    """
    json_name = json_file.split('.')[0]
    local_geojson_path = os.path.join(json_folder_path, json_file)

    # 读取 GeoJSON 文件
    try:
        with open(local_geojson_path, 'r', encoding='utf-8') as file:
            geojson_data = json.load(file)
    except FileNotFoundError:
        print(f"GeoJSON 文件未找到: {local_geojson_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"GeoJSON 文件解析错误: {local_geojson_path} - {e}")
        return None

    # 将 GeoJSON 数据转换为 GEE 的 FeatureCollection
    try:
        feature_collection = ee.FeatureCollection([
            ee.Feature(
                ee.Geometry(geojson_feature['geometry']),
                {**geojson_feature.get('properties', {}), 'system:index': str(index)}
            )
            for index, geojson_feature in enumerate(geojson_data.get('features', []))
        ])
    except Exception as e:
        print(f"转换 GeoJSON 数据为 FeatureCollection 时出错: {local_geojson_path} - {e}")
        return None

    # 指定上传到 GEE 资产的路径
    asset_path = fr'users/nicexian0011/{output_folder}/{json_name}'

    # 检查并删除资产，如果存在的话
    delete_asset_if_exists(asset_path)

    try:
        # 创建上传任务
        task = ee.batch.Export.table.toAsset(
            collection=feature_collection,
            description=f'Upload_geojson_to_asset_{json_name}',
            assetId=asset_path,
            fileFormat='GeoJSON'
        )

        # 开始上传任务
        task.start()
        print(f"上传任务已启动: {json_file}。")

        return task

    except Exception as e:
        print(f'上传 {json_file} 时出错: {e}')
        return None


def monitor_tasks(tasks):
    """
    监控一组任务，直到所有任务完成。

    参数:
    tasks (list): 要监控的任务列表。
    """
    while tasks:
        for task in tasks[:]:
            status = task.status()
            state = status.get('state')
            if state in ['COMPLETED', 'FAILED', 'CANCELLED']:
                try:
                    description = task.config['description']
                except KeyError:
                    description = 'No description'
                if state == 'COMPLETED':
                    print(f"任务完成: {description}")
                else:
                    print(f"任务 {state}: {description}")
                tasks.remove(task)
        if tasks:
            # print(f"等待 {len(tasks)} 个任务完成...")
            time.sleep(30)  # 每30秒检查一次


def format_time(seconds):
    """
    格式化时间（秒）为 HH:MM:SS 格式。

    参数:
    seconds (float): 时间，单位为秒。

    返回:
    str: 格式化后的时间字符串。
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)

    return f"{hours:02}:{minutes:02}:{seconds:02}"


def main():
    """
    主函数，用于批量上传 GeoJSON 文件到 Google Earth Engine (GEE) 资产存储。
    """
    # 记录开始时间
    start_time = time.time()

    # 指定 GeoJSON 文件夹路径
    json_folder_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\b_Global_Island_Grid\_DGS_GSV_Geojson"
    json_files = get_files_with_extension(directory=json_folder_path, extension='.geojson')

    if not json_files:
        print("没有找到 GeoJSON 文件。")
        return

    # 目标 GEE 资产文件夹
    output_folder = "_DGS_GSV_Grids"
    # output_folder = "islands"

    # 分批次处理，每批次最多3个文件
    batch_size = 3
    for batch_files in batch(json_files, batch_size):
        tasks = []
        for json_file in batch_files:
            task = upload_geojson_to_asset(json_file, json_folder_path, output_folder)
            if task:
                tasks.append(task)
        # 监控当前批次的任务
        monitor_tasks(tasks)

    # 记录结束时间
    end_time = time.time()
    # 计算程序运行时间
    formatted_time = format_time(end_time - start_time)
    print(f"所有任务已完成，运行时间: {formatted_time}")


if __name__ == '__main__':
    main()
