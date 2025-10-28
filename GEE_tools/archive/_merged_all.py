
# ====== Authenticate.py ======
import ee

try:
    ee.Initialize()
except ee.EEException:
    ee.Authenticate()
    ee.Initialize()

# ====== _DriveSharedFolders.py ======
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

# ====== _Otsu.py ======
import numpy as np
import cv2
from osgeo import gdal, gdal_array

def otsu_threshold_with_gdal(input_tif_path, output_tif_path):
    # 打开TIFF文件
    dataset = gdal.Open(input_tif_path, gdal.GA_ReadOnly)
    if dataset is None:
        raise IOError(f"Could not open file: {input_tif_path}")

    # 获取图像的地理信息
    geo_transform = dataset.GetGeoTransform()
    projection = dataset.GetProjection()

    # 读取单波段图像数据
    band = dataset.GetRasterBand(1)
    data = band.ReadAsArray()

    # 确保数据类型为无符号整型
    data = np.abs(data).astype(np.uint8)

    # 使用Otsu方法计算最佳阈值
    ret, binary_image = cv2.threshold(data, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 创建输出文件
    driver = gdal.GetDriverByName('GTiff')
    out_dataset = driver.Create(output_tif_path, binary_image.shape[1], binary_image.shape[0], 1, gdal.GDT_Byte)
    out_dataset.SetGeoTransform(geo_transform)
    out_dataset.SetProjection(projection)

    # 写入二值化后的图像
    out_band = out_dataset.GetRasterBand(1)
    out_band.WriteArray(binary_image)
    out_band.FlushCache()  # 刷新缓存到磁盘

    # 设置输出图像的无效值
    out_band.SetNoDataValue(0)

    # 关闭数据集
    out_dataset = None
    dataset = None

    print(f'Otsu thresholded image saved to: {output_tif_path}')

def main():
    # 输入和输出路径
    input_tif_path = fr'C:\Users\23042\Desktop\test\43E13Sru_ls578_Index.tif'
    output_tif_path = fr'C:\Users\23042\Desktop\test\43E13Sru_ls578_Index_otsu.tif'

    # 应用Otsu方法并保存结果
    otsu_threshold_with_gdal(input_tif_path, output_tif_path)

if __name__ == '__main__':
    main()

# ====== _PCA.py ======
import rasterio
import numpy as np
from sklearn.decomposition import PCA

"""主成分分析"""

# 设置输入输出文件路径
input_path = 'E:\\_OrderingProject\\F_IslandsBoundaryChange\\a_ArcData\\GEE_valid\\ISID_224209_zoom.tif'
output_path = 'E:\\_OrderingProject\\F_IslandsBoundaryChange\\a_ArcData\\GEE_valid\\ISID_224209_zoom_PCA.tif'

# 打开输入的图像文件
with rasterio.open(input_path) as src:
    # 读取两个波段的数据
    band1 = src.read(1)  # 波段1
    band2 = src.read(2)  # 波段2

    # 将波段数据展平并组合成二维数组（像素点数 x 波段数）
    image_stack = np.dstack((band1, band2))
    rows, cols, bands = image_stack.shape
    image_reshaped = image_stack.reshape(rows * cols, bands)

    # 处理 NaN 值，替换为0或者图像的平均值
    image_reshaped = np.nan_to_num(image_reshaped, nan=np.nanmean(image_reshaped))

    # 执行主成分分析 (PCA)
    pca = PCA(n_components=2)  # 保留2个主成分
    pca_result = pca.fit_transform(image_reshaped)

    # 将结果重新变回图像的形状
    pca_band1 = pca_result[:, 0].reshape(rows, cols)
    pca_band2 = pca_result[:, 1].reshape(rows, cols)

    # 保存PCA结果
    with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=rows,
            width=cols,
            count=2,  # 两个主成分
            dtype=rasterio.float32,
            crs=src.crs,
            transform=src.transform
    ) as dst:
        dst.write(pca_band1, 1)  # 保存主成分1
        dst.write(pca_band2, 2)  # 保存主成分2

print(f"PCA result saved at {output_path}")


# ====== _clearingTasks.py ======
# -*- coding:utf-8 -*-
"""
作者：23242
日期：2024年09月10日
"""
import os
import ee
import time

# 构架网络代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:4780'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:4780'
# 设置环境变量以解决 OpenSSL 3.0 的兼容性问题
os.environ['CRYPTOGRAPHY_OPENSSL_NO_LEGACY'] = '1'
# 授权 Earth Engine 账户及Earth Engine API
ee.Authenticate()
ee.Initialize(project='ee-nicexian0011')

def cancel_active_tasks():
    """
    取消所有正在运行的任务。
    """
    tasks = ee.batch.Task.list()
    for task in tasks:
        status = task.status()
        if status['state'] in ['READY', 'RUNNING']:
            task.cancel()
            print(f"Cancelled task {status['description']} with state {status['state']}.")

def delete_completed_tasks():
    """
    删除所有已完成的任务。
    """
    tasks = ee.batch.Task.list()
    for task in tasks:
        status = task.status()
        if status['state'] in ['COMPLETED', 'FAILED', 'CANCELLED']:
            task_id = status['id']
            ee.data.deleteTask(task_id)
            print(f"Deleted task {status['description']} with state {status['state']}.")

def clear_tasks():
    """
    清除所有任务，包括取消正在运行的任务和删除已完成的任务。
    """
    cancel_active_tasks()
    delete_completed_tasks()

def main():
    # 清除任务列表
    clear_tasks()

if __name__ == '__main__':
    main()

# ====== _draft.py ======
import geopandas as gpd
from shapely.geometry import LineString

# pip install --upgrade fiona geopandas
#    D:\ArcGISPro3\Pro\bin\Python\envs\arcgispro-py3\python.exe -m pip install --upgrade fiona geopandas -i https://pypi.doubanio.com/simple/

# Requirement already satisfied: fiona in c:\users\23242\appdata\roaming\python\python39\site-packages (1.10.1)
# Requirement already satisfied: geopandas in d:\arcgispro3\pro\bin\python\envs\arcgispro-py3\lib\site-packages (0.12.2)

