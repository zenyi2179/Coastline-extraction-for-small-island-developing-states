import os
import numpy as np
import rasterio
from scipy.ndimage import maximum_filter


def filter_by_local_max(data, window_size=31, max_threshold=0.5):
    """
    使用最大滤波器过滤局部区域低于最大阈值的像元。

    参数:
        data (np.ndarray): 输入二维数组（单波段栅格数据）。
        window_size (int): 最大滤波器窗口大小（应为奇数）。
        max_threshold (float): 最大值阈值。

    返回:
        np.ndarray: 滤波后的数组。
    """
    local_max = maximum_filter(data, size=window_size, mode='nearest')
    mask = local_max < max_threshold

    filtered = data.copy()
    filtered[mask] = 0
    return filtered


def apply_filter_to_raster(input_path, output_path, window_size=31, max_threshold=0.5):
    """
    对指定栅格图像应用局部最大值滤波，并保存输出。

    参数:
        input_path (str): 输入的 GeoTIFF 文件路径。
        output_path (str): 输出的 GeoTIFF 文件路径。
        window_size (int): 滤波器窗口大小。
        max_threshold (float): 最大值阈值。
    """
    with rasterio.open(input_path) as src:
        profile = src.profile
        data = src.read(1)

        filtered_data = filter_by_local_max(data, window_size, max_threshold)

        profile.update(dtype=rasterio.float32, nodata=None)
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(filtered_data.astype(np.float32), 1)


def main():
    input_tif = r'C:\Users\23042\Desktop\test\43E13Sru_ls578_Index.tif'
    output_tif = r'C:\Users\23042\Desktop\test\43E13Sru_ls578_Index_f.tif'
    apply_filter_to_raster(input_tif, output_tif, window_size=31, max_threshold=20)


if __name__ == '__main__':
    main()
