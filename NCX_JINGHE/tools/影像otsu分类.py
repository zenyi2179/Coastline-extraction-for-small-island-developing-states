import numpy as np
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly
import cv2
import os


def otsu_threshold_with_gdal(input_path, output_path, no_data_value=None):
    """
    对单波段 GeoTIFF 进行 Otsu 自动阈值二值化处理
    输出0/255二值化图像，保持地理参考信息
    """
    print(f"开始处理: {input_path}")

    # 检查输入文件是否存在
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    # 打开输入影像
    input_dataset = gdal.Open(input_path, GA_ReadOnly)
    if input_dataset is None:
        raise ValueError(f"无法打开输入文件: {input_path}")

    # 获取基本信息
    rows = input_dataset.RasterYSize
    cols = input_dataset.RasterXSize
    print(f"影像尺寸: {cols} x {rows}")

    # 获取地理参考信息
    geotransform = input_dataset.GetGeoTransform()
    projection = input_dataset.GetProjection()

    # 读取波段数据
    band = input_dataset.GetRasterBand(1)
    data = band.ReadAsArray()

    # 获取NoData值（如果未指定）
    if no_data_value is None:
        no_data_value = band.GetNoDataValue()

    print(f"原始数据类型: {data.dtype}")
    print(f"原始数据范围: {np.nanmin(data)} ~ {np.nanmax(data)}")
    print(f"NoData值: {no_data_value}")

    # 处理 NaN 值和无穷值
    data = np.where(np.isnan(data) | np.isinf(data), 0, data)

    # 处理 NoData 值
    if no_data_value is not None and not np.isnan(no_data_value):
        data = np.where(np.abs(data - no_data_value) < 1e-6, 0, data)

    # 检查数据范围
    data_min = np.min(data)
    data_max = np.max(data)

    if data_min == data_max:
        print("警告: 所有像素值相同，无法进行Otsu阈值计算")
        # 返回全零图像
        binary_data = np.zeros_like(data, dtype=np.uint8)
    else:
        # 数据归一化到0-255范围用于Otsu计算
        data_for_otsu = ((data - data_min) / (data_max - data_min) * 255).astype(np.uint8)

        print("执行 Otsu 阈值计算...")
        # 应用 Otsu 阈值，获取最佳阈值
        threshold_value, _ = cv2.threshold(data_for_otsu, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        print(f"Otsu 计算的阈值: {threshold_value}")

        # 使用原始数据和计算出的阈值进行二值化
        # 将原始数据的阈值映射回原始范围
        original_threshold = data_min + (threshold_value / 255.0) * (data_max - data_min)
        print(f"原始数据对应的阈值: {original_threshold}")

        # 创建二值化结果：大于阈值为255，小于等于阈值为0
        binary_data = np.where(data > original_threshold, 255, 0).astype(np.uint8)

        # 统计二值化结果
        count_0 = np.sum(binary_data == 0)
        count_255 = np.sum(binary_data == 255)
        print(f"二值化结果 - 0值像素数: {count_0}, 255值像素数: {count_255}")

    # 创建输出数据集
    driver = gdal.GetDriverByName('GTiff')
    output_dataset = driver.Create(
        output_path,
        cols,
        rows,
        1,  # 单波段
        gdal.GDT_Byte
    )

    # 设置地理参考信息
    output_dataset.SetGeoTransform(geotransform)
    output_dataset.SetProjection(projection)

    # 设置 NoData 值
    output_band = output_dataset.GetRasterBand(1)
    output_band.SetNoDataValue(0)  # 0 通常表示背景/非目标区域

    # 写入二值化数据
    output_band.WriteArray(binary_data)

    # 强制写入磁盘并关闭数据集
    output_band.FlushCache()
    output_dataset.FlushCache()

    # 关闭数据集
    input_dataset = None
    output_dataset = None

    print(f"处理完成，结果保存至: {output_path}")
    return binary_data


def analyze_data_distribution(input_path):
    """
    分析输入数据的分布情况
    """
    dataset = gdal.Open(input_path, GA_ReadOnly)
    band = dataset.GetRasterBand(1)
    data = band.ReadAsArray()

    # 处理 NaN 和无穷值
    data_valid = np.where(np.isnan(data) | np.isinf(data), np.nan, data)
    valid_data = data_valid[~np.isnan(data_valid)]

    print("数据统计分析:")
    print(f"  总像素数: {data.size}")
    print(f"  有效像素数: {valid_data.size}")
    print(f"  NaN像素数: {np.isnan(data).sum()}")
    print(f"  无穷值像素数: {np.isinf(data).sum()}")
    if valid_data.size > 0:
        print(f"  有效数据范围: {valid_data.min():.6f} ~ {valid_data.max():.6f}")
        print(f"  有效数据均值: {valid_data.mean():.6f}")
        print(f"  有效数据标准差: {valid_data.std():.6f}")
    else:
        print("  无有效数据")

    dataset = None


def validate_binary_output(output_path):
    """
    验证输出的二值化图像是否真的只有0和255两个值
    """
    dataset = gdal.Open(output_path, GA_ReadOnly)
    band = dataset.GetRasterBand(1)
    data = band.ReadAsArray()

    unique_values = np.unique(data)
    print(f"输出图像的唯一值: {unique_values}")

    is_binary = set(unique_values) <= {0, 255}
    print(f"是否为真正的二值化图像: {is_binary}")

    if is_binary:
        count_0 = np.sum(data == 0)
        count_255 = np.sum(data == 255)
        print(f"验证通过 - 0值像素: {count_0}, 255值像素: {count_255}")
    else:
        print(f"验证失败 - 发现非0/255值: {set(unique_values) - {0, 255} }")

    dataset = None
    return is_binary


def main():
    """
    主函数：演示 Otsu 阈值处理的使用
    """
    input_path = r"C:\Users\23042\Desktop\test\108_5E21_8N_MNDWI.tif"
    output_path = r"C:\Users\23042\Desktop\test\108_5E21_8N_MNDWI_otsu_final.tif"

    if os.path.exists(input_path):
        # 先分析数据分布
        print("分析输入数据分布...")
        analyze_data_distribution(input_path)

        # 执行 Otsu 阈值二值化
        result = otsu_threshold_with_gdal(input_path, output_path)

        # 验证输出结果
        print("\n验证输出结果...")
        validate_binary_output(output_path)
        print(f"Otsu 阈值二值化完成，结果保存至: {output_path}")
    else:
        print(f"输入文件不存在: {input_path}")
        # 创建示例MNDWI数据进行测试
        print("创建示例MNDWI数据进行演示...")

        # 创建一个模拟的MNDWI数据（通常MNDWI值在-1到1之间）
        np.random.seed(42)  # 为了结果可重现
        example_data = np.random.uniform(-0.5, 0.5, (500, 500)).astype(np.float32)
        # 添加一些异常值和NaN值
        example_data[100:200, 100:200] = np.nan
        example_data[250:300, 250:300] = np.inf

        driver = gdal.GetDriverByName('GTiff')
        example_dataset = driver.Create('example_mndwi.tif', 500, 500, 1, gdal.GDT_Float32)
        example_dataset.GetRasterBand(1).WriteArray(example_data)
        example_dataset.GetRasterBand(1).SetNoDataValue(np.nan)
        example_dataset = None

        # 处理示例数据
        result = otsu_threshold_with_gdal('example_mndwi.tif', 'example_output_final.tif')

        # 验证输出结果
        print("\n验证示例输出结果...")
        validate_binary_output('example_output_final.tif')
        print("示例处理完成")


if __name__ == '__main__':
    main()