import geopandas as gpd
from shapely.geometry import LineString, MultiLineString

# 定义函数用于输出组件的首尾点，并封闭线段
def process_multilinestring(geometry):
    if isinstance(geometry, MultiLineString):
        for i, component in enumerate(geometry.geoms):  # 使用 .geoms 来迭代 MultiLineString 中的每个 LineString
            coords = list(component.coords)
            start_point = coords[0]
            end_point = coords[-1]
            # # 输出每个组件的首尾点
            # print(f"Component {i + 1}:")
            # print(f"  Start Point (Index: 0): Longitude: {start_point[0]}, Latitude: {start_point[1]}")
            # print(f"  End Point (Index: {len(coords) - 1}): Longitude: {end_point[0]}, Latitude: {end_point[1]}")
            # print('-' * 50)

            # 检查首尾点是否一致，不一致则封闭
            if start_point != end_point:
                # print(f"  Closing Component {i + 1}...")
                coords.append(start_point)  # 封闭
            # else:
            #     print(f"  Component {i + 1} is already closed.")
            # print('-' * 50)
            # 返回封闭后的 LineString
            yield LineString(coords)
    else:
        print("Geometry is not MultiLineString.")
        return None

def fix_subpixel_extraction(input_geojson, output_geojson):
    # 读取 GeoJSON 文件
    # input_geojson = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\k_subPixelWaterlineExtraction\UID_114940_subpixel.geojson"
    gdf = gpd.read_file(input_geojson)

    # 处理所有要素的几何
    for idx, row in gdf.iterrows():
        geometry = row['geometry']
        # print(f"Processing Feature {idx + 1}...")
        if isinstance(geometry, MultiLineString):
            closed_components = list(process_multilinestring(geometry))  # 封闭每个组件
            # 创建封闭后的 MultiLineString 几何
            closed_multilinestring = MultiLineString(closed_components)
            gdf.at[idx, 'geometry'] = closed_multilinestring  # 更新封闭后的几何
        else:
            print(f"Feature {idx + 1} is not a MultiLineString.")

    # 输出结果
    # output_geojson = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\k_subPixelWaterlineExtraction\UID_114940_subpixel_closed.geojson"
    gdf.to_file(output_geojson, driver="GeoJSON")
    print(f"Subpixel_closed MultiLineString output: {output_geojson}")

if __name__ == "__main__":
    fix_subpixel_extraction(input_geojson=r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\k_subPixelWaterlineExtraction\UID_114940_subpixel.geojson",
                            output_geojson=r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\k_subPixelWaterlineExtraction\UID_114940_subpixel_closed.geojson")


# ====== _draft2.py ======
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

# ====== _main.py ======
# -*- coding:utf-8 -*-
"""
作者：23242
日期：2024年09月18日
"""
from h_bandInterpolation import downscaling_by_interpolation
from i_cadulateMNDWI import calculate_band_ratio
from j_distinguishRange import extract_by_mask
# from k_subPixelWaterlineExtraction import subpixel_extraction
from k_v2 import subpixel_extraction
# from l_buildShapeFeature import geojson_to_polygon
from l_v2 import geojson_to_polygon
from m_caculateFields import caculate_area_length
import os

def main():
    # 初始 Landsat 8 tif
    # input_tif_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE_valid\ISID_224209.tif'
    # input_tif_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\c_YY_2020\Africa\UID_130247.tif'

    # 指定的文件夹路径
    folder_path = r'E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\c_YY_2015\temp'

    # 使用os.listdir()来获取文件夹中的所有文件名和子目录名
    entries = os.listdir(folder_path)

    # 打印所有的条目
    for entry in entries:
        input_tif_path = os.path.join(folder_path, entry)
        print(input_tif_path)

        # uid 选择
        uid_is_temp = input_tif_path.split('\\')[-1]
        uid_is_temp2 = uid_is_temp.split('_')[-1]
        uid_is = uid_is_temp2.split('.')[0]
        print(uid_is)

        # 利用插值法降尺度全色（PAN）波段
        zoom_tif = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\h_bandInterpolation\UID_{uid_is}_zoom.tif'
        downscaling_by_interpolation(origin_tif=input_tif_path, zoom_tif=zoom_tif, zoom_ratio=3)

        # 计算水分指数：MNDWI 水体指数（使用 Landsat 的绿色和短波红外 (SWIR) 1 波段）4-SR6 2-SR3
        MNDWI_tif = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\i_cadulateMNDWI\UID_{uid_is}_ND.tif'
        calculate_band_ratio(input_path=zoom_tif, output_path=MNDWI_tif, band1=2, band2=4)

        # 裁剪有效范围
        mask_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\SmallIslands_con_buffer.gdb\Africa_buffer"
        valid_tif = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\j_distinguishRange\UID_{uid_is}_extract.tif"
        extract_by_mask(origin_tif=MNDWI_tif, mask=mask_shp, identifier=uid_is, output_tif=valid_tif)

        # 亚像元边界提取
        subpixel_tif = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\k_subPixelWaterlineExtraction\UID_{uid_is}_subpixel.geojson"
        subpixel_extraction(input_tif=valid_tif, z_values=10.5, subpixel_tif=subpixel_tif)

        shp_mask = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\SmallIslands_continent.gdb\Africa"
        coast_line_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Landsat_output\YY_2015\Africa\UID_{uid_is}_after.shp"
        try:
            # 构建有效面要素
            geojson_to_polygon(extract_geojson=subpixel_tif, shp_mask=shp_mask, identifier=uid_is, tolerance=60, coast_line_shp=coast_line_shp)
            # 整理 shp 的字段及计算几何属性
            caculate_area_length(origin_fields_shp=coast_line_shp)
        except Exception as e:
            print(fr'geojson_to_polygon {uid_is} failed.')


if __name__ == "__main__":
    main()


# ====== _pca2.py ======
import rasterio
import numpy as np
from sklearn.decomposition import PCA

"""主成分分析"""

# 设置输入输出文件路径
input_path = 'E:\\_OrderingProject\\F_IslandsBoundaryChange\\a_ArcData\\GEE_valid\\ISID_224209_ND.tif'
output_path = 'E:\\_OrderingProject\\F_IslandsBoundaryChange\\a_ArcData\\GEE_valid\\ISID_224209_ND_PCA.tif'

# 打开输入的图像文件
with rasterio.open(input_path) as src:
    # 读取两个波段的数据
    band1 = src.read(1)  # 波段1
    band2 = src.read(2)  # 波段2

    # 将波段数据展平并组合成二维数组（像素点数 x 波段数）
    image_stack = np.dstack((band1, band2))
    rows, cols, bands = image_stack.shape
    image_reshaped = image_stack.reshape(rows * cols, bands)

    # 处理 NaN 值，替换为0或者图像的平均值
    image_reshaped = np.nan_to_num(image_reshaped, nan=np.nanmean(image_reshaped))

    # 执行主成分分析 (PCA)
    pca = PCA(n_components=2)  # 保留2个主成分
    pca_result = pca.fit_transform(image_reshaped)

    # 将结果重新变回图像的形状
    pca_band1 = pca_result[:, 0].reshape(rows, cols)
    pca_band2 = pca_result[:, 1].reshape(rows, cols)

    # 保存PCA结果
    with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=rows,
            width=cols,
            count=2,  # 两个主成分
            dtype=rasterio.float32,
            crs=src.crs,
            transform=src.transform
    ) as dst:
        dst.write(pca_band1, 1)  # 保存主成分1
        dst.write(pca_band2, 2)  # 保存主成分2

