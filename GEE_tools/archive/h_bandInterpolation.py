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
