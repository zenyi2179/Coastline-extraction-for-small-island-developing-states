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

def crop_image_sentinel(boundary, year, output_path):
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
        # print(f'Number of features in the FeatureCollection: {numFeatures}')

        # 获取边界数据集的几何信息
        boundaryGeometry = adminBoundary.geometry()

        # 创建 Sentinel-2 TOA 反射率图像集合
        s2Images = ee.ImageCollection('COPERNICUS/S2_HARMONIZED') \
            .filterBounds(boundaryGeometry) \
            .filterDate(datetime(date_year, 1, 1), datetime(date_year+1, 1, 1)) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))

        # 定义一个函数来遮蔽 Sentinel-2 图像中的云
        def mask_clouds(image):
            qa_band = image.select('QA60')
            cloud_mask = qa_band.bitwiseAnd(1 << 10).eq(0).And(qa_band.bitwiseAnd(1 << 11).eq(0))
            return image.updateMask(cloud_mask).divide(10000)

        # 映射函数至图像集合
        s2Images = s2Images.map(mask_clouds)

        # 计算图像集合的中值图像，并按边界裁剪
        clippedMedian = s2Images.median().clip(adminBoundary)

        # 确保波段顺序正确
        clippedMedian = clippedMedian.select(['B4', 'B3', 'B2'])

        # 导出裁剪后的中值图像到 Google Drive
        outputDescription = img_name
        task = ee.batch.Export.image.toDrive(
            image=clippedMedian,
            folder=img_folder,
            fileNamePrefix=outputDescription,
            region=adminBoundary.geometry(),
            scale=10,
            maxPixels=1e13
        )
        task.start()
        # print(f'Task started: {outputDescription}')
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
    # 指定文件夹路径
    folder_path = 'users/nicexian0011/islands/'
    # 获取文件夹下的所有资产名称
    asset_names = list_assets_in_folder(folder_path)

    for asset_name in asset_names:
        print(asset_name) # 'projects/earthengine-legacy/assets/users/nicexian0011/islands/ISID_1005'
        # island_boundary = fr"users/nicexian0011/islands/ISID_1005"
        island_boundary = asset_name.split(fr'assets/')[-1]
        start_year = 2016
        gee_output_path = fr"GEE_Islands"
        crop_image_sentinel(boundary=island_boundary, year=start_year, output_path=gee_output_path)


if __name__ == '__main__':
    main()