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