print(f"PCA result saved at {output_path}")


# ====== a_island.py ======
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

# ====== b_featuretoJson.py ======
# -*- coding: utf-8 -*-
"""
此脚本用于批量将指定文件夹下的 Shapefile (.shp) 文件转换为 GeoJSON 文件。
生成的 GeoJSON 文件将保存在指定的目标文件夹中。

生成日期：2024-09-10 15:39:13
"""

import os
import arcpy


def Model(shp, json):  # a_Feature to json
    """
    将 Shapefile 转换为 GeoJSON 文件。

    参数:
    shp (str): 输入的 Shapefile 文件路径。
    json (str): 输出的 GeoJSON 文件路径。
    """
    # 允许覆盖输出文件
    arcpy.env.overwriteOutput = True

    # 转换 Shapefile 为 GeoJSON
    arcpy.conversion.FeaturesToJSON(
        in_features=shp,
        out_json_file=json,
        format_json="NOT_FORMATTED",
        geoJSON="GEOJSON",
        outputToWGS84="WGS84",
        use_field_alias="USE_FIELD_NAME"
    )
    print(f'{json} conversion completed！')


def get_files_with_extension(directory, extension):
    """
    获取指定文件夹中具有特定扩展名的所有文件名。

    参数:
    directory (str): 文件夹路径。
    extension (str): 文件扩展名（包括点，例如 '.shp'）。

    返回:
    list: 包含指定扩展名文件名的列表。
    """
    # 规范化目录路径
    directory = os.path.normpath(directory)

    # 获取文件夹中的所有文件
    all_files = os.listdir(directory)

    # 筛选出指定扩展名的文件
    files_with_extension = [file for file in all_files if file.endswith(extension)]

    # 返回结果
    return files_with_extension


if __name__ == '__main__':
    # 设置全局环境变量
    # shp_folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\temp"
    shp_folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\b_Global_Island_Grid\_DGS_GSV_Grids"
    # json_folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\Geojson"
    json_folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\b_Global_Island_Grid\_DGS_GSV_Geojson"

    # 获取指定文件夹下所有后缀为 .shp 的文件名列表
    shp_files = get_files_with_extension(directory=shp_folder_path, extension='.shp')
    print(f"find '.shp' file: {shp_files}")

    # 遍历所有 .shp 文件
    for shp_name in shp_files:
        # 生成对应的 GeoJSON 文件名
        geo_name = shp_name.split('.')[0] + '.geojson'

        # 构建完整的文件路径
        feature_shp = os.path.join(shp_folder_path, shp_name)
        feature_geojson = os.path.join(json_folder_path, geo_name)

        # 调用 Model 函数批量转换 Shapefile 为 GeoJSON
        Model(shp=feature_shp, json=feature_geojson)

# ====== c_uploadBoundary.py ======
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
    # json_folder_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\b_continent_si_buffer\Africa_si_buffer_geojson'
    json_folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\b_Global_Island_Grid\_DGS_GSV_Geojson"
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
        # asset_path = fr'users/nicexian0011/_DGS_GSV_Grids/{json_name}'

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

# ====== d_cropImageSentinel.py ======
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

# ====== e_deleteAssets.py ======
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


# ====== e_v2.py ======
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


# ====== f_cropImageLandsat.py ======
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


def crop_image_landsat(boundary, year, output_path):
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
            # print(f'Number of images in the collection: {numImages}')

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

            # 确保波段顺序正确
            clippedMedian = clippedMedian.select(['SR_B4', 'SR_B3', 'SR_B2'])

            # 导出裁剪后的中值图像到 Google Drive
            outputDescription = img_name
            task = ee.batch.Export.image.toDrive(
                image=clippedMedian,
                folder=img_folder,
                fileNamePrefix=outputDescription,
                region=boundaryGeometry,
                scale=30,
                maxPixels=1e13,
                description=fr'Download Landsat 8 image {outputDescription}'  # 使用定义的任务名称
            )
            task.start()
            print(f'Task started: {outputDescription}')
        else:
            print(fr'No images found in the specified date range and cloud cover criteria.{boundary}')
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
    folder_path = 'users/nicexian0011/Africa_si_buffer'
    # 获取文件夹下的所有资产名称
    asset_names = list_assets_in_folder(folder_path)
    # aim_list = ['115605', '114062', '115607', '120049', '120008', '130247', '6448', '6451', '9220', '9226']

    for asset_name in asset_names:
        # 'projects/earthengine-legacy/assets/users/nicexian0011/islands/ISID_1005'
        # id = asset_name.split('_')[-1]

        # if id in aim_list:
        island_boundary = asset_name.split(fr'assets/')[-1]
        start_year = 2020
        gee_output_path = fr"Africa_land_20"
        crop_image_landsat(boundary=island_boundary, year=start_year, output_path=gee_output_path)


