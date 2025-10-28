import numpy as np
from scipy.ndimage import label, find_objects, gaussian_filter, zoom
import rasterio
from rasterio.warp import calculate_default_transform
from pyproj import CRS
import cv2


# 定义函数：读取影像并应用高斯滤波
def apply_gaussian_filter(image_path, sigma=1.0, output_path=None):
    """
    对输入影像应用高斯滤波，并可选择将结果保存。

    :param image_path: str，输入影像路径
    :param sigma: float，高斯滤波标准差，控制平滑程度
    :param output_path: str，输出影像路径（若提供，将保存滤波结果）
    :return: ndarray，滤波后的影像
    """
    # 读取影像文件
    with rasterio.open(image_path) as src:
        image = src.read(1)  # 读取单波段
        profile = src.profile  # 影像元数据

    # 应用高斯滤波
    filtered_image = gaussian_filter(image, sigma=sigma)

    # 保存滤波后的影像（若提供路径）
    if output_path:
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(filtered_image, 1)

    return filtered_image


# 筛选图像，去除面积小于阈值的区域，并保留含有 2x2 子区域的块
def filter_image_with_2x2_subregions(image_path, threshold=10, min_size=4):
    """
    筛选影像中大于阈值的像素，去除小区域，仅保留包含 2x2 子区域的块。

    :param image_path: str，输入影像路径
    :param threshold: int，筛选大于此值的像素
    :param min_size: int，最小保留区域面积（像素数）
    :return: tuple，筛选后的影像数组和影像元数据
    """
    # 读取影像
    with rasterio.open(image_path) as src:
        image = src.read(1)
        profile = src.profile

    # 生成二进制掩膜
    binary_mask = image > threshold

    # 使用8邻域连接结构
    structure = np.array([[1, 1, 1],
                          [1, 1, 1],
                          [1, 1, 1]])

    # 检测连通区域
    labeled_array, num_features = label(binary_mask, structure=structure)
    object_slices = find_objects(labeled_array)

    # 创建空数组保存筛选结果
    filtered_image = np.zeros_like(image)

    # 遍历连通区域，筛选符合面积要求并包含2x2子区域的区域
    for i, slice_tuple in enumerate(object_slices):
        region = labeled_array[slice_tuple] == (i + 1)
        area = np.sum(region)

        # 检查是否符合面积和包含2x2子区域
        if area >= min_size:
            contains_2x2 = any(
                np.all(region[x:x + 2, y:y + 2]) for x in range(region.shape[0] - 1) for y in range(region.shape[1] - 1)
            )

            if contains_2x2:
                filtered_image[slice_tuple] += image[slice_tuple] * region

    return filtered_image, profile


# 保存处理后的影像
def save_filtered_image(output_path, filtered_image, profile):
    """
    保存筛选后的影像为 GeoTIFF 文件。

    :param output_path: str，输出影像路径
    :param filtered_image: ndarray，筛选后的影像数据
    :param profile: dict，影像元数据
    """
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(filtered_image, 1)


# 定义函数：双线性插值降尺度影像
def downscaling_by_interpolation(origin_tif, zoom_tif, zoom_ratio=2):
    """
    对影像进行降尺度处理，使用双线性插值。

    :param origin_tif: str，输入影像路径
    :param zoom_tif: str，输出影像路径
    :param zoom_ratio: float，放大倍数，默认2倍
    """
    target_crs = CRS.from_epsg(4326)  # WGS 84 EPSG:4326

    # 打开影像
    with rasterio.open(origin_tif) as src:
        src_crs = src.crs
        transform = src.transform
        band_count = src.count

        # 重采样每个波段
        resampled_bands = [
            zoom(src.read(band), zoom_ratio, order=1) for band in range(1, band_count + 1)
        ]

        # 计算新地理变换矩阵
        new_transform, new_width, new_height = calculate_default_transform(
            src_crs, target_crs, src.width * zoom_ratio, src.height * zoom_ratio, *src.bounds
        )

        # 保存重采样后影像
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
            for band in range(1, band_count + 1):
                dst.write(resampled_bands[band - 1], band)


# 主流程函数：执行降尺度、高斯滤波及区域筛选
def filter_image(filter_input_path, filter_output_path):
    """
    主流程：对影像降尺度后高斯滤波，最后进行区域筛选。

    :param filter_input_path: str，输入影像路径
    :param filter_output_path: str，筛选后影像输出路径
    """
    temp_input_image_path = r'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\GEE_globe\C_zoom.tif'

    # 1. 执行降尺度
    downscaling_by_interpolation(origin_tif=filter_input_path, zoom_tif=temp_input_image_path)

    # 2. 对降尺度影像高斯滤波
    temp_output_image_path = r'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\GEE_globe\C_gaussian.tif'
    gaussian_filtered_image = apply_gaussian_filter(temp_input_image_path, sigma=0.5,
                                                    output_path=temp_output_image_path)

    # 3. 区域筛选，移除不符合要求的区域
    filtered_image, profile = filter_image_with_2x2_subregions(temp_output_image_path, threshold=10, min_size=4)

    # 保存筛选结果
    save_filtered_image(filter_output_path, filtered_image, profile)

    print(f"The filtered images have been saved to: {filter_output_path}")


# 主程序入口
if __name__ == '__main__':
    # 主流程：对影像降尺度后高斯滤波，最后进行区域筛选。
    filter_image(
        filter_input_path=fr'E:\_GoogleDrive\SouthChinaSea\114E22Nlb_MNDWI.tif',
        filter_output_path=fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Filtering\114E22Nlb_filter.tif'
    )
