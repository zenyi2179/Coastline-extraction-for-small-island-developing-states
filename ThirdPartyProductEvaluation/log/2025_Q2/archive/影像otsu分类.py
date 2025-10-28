import numpy as np
import cv2
from osgeo import gdal, gdal_array


def otsu_threshold_with_gdal(input_tif_path, output_tif_path):
    """
    读取单波段 GeoTIFF，使用 Otsu 算法进行二值化，并保持地理参考信息输出。

    参数:
        input_tif_path (str): 输入单波段 GeoTIFF 路径。
        output_tif_path (str): 输出二值化 GeoTIFF 路径。
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

    # 转为 uint8 并取绝对值，确保数据类型符合 Otsu 要求
    data = np.abs(data).astype(np.uint8)

    # Otsu 二值化：自动计算阈值，输出 0/255
    _, binary_image = cv2.threshold(data, 0, 255,
                                    cv2.THRESH_BINARY + cv2.THRESH_OTSU)

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

    print(f'Otsu thresholded image saved to: {output_tif_path}')


def main():
    """
    主函数：设置输入/输出路径并调用 Otsu 二值化。
    """
    input_tif_path = r'C:\Users\23042\Desktop\test\43E13Sru_ls578_Index_f.tif'
    output_tif_path = r'C:\Users\23042\Desktop\test\43E13Sru_ls578_Index_f_otsu.tif'

    otsu_threshold_with_gdal(input_tif_path, output_tif_path)


if __name__ == '__main__':
    main()