if __name__ == '__main__':
    main()

# ====== g_cropLandsatMNDWI.py ======
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

def crop_image_landsat(boundary, year, output_path):
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
            .filter(ee.Filter.lte('CLOUD_COVER', 50))

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

            # 确保提取指定的波段
            clippedMedian = clippedMedian.select(['SR_B4', 'SR_B3', 'SR_B2', 'SR_B6'])

            # 导出裁剪后的中值图像到 Google Drive
            outputDescription = img_name
            task = ee.batch.Export.image.toDrive(
                image=clippedMedian,
                folder=img_folder,
                fileNamePrefix=outputDescription,
                region=boundaryGeometry,
                scale=30,
                maxPixels=1e13,
                description=fr'Download Landsat 8 image {outputDescription}'  # 使用定义的任务名称
            )
            task.start()
            print(f'Task started: {outputDescription}')
        else:
            print(f'Task failed: {boundary}')
    else:
        print('FeatureCollection is null.')


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

    # island_boundary = fr"users/nicexian0011/islands/ISID_224209"
    # start_year = 2020
    # gee_output_path = fr"LandsatMNDWI"
    # crop_image_landsat(boundary=island_boundary, year=start_year, output_path=gee_output_path)
    #
    #
    # 指定文件夹路径
    folder_path = 'users/nicexian0011/Africa_si_buffer'
    # 获取文件夹下的所有资产名称
    asset_names = list_assets_in_folder(folder_path)
    # aim_list = ['206630', '114872', '344859', '17933', '18533', '56231', '18050']
    # aim_list = []

    for asset_name in asset_names:
        # 'projects/earthengine-legacy/assets/users/nicexian0011/islands/ISID_1005'
        # id = asset_name.split('_')[-1]

        # if id in aim_list:
        island_boundary = asset_name.split(fr'assets/')[-1]
        start_year = 2015
        gee_output_path = fr"Africa_land_15"
        crop_image_landsat(boundary=island_boundary, year=start_year, output_path=gee_output_path)


if __name__ == '__main__':
    main()

# ====== h_bandInterpolation.py ======
import rasterio
from rasterio.warp import calculate_default_transform
from rasterio.enums import Resampling
from pyproj import CRS
from scipy.ndimage import zoom

"""
    使用双线性插值方法对栅格图像进行缩放。
    它实际上是在执行上采样（增加分辨率），而不是下采样（降低分辨率）。
"""


def downscaling_by_interpolation(origin_tif, zoom_tif, zoom_ratio=2):
    # 设置输入输出路径
    input_path = origin_tif
    output_path = zoom_tif

    # 指定输出的坐标系 WGS 84
    target_crs = CRS.from_epsg(4326)  # WGS 84 EPSG:4326

    # 打开输入图像
    with rasterio.open(input_path) as src:
        # 读取原始图像的元数据
        src_crs = src.crs  # 原始坐标系
        transform = src.transform  # 原始的地理变换矩阵
        band_count = src.count  # 波段数量

        # 使用双线性插值法降尺度，提高分辨率（例如2倍分辨率）
        scale_factor = zoom_ratio

        # 创建用于存储重采样后数据的空列表
        resampled_bands = []

        # 对每个波段进行处理
        for band in range(1, band_count + 1):
            data = src.read(band)  # 读取每个波段的数据
            resampled_data = zoom(data, scale_factor, order=1)  # 双线性插值
            resampled_bands.append(resampled_data)  # 将重采样后的波段数据添加到列表中

        # 计算新的地理变换矩阵
        new_transform, new_width, new_height = calculate_default_transform(
            src_crs, target_crs, src.width * scale_factor, src.height * scale_factor, *src.bounds
        )

        # 写入新的图像文件
        with rasterio.open(
                output_path,
                'w',
                driver='GTiff',
                height=new_height,
                width=new_width,
                count=band_count,  # 保持波段数量不变
                dtype=resampled_bands[0].dtype,
                crs=target_crs,
                transform=new_transform,
        ) as dst:
            # 将每个波段写入新的文件
            for band in range(1, band_count + 1):
                dst.write(resampled_bands[band - 1], band)

    print(f"Resampled image saved at {output_path}")


if __name__ == '__main__':
    input_path = 'E:\\_OrderingProject\\F_IslandsBoundaryChange\\a_ArcData\\GEE_valid\\ISID_224209.tif'
    output_path = 'E:\\_OrderingProject\\F_IslandsBoundaryChange\\a_ArcData\\GEE_valid\\ISID_224209_zoom.tif'
    downscaling_by_interpolation(origin_tif=input_path, zoom_tif=output_path)


# ====== i_cadulateMNDWI.py ======
# -*- coding:utf-8 -*-
"""
作者：23242
日期：2024年09月17日
"""
import rasterio
import numpy as np

def calculate_band_ratio(input_path, output_path, band1, band2):
    # 打开遥感图像文件
    with rasterio.open(input_path) as src:
        # 读取指定的两个波段
        band1_data = src.read(band1).astype(float)
        band2_data = src.read(band2).astype(float)

        # 计算比值 (band1 - band2) / (band1 + band2)，注意这里的公式已修正为与函数名一致
        # ratio = (band1_data - band2_data) / (band1_data + band2_data + 1e-10)
        ratio = (band2_data - band1_data) / (band1_data + band2_data + 1e-10)

        # 处理无效值
        ratio[np.isinf(ratio)] = 0  # 替换无穷大为0
        ratio[np.isnan(ratio)] = 0  # 替换NaN为0

        # 将比值数据转换为与原图像相同的数据类型
        ratio = np.clip(ratio, 0, 1)  # 确保比值在0到1之间
        ratio_data = (ratio * 255).astype(np.uint8)  # 转换为0-255范围的整数

        # 创建输出文件的元数据
        out_meta = src.meta.copy()
        out_meta.update({
            'dtype': 'uint8',
            'count': 1,
            'height': ratio_data.shape[0],
            'width': ratio_data.shape[1]
        })

        # 写入输出文件
        with rasterio.open(output_path, 'w', **out_meta) as dst:
            dst.write(ratio_data, 1)

    print(f"MNDWI image saved to {output_path}")


