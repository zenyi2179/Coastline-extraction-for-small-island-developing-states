import rasterio
import numpy as np
import cv2
import os

# 输入文件路径和输出文件路径
input_file = r'C:\Users\23242\Desktop\draft1111\GEE_MNDWI.tif'
output_path = r'C:\Users\23242\Desktop\draft1111'
output_file = os.path.join(output_path, 'GEE_otsu_MNDWI.tif')

# 读取图像数据
with rasterio.open(input_file) as src:
    image_data = src.read(1)  # 读取第一个波段
    profile = src.profile     # 保存图像的元数据

# 使用 OpenCV 的 Otsu 方法进行二值化
# 将数据转换为 8 位（因为 Otsu 方法仅支持 uint8 格式）
image_data_8bit = cv2.normalize(image_data, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
_, otsu_thresholded = cv2.threshold(image_data_8bit, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

# 保存二值化后的图像，同时保持地理信息
profile.update(dtype=rasterio.uint8)  # 更新数据类型为 uint8

with rasterio.open(output_file, 'w', **profile) as dst:
    dst.write(otsu_thresholded, 1)  # 写入第一个波段

print("使用Otsu方法处理后的图像已保存到:", output_file)
