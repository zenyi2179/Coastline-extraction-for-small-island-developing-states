import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from pyproj import CRS
import os
import numpy as np
import time

def downscaling_by_interpolation(origin_tif, zoom_tif, zoom_ratio=2):
    # 设置输入输出路径
    input_path = origin_tif
    output_path = zoom_tif

    # 指定输出的坐标系 WGS 84
    target_crs = CRS.from_epsg(4326)  # WGS 84 EPSG:4326

    # 打开输入图像
    with rasterio.open(input_path) as src:
        src_crs = src.crs  # 原始坐标系
        src_transform = src.transform  # 原始的地理变换矩阵
        src_width = src.width
        src_height = src.height
        src_bounds = src.bounds
        band_count = src.count  # 波段数量
        src_dtype = src.dtypes[0]

        # 计算新的宽度和高度
        scale_factor = zoom_ratio
        new_width = src_width * scale_factor
        new_height = src_height * scale_factor

        # 计算新的变换矩阵
        new_transform = src_transform * src_transform.scale(
            (src_width / new_width),
            (src_height / new_height)
        )

        # 计算目标变换和尺寸
        dst_transform, dst_width, dst_height = calculate_default_transform(
            src_crs, target_crs, new_width, new_height, *src.bounds
        )

        # 准备输出元数据
        dst_meta = src.meta.copy()
        dst_meta.update({
            'crs': target_crs,
            'transform': dst_transform,
            'width': dst_width,
            'height': dst_height
        })

        # 打开目标文件进行写入
        with rasterio.open(output_path, 'w', **dst_meta) as dst:
            for i in range(1, band_count + 1):
                # 读取源波段
                src_band = src.read(i)

                # 初始化目标波段数组
                dst_band = np.empty((dst_height, dst_width), dtype=src_dtype)

                # 使用双线性插值进行重采样和重投影
                reproject(
                    source=src_band,
                    destination=dst_band,
                    src_transform=src_transform,
                    src_crs=src_crs,
                    dst_transform=dst_transform,
                    dst_crs=target_crs,
                    resampling=Resampling.bilinear
                )

                # 写入目标波段
                dst.write(dst_band, i)

    print(f"Resampled image saved at {output_path}")

if __name__ == '__main__':
    input_path = r'E:\_OrderingProject\20367_ND2.tif'
    output_path = r'E:\_OrderingProject\20367_ND2_zoom.tif'
    downscaling_by_interpolation(origin_tif=input_path, zoom_tif=output_path)