if __name__ == '__main__':
    # 调用函数
    input_path = fr'E:\\_OrderingProject\\F_IslandsBoundaryChange\\a_ArcData\\GEE_valid\\ISID_224209_zoom.tif'  # 输入图像路径
    output_path = fr'E:\\_OrderingProject\\F_IslandsBoundaryChange\\a_ArcData\\GEE_valid\\ISID_224209_zoom_ND2.tif'  # 输出图像路径
    band1 = 1  # SR_B3 波段索引
    band2 = 2  # SR_B6 波段索引

    calculate_band_ratio(input_path, output_path, band1, band2)

    #    D:\ArcGISPro3\Pro\bin\Python\envs\arcgispro-py3\python.exe -m pip install --user pydrive -i https://pypi.doubanio.com/simple/
    # pip install dea- tools


# ====== j_distinguishRange.py ======
# -*- coding: utf-8 -*-
"""
Generated by ArcGIS ModelBuilder on : 2024-09-18 20:35:14
"""
import arcpy


def extract_by_mask(origin_tif, mask, identifier, output_tif):  # _draft

    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    # 确认掩膜范围 shp_mask
    # 加载Shapefile/GDB Layer
    shapefile_layer = fr"in_memory\mask_layer"
    feature_path = mask
    arcpy.MakeFeatureLayer_management(feature_path, shapefile_layer)

    # 标记id identifier
    where_clause = f"ALL_Uniq = {identifier}"
    arcpy.SelectLayerByAttribute_management(shapefile_layer, "NEW_SELECTION", where_clause)

    ISID_224209_tif = arcpy.Raster(origin_tif)
    _224209_shp = shapefile_layer

    # Process: 按掩膜提取 (按掩膜提取) (sa)
    ISID_extract_tif = output_tif
    extract_by_mask = ISID_extract_tif
    with arcpy.EnvManager(extent=_224209_shp):
        ISID_extract_tif = arcpy.sa.ExtractByMask(in_raster=ISID_224209_tif, in_mask_data=_224209_shp,
                                                  extraction_area="INSIDE", analysis_extent=ISID_224209_tif)
        ISID_extract_tif.save(extract_by_mask)

    # 清除选择状态
    arcpy.SelectLayerByAttribute_management(shapefile_layer, "CLEAR_SELECTION")

    print(fr"Extracting valid tif: {output_tif}")


if __name__ == '__main__':
    extract_by_mask(origin_tif='E:\\_OrderingProject\\F_IslandsBoundaryChange\\a_ArcData\\GEE_valid\\ISID_224209_zoom_ND.tif',
                    mask="E:\\_OrderingProject\\F_IslandsBoundaryChange\\a_ArcData\\temp\\224209.shp",
                    identifier='',
                    output_tif="E:\\_OrderingProject\\F_IslandsBoundaryChange\\a_ArcData\\GEE_valid\\ISID_224209_zoom_ND_extract.tif")
    pass
# E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\SmallIslands_con_buffer.gdb\Africa_buffer


# ====== k_subPixelWaterlineExtraction.py ======
# -*- coding:utf-8 -*-
"""
作者：23242
日期：2024年09月18日
"""
from dea_tools.spatial import subpixel_contours
import rasterio
import xarray as xr
import rioxarray  # Import rioxarray to access rio features


def subpixel_extraction(input_tif, z_values, subpixel_tif):
    # 定义 TIFF 文件路径
    # tif_file = r'E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE_valid\ISID_224209_zoom_ND_extract.tif'
    # subpixel_tif = fr"E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE\ISID_224209_zoom_ND_extract.geojson"
    tif_file = input_tif

    # 使用 rasterio 读取 TIFF 文件
    with rasterio.open(tif_file) as src:
        # 读取栅格数据
        raster_data = src.read(1)  # 读取第一个波段

        # 获取 TIFF 文件的元数据（如坐标系和变换信息）
        transform = src.transform
        crs = src.crs

        # 创建坐标数组
        height, width = raster_data.shape
        x_coords = [transform * (col, 0) for col in range(width)]  # 计算X轴坐标
        y_coords = [transform * (0, row) for row in range(height)]  # 计算Y轴坐标

        # 提取X和Y坐标
        x_coords = [x[0] for x in x_coords]
        y_coords = [y[1] for y in y_coords]

        # 将数据转换为 xarray DataArray
        data_array = xr.DataArray(
            raster_data,
            coords=[y_coords, x_coords],  # 设置坐标
            dims=["y", "x"],  # 定义维度名称
            attrs={
                'crs': str(crs),  # 设置坐标系
                'transform': transform  # 设置变换信息
            }
        )

    # 使用 rioxarray 设置 CRS
    data_array = data_array.rio.write_crs("EPSG:4326", inplace=True)

    # 打印 DataArray 的信息
    # print(data_array)

    subpixel_contours(da=data_array, z_values=z_values, attribute_df=None, output_path=subpixel_tif)


if __name__ == '__main__':
    # 定义 TIFF 文件路径
    tif_file = r'E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE_valid\ISID_224209_zoom_ND_extract.tif'
    subpixel_tif = fr"E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE\ISID_224209_zoom_ND_extract.geojson"
    subpixel_extraction(input_tif=tif_file, z_values=0, subpixel_tif=subpixel_tif)

# E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE
# E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\ISID_224209.tif

# pip install --upgrade shapely odc-geo

# #    D:\ArcGISPro3\Pro\bin\Python\envs\arcgispro-py3\python.exe -m pip install --user --upgrade fiona -i https://pypi.doubanio.com/simple/
# , output_path=fr"E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE"

