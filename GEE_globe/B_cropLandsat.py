# -*- coding:utf-8 -*-
"""
加载并处理地理空间数据：
    加载一个包含地理边界的 FeatureCollection。
    确认边界数据集中有特征存在。
处理 Landsat-8 图像数据：
    创建一个过滤后的 Landsat-8 图像集合，包括时间和地理范围的筛选。
    使用 QA_PIXEL 波段进行云遮蔽处理。
    计算图像集合的中值图像，并按边界裁剪。
导出处理后的图像数据：
    将处理后的中值图像导出到 Google Drive。

    对应波段['SR_B4', 'SR_B3', 'SR_B2', 'SR_B6']
"""

import ee
from datetime import datetime
import os
import time

# 设置网络代理（如有需要）
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:4780'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:4780'

# 设置代理超时时间（如有需要）
os.environ['http_proxy_timeout'] = '300'
os.environ['https_proxy_timeout'] = '300'

# 设置环境变量以解决 OpenSSL 3.0 的兼容性问题
os.environ['CRYPTOGRAPHY_OPENSSL_NO_LEGACY'] = '1'

# 授权并初始化 Earth Engine API
ee.Authenticate()
ee.Initialize(project='ee-nicexian0011')

def crop_image_landsat(boundary, year, output_path):
    """
    裁剪 Landsat 8 图像并导出到 Google Drive。

    参数:
    boundary (str): 资产的完整路径，如 'users/nicexian0011/_DGS_GSV_Grids/20367'
    year (int): 年份，用于过滤图像
    output_path (str): 导出到 Google Drive 的文件夹名称
    """
    img_boundary = boundary
    date_year = year
    img_folder = output_path
    img_name = img_boundary.split('/')[-1]

    try:
        # 加载用户的行政区划边界数据集
        adminBoundary = ee.FeatureCollection(img_boundary)

        # 检查边界数据集中是否有特征
        numFeatures = adminBoundary.size().getInfo()
        if numFeatures > 0:
            # 获取边界数据集的几何信息
            boundaryGeometry = adminBoundary.geometry()

            # 创建 Landsat 8 Level-2 反射率图像集合
            ls8ImageCollection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                .filterBounds(boundaryGeometry) \
                .filterDate(ee.Date.fromYMD(date_year, 1, 1), ee.Date.fromYMD(date_year + 1, 1, 1)) \
                .filter(ee.Filter.lte('CLOUD_COVER', 50)) \
                .sort('CLOUD_COVER')

            # 检查图像集合的大小
            numImages = ls8ImageCollection.size().getInfo()
            if numImages > 0:
                # 获取云量最少的影像
                ls8Image = ls8ImageCollection.first()

                # 定义一个函数来遮蔽 Landsat 8 图像中的云
                def mask_landsat8_clouds(image):
                    # 使用内置的 QA_PIXEL 波段来进行云掩膜
                    qa_band = image.select('QA_PIXEL')
                    cloud_mask = qa_band.bitwiseAnd(1 << 5).eq(0) \
                        .And(qa_band.bitwiseAnd(1 << 3).eq(0)) \
                        .And(qa_band.bitwiseAnd(1 << 4).eq(0))
                    return image.updateMask(cloud_mask).divide(10000)

                # 应用云掩膜
                masked_ls8 = mask_landsat8_clouds(ls8Image)

                # 计算图像集合的中值图像，并按边界裁剪
                clippedMedian = masked_ls8.clip(boundaryGeometry)

                # 确保提取指定的波段
                clippedMedian = clippedMedian.select(['SR_B4', 'SR_B3', 'SR_B2', 'SR_B6'])

                # 导出裁剪后的中值图像到 Google Drive
                outputDescription = img_name
                task = ee.batch.Export.image.toDrive(
                    image=clippedMedian,
                    folder=img_folder,
                    fileNamePrefix=outputDescription,
                    region=boundaryGeometry.getInfo()['coordinates'],
                    scale=30,
                    maxPixels=1e13,
                    description=f'Download Landsat 8 image {outputDescription}'  # 使用定义的任务名称
                )
                task.start()
                print(f'Task started: {outputDescription}')

                # 可选：监控任务状态
                while task.active():
                    print('Task is running...')
                    time.sleep(30)  # 每30秒检查一次
                print(f'Task completed with status: {task.status()}')
            else:
                print(f'No Landsat 8 images found for boundary: {img_boundary}')
        else:
            print('FeatureCollection is empty.')
    except ee.EEException as e:
        print(f'Error processing boundary {img_boundary}: {e}')

def list_assets_in_folder(folder_path):
    """
    列出指定文件夹下的所有资产名称，包括子文件夹中的资产。

    参数:
    folder_path (str): 文件夹路径，如 'users/nicexian0011/_DGS_GSV_Grids'

    返回:
    list: 包含指定文件夹下所有资产名称的列表。
    """
    assets = []

    def _list_assets_recursive(prefix):
        try:
            response = ee.data.listAssets({'parent': prefix})
            for asset in response.get('assets', []):
                asset_name = asset['name']
                assets.append(asset_name)
                # 如果资产是文件夹，则递归列出其内容
                if asset['type'] == 'FOLDER':
                    _list_assets_recursive(asset_name + '/')
        except ee.EEException as e:
            print(f"Error listing assets in {prefix}: {e}")

    _list_assets_recursive(folder_path)
    return assets

def main():
    # 指定文件夹路径
    folder_path = 'users/nicexian0011/_DGS_GSV_Grids'
    # 获取文件夹下的所有资产名称
    asset_names = list_assets_in_folder(folder_path)
    # 需要处理的资产列表
    aim_list = ['20367']

    for asset_name in asset_names:
        # asset_name 格式如 'users/nicexian0011/_DGS_GSV_Grids/20367'
        uid = asset_name.split('/')[-1]

        if uid in aim_list:
            # 直接传递完整的资产路径
            island_boundary = asset_name
            start_year = 2023  # 修改为你需要的年份
            gee_output_path = "_DGS_GSV_Landsat"
            crop_image_landsat(boundary=island_boundary, year=start_year, output_path=gee_output_path)


if __name__ == '__main__':
    main()
