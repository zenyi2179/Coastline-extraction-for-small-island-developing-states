import ee
from datetime import datetime
import os

os.environ['HTTP_PROXY'] = 'http://127.0.0.1:4780'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:4780'

# 设置环境变量以解决 OpenSSL 3.0 的兼容性问题
os.environ['CRYPTOGRAPHY_OPENSSL_NO_LEGACY'] = '1'

# 授权 Earth Engine 账户
ee.Authenticate()

# 初始化 Earth Engine API
ee.Initialize(project='ee-nicexian0011')

# 加载用户的行政区划边界数据集
adminBoundary = ee.FeatureCollection("projects/ee-nicexian0011/assets/test")

# 检查边界数据集中是否有特征
numFeatures = adminBoundary.size().getInfo()
if numFeatures > 0:
    print(f'Number of features in the FeatureCollection: {numFeatures}')

    # 获取边界数据集的几何信息
    boundaryGeometry = adminBoundary.geometry()

    # 创建 Sentinel-2 TOA 反射率图像集合
    s2Images = ee.ImageCollection('COPERNICUS/S2_HARMONIZED') \
                .filterBounds(adminBoundary) \
                .filterDate(datetime(2016, 1, 1), datetime(2017, 1, 1)) \
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
    outputDescription = 'Sentinel2_image2'
    task = ee.batch.Export.image.toDrive(
        image=clippedMedian,
        description=outputDescription,
        folder='GEE_exports',
        fileNamePrefix=outputDescription,
        region=adminBoundary.geometry(),
        scale=10,
        maxPixels=1e13
    )
    task.start()
    print(f'Task started: {outputDescription}')
else:
    print('The FeatureCollection is empty.')