# ====== k_v2.py ======
# -*- coding:utf-8 -*-
"""
作者：23242
日期：2024年09月18日
"""
from dea_tools.spatial import subpixel_contours
import rasterio
import xarray as xr
import rioxarray  # Import rioxarray to access rio features
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString


# 定义函数用于输出组件的首尾点，并封闭线段
def process_multilinestring(geometry):
    if isinstance(geometry, MultiLineString):
        for i, component in enumerate(geometry.geoms):  # 使用 .geoms 来迭代 MultiLineString 中的每个 LineString
            coords = list(component.coords)
            start_point = coords[0]
            end_point = coords[-1]
            # # 输出每个组件的首尾点
            # print(f"Component {i + 1}:")
            # print(f"  Start Point (Index: 0): Longitude: {start_point[0]}, Latitude: {start_point[1]}")
            # print(f"  End Point (Index: {len(coords) - 1}): Longitude: {end_point[0]}, Latitude: {end_point[1]}")
            # print('-' * 50)

            # 检查首尾点是否一致，不一致则封闭
            if start_point != end_point:
                # print(f"  Closing Component {i + 1}...")
                coords.append(start_point)  # 封闭
            # else:
            #     print(f"  Component {i + 1} is already closed.")
            # print('-' * 50)
            # 返回封闭后的 LineString
            yield LineString(coords)
    else:
        print("Geometry is not MultiLineString.")
        return None


def fix_subpixel_extraction(input_geojson, output_geojson):
    # 读取 GeoJSON 文件
    # input_geojson = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\k_subPixelWaterlineExtraction\UID_114940_subpixel.geojson"
    gdf = gpd.read_file(input_geojson)

    # 处理所有要素的几何
    for idx, row in gdf.iterrows():
        geometry = row['geometry']
        # print(f"Processing Feature {idx + 1}...")
        if isinstance(geometry, MultiLineString):
            closed_components = list(process_multilinestring(geometry))  # 封闭每个组件
            # 创建封闭后的 MultiLineString 几何
            closed_multilinestring = MultiLineString(closed_components)
            gdf.at[idx, 'geometry'] = closed_multilinestring  # 更新封闭后的几何
        else:
            print(f"Feature {idx + 1} is not a MultiLineString.")

    # 输出结果
    # output_geojson = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\k_subPixelWaterlineExtraction\UID_114940_subpixel_closed.geojson"
    gdf.to_file(output_geojson, driver="GeoJSON")
    print(f"Subpixel_closed MultiLineString output: {output_geojson}")


def subpixel_extraction(input_tif, z_values, subpixel_tif):
    # 定义 TIFF 文件路径
    # tif_file = r'E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE_valid\ISID_224209_zoom_ND_extract.tif'
    # subpixel_tif = fr"E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE\ISID_224209_zoom_ND_extract.geojson"
    tif_file = input_tif

    # 使用 rasterio 读取 TIFF 文件
    with rasterio.open(tif_file) as src:
        # 读取栅格数据
        raster_data = src.read(1)  # 读取第一个波段

        # 获取 TIFF 文件的元数据（如坐标系和变换信息）
        transform = src.transform
        crs = src.crs

        # 创建坐标数组
        height, width = raster_data.shape
        x_coords = [transform * (col, 0) for col in range(width)]  # 计算X轴坐标
        y_coords = [transform * (0, row) for row in range(height)]  # 计算Y轴坐标

        # 提取X和Y坐标
        x_coords = [x[0] for x in x_coords]
        y_coords = [y[1] for y in y_coords]

        # 将数据转换为 xarray DataArray
        data_array = xr.DataArray(
            raster_data,
            coords=[y_coords, x_coords],  # 设置坐标
            dims=["y", "x"],  # 定义维度名称
            attrs={
                'crs': str(crs),  # 设置坐标系
                'transform': transform  # 设置变换信息
            }
        )

    # 使用 rioxarray 设置 CRS
    data_array = data_array.rio.write_crs("EPSG:4326", inplace=True)

    # 打印 DataArray 的信息
    # print(data_array)


    # 未修复前
    subpixel_tif_temp = subpixel_tif.split('.geojson')[0] + '_temp.geojson'
    subpixel_contours(da=data_array, z_values=z_values, attribute_df=None, output_path=subpixel_tif_temp)
    # 修复闭合线段
    fix_subpixel_extraction(subpixel_tif_temp, subpixel_tif)


if __name__ == '__main__':
    # 定义 TIFF 文件路径
    tif_file = r'E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE_valid\ISID_224209_zoom_ND_extract.tif'
    subpixel_tif = fr"E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE\ISID_224209_zoom_ND_extract.geojson"
    subpixel_extraction(input_tif=tif_file, z_values=0, subpixel_tif=subpixel_tif)

# E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE
# E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\ISID_224209.tif

# pip install --upgrade shapely odc-geo

# #    D:\ArcGISPro3\Pro\bin\Python\envs\arcgispro-py3\python.exe -m pip install --user --upgrade fiona -i https://pypi.doubanio.com/simple/
# , output_path=fr"E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE"

# ====== l_buildShapeFeature.py ======
# -*- coding: utf-8 -*-
"""
Generated by ArcGIS ModelBuilder on : 2024-09-19 16:01:39
"""
import arcpy
import os
from sys import argv

