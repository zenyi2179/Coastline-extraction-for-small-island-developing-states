import numpy as np
from scipy.ndimage import label, find_objects, gaussian_filter, zoom
import rasterio
from rasterio.warp import calculate_default_transform
from pyproj import CRS
import cv2


# 定义函数：读取图像并应用高斯滤波
def apply_gaussian_filter(image_path, sigma=1.0, output_path=None):
    """
    对输入的影像应用高斯滤波，并可选择将结果保存为新的影像文件。

    :param image_path: 输入影像路径
    :param sigma: 高斯滤波的标准差，控制平滑程度
    :param output_path: 输出影像路径（如果需要保存处理后的影像）
    :return: 滤波后的影像
    """
    # 读取输入影像文件
    with rasterio.open(image_path) as src:
        image = src.read(1)  # 读取单波段图像
        profile = src.profile  # 获取影像的元数据

    # 应用高斯滤波
    filtered_image = gaussian_filter(image, sigma=sigma)

    # 如果提供了输出路径，则保存滤波后的影像
    if output_path:
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(filtered_image, 1)

    return filtered_image


# 定义函数：筛选图像，去除面积小于指定阈值的区域，并保留含有 2x2 子区域的块
def filter_image_with_2x2_subregions(image_path, threshold=10, min_size=4):
    """
    筛选图像中大于指定阈值的像素，并移除面积小于最小尺寸的连通区域。
    仅保留包含 2x2 子区域的块。

    :param image_path: 输入影像路径
    :param threshold: 阈值，筛选大于该值的像素
    :param min_size: 保留的连通区域的最小面积
    :return: 筛选后的影像和元数据
    """
    # 读取输入影像
    with rasterio.open(image_path) as src:
        image = src.read(1)  # 读取单波段图像
        profile = src.profile  # 获取影像的元数据

    # 筛选出大于阈值的像素，形成二进制掩膜
    binary_mask = image > threshold

    # 定义 8 邻域连接结构，确保连通区域检测基于 8 邻域
    structure = np.array([[1, 1, 1],
                          [1, 1, 1],
                          [1, 1, 1]])

    # 使用 label() 函数标记所有连通区域，并返回每个区域的索引
    labeled_array, num_features = label(binary_mask, structure=structure)

    # 查找所有连通区域的切片对象
    object_slices = find_objects(labeled_array)

    # 创建一个空数组，用于存储筛选后的图像
    filtered_image = np.zeros_like(image)

    # 遍历所有连通区域，检查面积并保留包含 2x2 正方形子区域的区域
    for i, slice_tuple in enumerate(object_slices):
        region = labeled_array[slice_tuple] == (i + 1)  # 获取每个连通区域的掩膜
        area = np.sum(region)  # 计算该区域的面积（像素数）

        # 如果区域面积大于等于指定的最小面积
        if area >= min_size:
            # 检查该区域是否包含 2x2 的正方形子区域
            region_shape = region.shape
            contains_2x2 = False
            for x in range(region_shape[0] - 1):
                for y in range(region_shape[1] - 1):
                    # 检查 2x2 子区域是否都为 True
                    if np.all(region[x:x + 2, y:y + 2]):
                        contains_2x2 = True
                        break
                if contains_2x2:
                    break

            # 如果包含 2x2 子区域，则保留该区域
            if contains_2x2:
                filtered_image[slice_tuple] += image[slice_tuple] * region

    return filtered_image, profile


# 保存处理后的图像
def save_filtered_image(output_path, filtered_image, profile):
    """
    保存经过筛选的影像数据为 GeoTIFF 文件。

    :param output_path: 输出影像路径
    :param filtered_image: 筛选后的影像数据
    :param profile: 影像的元数据
    """
    # 保存影像文件
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(filtered_image, 1)


# 定义函数：通过双线性插值对图像进行降尺度
def downscaling_by_interpolation(origin_tif, zoom_tif, zoom_ratio=2):
    """
    对输入影像进行降尺度处理，使用双线性插值进行插值。

    :param origin_tif: 输入影像路径
    :param zoom_tif: 输出影像路径
    :param zoom_ratio: 放大比例，默认为2倍
    """
    # 指定输出的坐标系 WGS 84
    target_crs = CRS.from_epsg(4326)  # WGS 84 EPSG:4326

    # 打开输入影像
    with rasterio.open(origin_tif) as src:
        src_crs = src.crs  # 获取原始坐标系
        transform = src.transform  # 原始地理变换矩阵
        band_count = src.count  # 波段数量

        # 放大因子，进行图像降尺度
        scale_factor = zoom_ratio

        # 存储重采样后的波段数据
        resampled_bands = []

        # 对每个波段进行双线性插值重采样
        for band in range(1, band_count + 1):
            data = src.read(band)  # 读取每个波段的数据
            resampled_data = zoom(data, scale_factor, order=1)  # 双线性插值
            resampled_bands.append(resampled_data)

        # 计算新的地理变换矩阵
        new_transform, new_width, new_height = calculate_default_transform(
            src_crs, target_crs, src.width * scale_factor, src.height * scale_factor, *src.bounds
        )

        # 写入新的影像文件
        with rasterio.open(
                zoom_tif,
                'w',
                driver='GTiff',
                height=new_height,
                width=new_width,
                count=band_count,
                dtype=resampled_bands[0].dtype,
                crs=target_crs,
                transform=new_transform,
        ) as dst:
            # 将每个波段写入新文件
            for band in range(1, band_count + 1):
                dst.write(resampled_bands[band - 1], band)


# 主流程函数：执行多步骤处理，包括降尺度、高斯滤波和区域筛选
def filter_image(filter_input_path, filter_output_path):
    """
    主流程：先对影像进行降尺度处理，再进行高斯滤波，最后进行区域筛选。

    :param filter_input_path: 输入影像路径
    :param filter_output_path: 过滤后影像的输出路径
    """
    temp_input_image_path = r'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\GEE_globe\C_zoom.tif'

    # 执行降尺度操作
    downscaling_by_interpolation(origin_tif=filter_input_path, zoom_tif=temp_input_image_path)

    # 对降尺度后的影像进行高斯滤波
    temp_output_image_path = r'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\GEE_globe\C_gaussian.tif'
    gaussian_filtered_image = apply_gaussian_filter(temp_input_image_path, sigma=0.5,
                                                    output_path=temp_output_image_path)

    # 筛选图像区域，去除不符合要求的区域
    filtered_image, profile = filter_image_with_2x2_subregions(temp_output_image_path, threshold=10, min_size=4)

    # 保存筛选后的影像
    save_filtered_image(filter_output_path, filtered_image, profile)

    print(f"The filtered images have been saved to: {filter_output_path}")

# E:\_GoogleDrive\_DGS_GSV_Landsat\60W53S_MNDWI.tif

# 主程序入口
if __name__ == '__main__':
    # filter_image(
    #     filter_input_path=fr'E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\c_YY_2015\UID_30474_MNDWI.tif',
    #     filter_output_path=fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Filtering\UID_30474_filtered.tif'
    # )
    filter_image(
        filter_input_path=fr'E:\_GoogleDrive\_DGS_GSV_Landsat\67W56S_MNDWI.tif',
        filter_output_path=fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Filtering\67W56S_filtered.tif'
    )