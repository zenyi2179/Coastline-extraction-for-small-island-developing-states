# -*- coding:utf-8 -*-
"""
加载并处理地理空间数据：
    加载一个包含地理边界的 FeatureCollection。
    确认边界数据集中有特征存在。
处理 Sentinel-2 图像数据：
    创建一个过滤后的 Sentinel-2 图像集合，包括时间和地理范围的筛选。
    使用 QA60 波段进行云遮蔽处理。
    计算图像集合的中值图像，并按边界裁剪。
导出处理后的图像数据：
    将处理后的中值图像导出到 Google Drive。

作者：23242
日期：2024年09月10日
"""

import ee
from datetime import datetime
import os

# 设置网络代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:4780'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:4780'

# 设置代理超时时间
os.environ['http_proxy_timeout'] = '300'
os.environ['https_proxy_timeout'] = '300'

# 设置环境变量以解决 OpenSSL 3.0 的兼容性问题
os.environ['CRYPTOGRAPHY_OPENSSL_NO_LEGACY'] = '1'

# 授权并初始化 Earth Engine API
ee.Authenticate()
ee.Initialize(project='ee-nicexian0011')

def calculate_band_ratio(boundary, year, output_path):
    # 初始化要素
    img_boundary = boundary
    date_year = year
    img_folder = output_path
    img_name = img_boundary.split('/')[-1]

    # 加载用户的行政区划边界数据集
    adminBoundary = ee.FeatureCollection(img_boundary)

    # 检查边界数据集中是否有特征
    numFeatures = adminBoundary.size().getInfo()
    if numFeatures > 0:
        # 获取边界数据集的几何信息
        boundaryGeometry = adminBoundary.geometry()

        # 创建 Landsat 8 TOA 反射率图像集合
        ls8Images = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
            .filterBounds(boundaryGeometry) \
            .filterDate(ee.Date.fromYMD(date_year, 1, 1), ee.Date.fromYMD(date_year + 1, 1, 1)) \
            .filter(ee.Filter.lte('CLOUD_COVER', 20))

        # 检查图像集合的大小
        numImages = ls8Images.size().getInfo()
        if numImages > 0:
            # 定义一个函数来遮蔽 Landsat 8 图像中的云
            def mask_landsat8_clouds(image):
                # 使用内置的 QA 波段来进行云掩膜
                qa_band = image.select('QA_PIXEL')
                cloud_mask = qa_band.bitwiseAnd(1 << 5).eq(0) \
                    .And(qa_band.bitwiseAnd(1 << 3).eq(0)) \
                    .And(qa_band.bitwiseAnd(1 << 4).eq(0))
                return image.updateMask(cloud_mask).divide(10000)

            # 映射函数至图像集合
            ls8Images = ls8Images.map(mask_landsat8_clouds)

            # 计算图像集合的中值图像，并按边界裁剪
            clippedMedian = ls8Images.median().clip(boundaryGeometry)

            # 计算比值 (SR_B3 - SR_B6) / (SR_B3 + SR_B6)
            ratioImage = clippedMedian.normalizedDifference(['SR_B3', 'SR_B6']).rename('BandRatio')

            # 导出裁剪后的比值图像到 Google Drive
            outputDescription = img_name + '_BandRatio'
            task = ee.batch.Export.image.toDrive(
                image=ratioImage,
                folder=img_folder,
                fileNamePrefix=outputDescription,
                region=boundaryGeometry,
                scale=30,
                maxPixels=1e13,
                description=fr'Download Band Ratio image {outputDescription}'  # 使用定义的任务名称
            )
            task.start()
            print(f'Task started: {outputDescription}')
        else:
            print('No images found in the specified date range and cloud cover criteria.')
    else:
        print('The FeatureCollection is empty.')


def list_assets_in_folder(folder_path):
    """
    列出指定文件夹下的所有资产名称。

    参数:
    folder_path (str): 文件夹路径。

    返回:
    list: 包含指定文件夹下所有资产名称的列表。
    """
    assets = []

    def _list_assets(prefix):
        try:
            response = ee.data.listAssets({
                'parent': prefix
            })

            for asset in response['assets']:
                asset_name = asset['name']
                assets.append(asset_name)

                # 递归处理子文件夹
                if 'assets' in asset and len(asset['assets']) > 0:
                    _list_assets(asset_name + '/')

        except ee.EEException as e:
            print(f"Error listing assets: {e}")

    _list_assets(folder_path)

    return assets


def main():
    '''
    # 指定文件夹路径
    folder_path = 'users/nicexian0011/islands/'
    # 获取文件夹下的所有资产名称
    asset_names = list_assets_in_folder(folder_path)

    for asset_name in asset_names:
        # 'projects/earthengine-legacy/assets/users/nicexian0011/islands/ISID_1005'
        island_boundary = asset_name.split(fr'assets/')[-1]
        start_year = 2020
        gee_output_path = fr"LandsatMNDWI"
        crop_image_landsat(boundary=island_boundary, year=start_year, output_path=gee_output_path)
    '''

    island_boundary = fr"users/nicexian0011/islands/ISID_224209"
    start_year = 2020
    gee_output_path = fr"LandsatMNDWI"
    calculate_band_ratio(boundary=island_boundary, year=start_year, output_path=gee_output_path)


if __name__ == '__main__':
    main()