def geojson_to_polygon(extract_geojson, shp_mask, identifier, tolerance, coast_line_shp):  # smooth

    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    # Process: JSON 转要素 (JSON 转要素) (conversion)
    ISID_JSONToFeature = "in_memory\\ISID_JSONToFeature"
    arcpy.conversion.JSONToFeatures(in_json_file=extract_geojson, out_features=ISID_JSONToFeature, geometry_type="POLYLINE")

    # Process: 平滑线 (平滑线) (cartography)
    ISID_SmoothLine = "in_memory\\ISID_224209_zo_JS_SmoothLine"
    with arcpy.EnvManager(transferGDBAttributeProperties="false"):
        arcpy.cartography.SmoothLine(in_features=ISID_JSONToFeature, out_feature_class=ISID_SmoothLine, algorithm="PAEK", tolerance=fr"{tolerance} Meters", endpoint_option="FIXED_CLOSED_ENDPOINT", error_option="NO_CHECK", in_barriers=[])

    # Process: 要素转面 (要素转面) (management)
    ISID_Polygon = "in_memory\\ISID_224209_Poly"
    arcpy.management.FeatureToPolygon(in_features=[ISID_SmoothLine], out_feature_class=ISID_Polygon, attributes="ATTRIBUTES")

    # 确认掩膜范围 shp_mask
    # 加载Shapefile/GDB Layer
    shapefile_layer = fr"in_memory\shapefile_layer"
    feature_path = shp_mask
    arcpy.MakeFeatureLayer_management(feature_path, shapefile_layer)

    # 标记id identifier
    where_clause = f"ALL_Uniq = {identifier}"
    arcpy.SelectLayerByAttribute_management(shapefile_layer, "NEW_SELECTION", where_clause)

    # Process: 要素转点 (要素转点) (management)
    center_poi = "in_memory\\_224209_cen"
    arcpy.management.FeatureToPoint(in_features=shapefile_layer, out_feature_class=center_poi, point_location="INSIDE")

    # 清除选择状态
    arcpy.SelectLayerByAttribute_management(shapefile_layer, "CLEAR_SELECTION")

    # Process: 按位置选择图层 (按位置选择图层) (management)
    aim_layer = arcpy.management.SelectLayerByLocation(in_layer=[ISID_Polygon], overlap_type="INTERSECT", select_features=center_poi, search_distance="", selection_type="NEW_SELECTION", invert_spatial_relationship="NOT_INVERT")

    # Process: 导出要素 (导出要素) (conversion)
    arcpy.conversion.ExportFeatures(in_features=aim_layer, out_features=coast_line_shp, where_clause="", use_field_alias_as_name="NOT_USE_ALIAS", sort_field=[])

    print(fr"Geojson to polygon: {coast_line_shp}")

if __name__ == '__main__':
    # Global Environment settings
    geojson_to_polygon(
        extract_geojson="E:\\_OrderingProject\\F_IslandsBoundaryChange\\a_ArcData\\GEE\\ISID_224209_zoom_ND_extract.geojson",
        shp_mask="E:\\_OrderingProject\\F_IslandsBoundaryChange\\a_ArcData\\temp\\224209.shp",
        identifier='273',
        tolerance=300,
        coast_line_shp="E:\\_OrderingProject\\F_IslandsBoundaryChange\\b_ArcMap\\IslandsBoundaryChange\\IslandsBoundaryChange.gdb\\ISID_224209_Po_fi222")
    pass


# ====== l_v2.py ======
# -*- coding: utf-8 -*-
"""
Generated by ArcGIS ModelBuilder on : 2024-09-19 16:01:39
"""
import arcpy
import os
from sys import argv


def export_largest_area_feature(input_feature, output_feature, area_field):
    # 初始化最大面积变量和最大面积的要素ID
    max_area = None
    max_feature = None

    # 设置路径到要素类（shapefile 或者 geodatabase 中的要素类）
    feature_class = input_feature  # 或者 .gdb 里面的要素类

    # # 使用 ListFields 函数获取字段列表
    # fields = arcpy.ListFields(feature_class)
    #
    # # 打印所有字段的名称
    # print("字段名称列表:")
    # for field in fields:
    #     print(field.name)

    # 使用 SearchCursor 遍历所有要素，寻找 area 字段最大的要素
    with arcpy.da.SearchCursor(input_feature, ['OID@', area_field]) as cursor:
        for row in cursor:
            oid, area_value = row
            if max_area is None or area_value > max_area:
                max_area = area_value
                max_feature = oid

    # 如果找到了最大面积的要素，执行导出
    if max_feature is not None:
        # 创建查询语句，基于 OBJECTID 选择最大面积的要素
        where_clause = f"OID = {max_feature}"
        # Process: 导出要素 (导出要素) (conversion)
        arcpy.conversion.ExportFeatures(in_features=input_feature, out_features=output_feature,
                                        where_clause=where_clause)
        print(f"Feature with the largest {area_field} value exported to {output_feature}")
    else:
        print("No features found with a valid area value.")

