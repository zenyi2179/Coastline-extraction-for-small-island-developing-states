import numpy as np
import cv2
import rasterio
import matplotlib.pyplot as plt
import os


def median_filter_image(image, kernel_size=3):
    """
    对输入图像进行中值滤波以去除噪声。

    参数：
    - image (ndarray): 输入的灰度图像。
    - kernel_size (int): 滤波器的大小，必须为奇数。

    返回：
    - filtered_image (ndarray): 经过中值滤波后的图像。
    """
    # 使用 OpenCV 的 medianBlur 函数进行中值滤波
    filtered_image = cv2.medianBlur(image, kernel_size)
    return filtered_image


def process_image(input_file, output_file):
    """
    读取遥感图像，应用中值滤波，并保存处理后的图像。

    参数：
    - input_file (str): 输入图像路径。
    - output_file (str): 输出图像路径。
    """
    # 读取图像
    with rasterio.open(input_file) as src:
        image_data = src.read(1)  # 读取第一个波段
        profile = src.profile

    # 应用中值滤波
    filtered_image = median_filter_image(image_data, kernel_size=3)

    # 保存处理后的图像
    profile.update(dtype=rasterio.float32)
    with rasterio.open(output_file, 'w', **profile) as dst:
        dst.write(filtered_image.astype(rasterio.float32), 1)

    print(f"处理后的图像已保存到: {output_file}")


# 主程序
if __name__ == "__main__":
    input_path = r'E:\_GoogleDrive\_DGS_GSV_Landsat\43E25S_MNDWI.tif'
    output_path = r'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Filtering\43E25S_median_filtered_MNDWI.tif'

    process_image(input_path, output_path)

