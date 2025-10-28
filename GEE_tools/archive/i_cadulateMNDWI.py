# -*- coding:utf-8 -*-
"""
作者：23242
日期：2024年09月17日
"""
import rasterio
import numpy as np

def calculate_band_ratio(input_path, output_path, band1, band2):
    # 打开遥感图像文件
    with rasterio.open(input_path) as src:
        # 读取指定的两个波段
        band1_data = src.read(band1).astype(float)
        band2_data = src.read(band2).astype(float)

        # 计算比值 (band1 - band2) / (band1 + band2)，注意这里的公式已修正为与函数名一致
        # ratio = (band1_data - band2_data) / (band1_data + band2_data + 1e-10)
        ratio = (band2_data - band1_data) / (band1_data + band2_data + 1e-10)

        # 处理无效值
        ratio[np.isinf(ratio)] = 0  # 替换无穷大为0
        ratio[np.isnan(ratio)] = 0  # 替换NaN为0

        # 将比值数据转换为与原图像相同的数据类型
        ratio = np.clip(ratio, 0, 1)  # 确保比值在0到1之间
        ratio_data = (ratio * 255).astype(np.uint8)  # 转换为0-255范围的整数

        # 创建输出文件的元数据
        out_meta = src.meta.copy()
        out_meta.update({
            'dtype': 'uint8',
            'count': 1,
            'height': ratio_data.shape[0],
            'width': ratio_data.shape[1]
        })

        # 写入输出文件
        with rasterio.open(output_path, 'w', **out_meta) as dst:
            dst.write(ratio_data, 1)

    print(f"MNDWI image saved to {output_path}")


if __name__ == '__main__':
    # 调用函数
    input_path = fr'E:\\_OrderingProject\\F_IslandsBoundaryChange\\a_ArcData\\GEE_valid\\ISID_224209_zoom.tif'  # 输入图像路径
    output_path = fr'E:\\_OrderingProject\\F_IslandsBoundaryChange\\a_ArcData\\GEE_valid\\ISID_224209_zoom_ND2.tif'  # 输出图像路径
    band1 = 1  # SR_B3 波段索引
    band2 = 2  # SR_B6 波段索引

    calculate_band_ratio(input_path, output_path, band1, band2)

    #    D:\ArcGISPro3\Pro\bin\Python\envs\arcgispro-py3\python.exe -m pip install --user pydrive -i https://pypi.doubanio.com/simple/
    # pip install dea- tools
