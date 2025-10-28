import numpy as np
import rasterio
from scipy.ndimage import binary_fill_holes


def fill_internal_holes(input_tif, output_tif):
    """
    填充栅格中目标区域内部的小孔隙（基于最大值区域）。

    参数:
        input_tif (str): 输入的二值 GeoTIFF。
        output_tif (str): 输出文件路径。
    """
    try:
        with rasterio.open(input_tif) as src:
            profile = src.profile
            data = src.read(1)

            # 找到唯一值
            unique_values = np.unique(data)
            if len(unique_values) == 1:
                print(f"[INFO] 跳过文件 {input_tif}，因为图像中只有一个唯一值。")
                return  # 跳过处理

            if len(unique_values) != 2:
                raise ValueError("该函数适用于二值图像（仅包含两个唯一值）")

            foreground_value = max(unique_values)
            background_value = min(unique_values)

            # 创建布尔掩膜，填充内部孔洞
            binary_mask = data == foreground_value
            filled_mask = binary_fill_holes(binary_mask)

            # 构建填充后的图像：前景区域设为 foreground_value，其他为 background
            filled_data = np.where(filled_mask, foreground_value, background_value)

            # 更新 profile，启用 PACKBITS 压缩
            profile.update(
                dtype=rasterio.uint8,  # 二值化图像可以使用 uint8 类型
                compress='packbits'  # 启用 PACKBITS 压缩
            )

            with rasterio.open(output_tif, 'w', **profile) as dst:
                dst.write(filled_data.astype(np.uint8), 1)

    except Exception as e:
        print(f"[ERROR] 在处理文件 {input_tif} 时发生错误：{e}")


def main():
    input_tif = r'C:\Users\23042\Desktop\test\43E13Sru_ls578_Index_f_otsu_re.tif'
    output_tif = r'C:\Users\23042\Desktop\test\43E13Sru_ls578_re_fi.tif'
    fill_internal_holes(input_tif, output_tif)


if __name__ == '__main__':
    main()