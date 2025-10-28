import numpy as np
import cv2
from osgeo import gdal, gdal_array

# 禁用异常处理
gdal.DontUseExceptions()

def threshold_with_gdal(input_tif_path, output_tif_path, threshold=10):
    """
    读取单波段 GeoTIFF，使用固定阈值进行二值化，并保持地理参考信息输出。

    参数:
        input_tif_path (str): 输入单波段 GeoTIFF 路径。
        output_tif_path (str): 输出二值化 GeoTIFF 路径。
        threshold (int): 阈值（0-255 之间），默认 10。
    """
    # 打开输入影像
    dataset = gdal.Open(input_tif_path, gdal.GA_ReadOnly)
    if dataset is None:
        raise IOError(f"Could not open file: {input_tif_path}")

    # 保存地理参考
    geo_transform = dataset.GetGeoTransform()
    projection = dataset.GetProjection()

    # 读取第一波段数据
    band = dataset.GetRasterBand(1)
    data = band.ReadAsArray()

    # 转为 uint8 并取绝对值
    data = np.abs(data).astype(np.uint8)

    # 固定阈值二值化（超过阈值为 255，否则为 0）
    _, binary_image = cv2.threshold(data, threshold, 255, cv2.THRESH_BINARY)

    # 创建输出 GeoTIFF
    driver = gdal.GetDriverByName('GTiff')
    out_dataset = driver.Create(output_tif_path,
                                binary_image.shape[1],
                                binary_image.shape[0],
                                1,
                                gdal.GDT_Byte)
    out_dataset.SetGeoTransform(geo_transform)
    out_dataset.SetProjection(projection)

    # 写入二值波段
    out_band = out_dataset.GetRasterBand(1)
    out_band.WriteArray(binary_image)
    out_band.FlushCache()  # 强制落盘

    # 关闭数据集
    out_dataset = None
    dataset = None


def main():
    """
    主函数：设置输入/输出路径并调用固定阈值二值化。
    """
    input_tif_path = r'C:\Users\23042\Desktop\test\43E13Sru_ls578_Index_f.tif'
    output_tif_path = r'C:\Users\23042\Desktop\test\43E13Sru_ls578_Index_f_threshold.tif'
    threshold_with_gdal(input_tif_path, output_tif_path, threshold=10)


if __name__ == '__main__':
    main()