def geojson_to_polygon(extract_geojson, shp_mask, identifier, tolerance, coast_line_shp):  # smooth
    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    # Process: JSON 转要素 (JSON 转要素) (conversion)
    ISID_JSONToFeature = "in_memory\\ISID_JSONToFeature"
    arcpy.conversion.JSONToFeatures(in_json_file=extract_geojson, out_features=ISID_JSONToFeature,
                                    geometry_type="POLYLINE")
    # Process: 平滑线 (平滑线) (cartography)
    ISID_SmoothLine = "in_memory\\ISID_SmoothLine"
    with arcpy.EnvManager(transferGDBAttributeProperties="false"):
        arcpy.cartography.SmoothLine(in_features=ISID_JSONToFeature, out_feature_class=ISID_SmoothLine,
                                     algorithm="PAEK", tolerance=fr"{tolerance} Meters",
                                     endpoint_option="FIXED_CLOSED_ENDPOINT")
    # Process: 要素转面 (要素转面) (management)
    ISID_Polygon = "in_memory\\ISID_Poly"
    arcpy.management.FeatureToPolygon(in_features=[ISID_SmoothLine], out_feature_class=ISID_Polygon, attributes="ATTRIBUTES")
    # Process: 缓冲区 修复空洞
    # ISID_Polygon_Fixed = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\l_buildShapeFeature\ISID_Polygon_Fixed.shp"
    ISID_Polygon_Fixed = fr"in_memory\ISID_Polygon_Fixed"
    arcpy.analysis.Buffer(in_features=ISID_Polygon, out_feature_class="in_memory\\ISID_Polygon_Fixed_temp",
                          buffer_distance_or_field="50 Meters", line_side="FULL", line_end_type="ROUND",
                          dissolve_option="NONE", dissolve_field=[], method="PLANAR")
    arcpy.analysis.Buffer(in_features="in_memory\\ISID_Polygon_Fixed_temp", out_feature_class=ISID_Polygon_Fixed,
                          buffer_distance_or_field="-50 Meters", line_side="FULL", line_end_type="ROUND",
                          dissolve_option="NONE", dissolve_field=[], method="PLANAR")

    # Process: 要素转点 找到中心点
    ISID_Polygon_Fixed_Poi = "in_memory\\ISID_Polygon_Fixed_Poi"
    arcpy.management.FeatureToPoint(in_features=ISID_Polygon_Fixed, out_feature_class=ISID_Polygon_Fixed_Poi,
                                    point_location="INSIDE")

    # 确认掩膜范围 shp_mask
    # 加载Shapefile/GDB Layer
    shapefile_layer = fr"in_memory\shapefile_layer"
    feature_path = shp_mask
    arcpy.MakeFeatureLayer_management(feature_path, shapefile_layer)
    # 标记id identifier
    where_clause = f"ALL_Uniq = {identifier}"
    arcpy.SelectLayerByAttribute_management(shapefile_layer, "NEW_SELECTION", where_clause)

    # Process: 按位置选择图层 (选择有效中心点 Fixed_Poi_Valid)
    Fixed_Poi_SelectLayerByLocation = arcpy.management.SelectLayerByLocation(
        in_layer=[ISID_Polygon_Fixed_Poi], overlap_type="INTERSECT", select_features=shapefile_layer,
        search_distance="30 Meters", selection_type="NEW_SELECTION", invert_spatial_relationship="NOT_INVERT")
    # Process: 导出要素 (导出要素) (conversion)
    # Fixed_Poi_Valid = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\l_buildShapeFeature\Fixed_Poi_Valid.shp"     # 包含有效要素的中心点 Fixed_Poi_Valid
    Fixed_Poi_Valid = fr"in_memory\Fixed_Poi_Valid"
    arcpy.conversion.ExportFeatures(in_features=Fixed_Poi_SelectLayerByLocation, out_features=Fixed_Poi_Valid)
    # 清除选择状态
    arcpy.SelectLayerByAttribute_management(shapefile_layer, "CLEAR_SELECTION")
    arcpy.SelectLayerByAttribute_management(ISID_Polygon_Fixed_Poi, "CLEAR_SELECTION")

    # Process: 按位置选择图层 (选择有效图形)
    # Process: 添加连接 (添加连接) (management)
    # 使用 ListFields 函数获取字段列表
    # fields = arcpy.ListFields(ISID_Polygon_Fixed)
    # #
    # # 打印所有字段的名称
    # print("字段名称列表:")
    # for field in fields:
    #     print(field.name)
    ISID_Polygon_Fixed_link = \
    arcpy.management.JoinField(in_data=ISID_Polygon_Fixed, in_field="OBJECTID", join_table=Fixed_Poi_Valid,
                               join_field="ORIG_FID")[0]
    # Process: 导出要素 (导出要素) (conversion)
    ISID_Polygon_Fixed_temp = fr"in_memory\ISID_Polygon_Fixed_temp"     # 与中心点相交的图形
    arcpy.conversion.ExportFeatures(in_features=ISID_Polygon_Fixed_link, out_features=ISID_Polygon_Fixed_temp,
                                    where_clause="BUFF_DIST_1 <> 0")
    # Process: 计算几何属性 (计算几何属性) (management)
    ISID_Polygon_Fixed_temp2 = arcpy.management.CalculateGeometryAttributes(in_features=ISID_Polygon_Fixed_temp,
                                                                            geometry_property=[
                                                                                ["Shape_Area", "AREA_GEODESIC"]],
                                                                            coordinate_format="SAME_AS_INPUT")[0]
    # 导出有效图形中面积最大的
    export_largest_area_feature(input_feature=ISID_Polygon_Fixed_temp2, output_feature=coast_line_shp,
                                area_field='Shape_Area')

    print(fr"Geojson to polygon: {coast_line_shp}")

if __name__ == '__main__':
    # Global Environment settings
    geojson_to_polygon(
        extract_geojson="E:\\_OrderingProject\\F_IslandsBoundaryChange\\a_ArcData\\GEE\\ISID_224209_zoom_ND_extract.geojson",
        shp_mask="E:\\_OrderingProject\\F_IslandsBoundaryChange\\a_ArcData\\temp\\224209.shp",
        identifier='273',
        tolerance=300,
        coast_line_shp="E:\\_OrderingProject\\F_IslandsBoundaryChange\\b_ArcMap\\IslandsBoundaryChange\\IslandsBoundaryChange.gdb\\ISID_224209_Po_fi222")
    pass


# ====== m_caculateFields.py ======
# -*- coding: utf-8 -*-
"""
Generated by ArcGIS ModelBuilder on : 2024-09-19 19:56:45
"""
import arcpy

def caculate_area_length(origin_fields_shp):  # field

    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    # 标记 id 从 shp 名称里取得
    unique_id = origin_fields_shp.split('_')[-2]

    # Process: 计算字段 (计算字段) (management)
    ISID_224209_subpixel_2_ = arcpy.management.CalculateField(in_table=origin_fields_shp, field="UID_ISID", expression=unique_id, expression_type="PYTHON3", code_block="", field_type="TEXT", enforce_domains="NO_ENFORCE_DOMAINS")[0]

    # Process: 计算几何属性 (计算几何属性) (management)
    ISID_224209_subpixel_4_ = arcpy.management.CalculateGeometryAttributes(in_features=ISID_224209_subpixel_2_, geometry_property=[["Geo_Area", "AREA_GEODESIC"], ["Geo_Length", "PERIMETER_LENGTH_GEODESIC"]], length_unit="KILOMETERS", area_unit="SQUARE_KILOMETERS", coordinate_system="", coordinate_format="SAME_AS_INPUT")[0]

    print(fr"Caculate area and length: {origin_fields_shp}")

if __name__ == '__main__':
    shp_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE_valid\ISID_224209_subpixel.shp"
    caculate_area_length(origin_fields_shp=shp_path)

