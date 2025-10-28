"""
1. 提取 .tif 文件中像元值大于 5 的区域并输出为新 .tif
"""
import rasterio
import numpy as np
from scipy.ndimage import maximum_filter
from scipy.ndimage import label
from scipy.ndimage import binary_fill_holes


def extract_pixels_gt_threshold(input_tif: str, output_tif: str, threshold: float = 5.0, nodata_value: float = 0.0):
    """
    提取像元值大于给定阈值的区域，并将其输出为新的 GeoTIFF 文件。

    参数:
        input_tif (str): 输入的 .tif 文件路径。
        output_tif (str): 输出的 .tif 文件路径。
        threshold (float): 像元阈值，默认是 5.0。
        nodata_value (float): 不满足条件的像元值填充值，默认是 0.0。
    """
    with rasterio.open(input_tif) as src:
        data = src.read(1)  # 读取第一个波段
        profile = src.profile

        # 创建掩码：像元值 > 阈值
        mask_data = data > threshold

        # 应用掩码：不满足条件的像元设为 nodata_value
        filtered_data = np.where(mask_data, data, nodata_value)

        # 更新 profile 信息
        profile.update(dtype=rasterio.float32, count=1, nodata=nodata_value)

        # 写入输出文件
        with rasterio.open(output_tif, 'w', **profile) as dst:
            dst.write(filtered_data.astype(rasterio.float32), 1)

    print(f"输出完成：{output_tif}")


def filter_by_local_max(input_tif: str, output_tif: str, window_size: int = 30, max_threshold: float = 10.0,
                        nodata_value: float = 0.0):
    """
    使用局部窗口（如30x30）进行最大值过滤：
    如果以像元为中心的窗口最大值 < max_threshold，则将该中心像元设置为 nodata_value。

    参数:
        input_tif (str): 输入 tif 文件路径。
        output_tif (str): 输出 tif 文件路径。
        window_size (int): 滤波窗口的大小（必须为奇数）。
        max_threshold (float): 最大值的阈值。
        nodata_value (float): 滤除后的像元值。
    """
    if window_size % 2 == 0:
        raise ValueError("window_size 必须为奇数，例如 29 或 31")

    with rasterio.open(input_tif) as src:
        data = src.read(1)  # 读取第一个波段
        profile = src.profile

        # 使用最大滤波器获取局部最大值
        local_max = maximum_filter(data, size=window_size, mode='nearest')

        # 过滤条件：窗口最大值 < 阈值 → 当前像元设为 nodata
        filtered_data = np.where(local_max < max_threshold, nodata_value, data)

        # 更新 profile
        profile.update(dtype=rasterio.float32, count=1, nodata=nodata_value)

        # 写入输出文件
        with rasterio.open(output_tif, 'w', **profile) as dst:
            dst.write(filtered_data.astype(rasterio.float32), 1)

    print(f"局部最大值过滤完成：{output_tif}")

def remove_small_clusters(input_tif: str, output_tif: str, min_cluster_size: int = 4, nodata_value: float = 0.0):
    """
    移除像元数量少于 min_cluster_size 的相邻小团块（连通区域）。

    参数:
        input_tif (str): 输入的栅格路径。
        output_tif (str): 输出文件路径。
        min_cluster_size (int): 最小保留的连通区域大小（像元数）。
        nodata_value (float): 被移除区域赋值。
    """
    with rasterio.open(input_tif) as src:
        data = src.read(1)
        profile = src.profile

        # 创建掩码：非0区域为目标区域
        mask = data != 0

        # 连通区域标记，8邻域结构
        structure = np.array([[0, 1, 0],
                              [1, 1, 1],
                              [0, 1, 0]])
        labeled, num_features = label(mask, structure=structure)

        # 统计每个区域的像元数量
        counts = np.bincount(labeled.ravel())

        # 创建掩码：保留像元数量 ≥ min_cluster_size 的区域
        keep_mask = np.isin(labeled, np.where(counts >= min_cluster_size)[0])

        # 应用掩码：过滤小团块
        filtered_data = np.where(keep_mask, data, nodata_value)

        # 更新 profile
        profile.update(dtype=rasterio.float32, count=1, nodata=nodata_value)

        # 保存结果
        with rasterio.open(output_tif, 'w', **profile) as dst:
            dst.write(filtered_data.astype(rasterio.float32), 1)

    print(f"小团块过滤完成（保留大小 ≥ {min_cluster_size}）：{output_tif}")


def fill_internal_holes(input_tif: str, output_tif: str, fill_value: float = 20.0):
    """
    封闭非零区域内部的空洞（值为0的像元），并赋值为指定值。

    参数:
        input_tif (str): 输入的.tif路径。
        output_tif (str): 输出的.tif路径。
        fill_value (float): 填充空洞的像元值，默认是 20.0。
    """
    with rasterio.open(input_tif) as src:
        data = src.read(1)
        profile = src.profile

        # 创建前景掩码（非零区域为前景）
        foreground = data != 0

        # 空洞填充：对前景进行填洞（binary_fill_holes作用于布尔数组）
        filled_foreground = binary_fill_holes(foreground)

        # 空洞区域 = 填充后 - 原前景（True表示原来是空洞）
        holes = filled_foreground & (~foreground)

        # 把空洞像元赋值为指定填充值
        data_filled = data.copy()
        data_filled[holes] = fill_value

        # 更新 profile
        profile.update(dtype=rasterio.float32, nodata=0.0)

        # 写出结果
        with rasterio.open(output_tif, 'w', **profile) as dst:
            dst.write(data_filled.astype(rasterio.float32), 1)

    print(f"空洞填充完成，空洞像元赋值为 {fill_value} ：{output_tif}")



def filter_clusters_by_median(input_tif: str, output_tif: str, threshold: float = 10.0, connectivity: int = 8):
    """
    根据像元团块中像元值的中位数过滤小团块。中位数小于 threshold 的团块将被赋值为 0。

    参数:
        input_tif (str): 输入栅格路径。
        output_tif (str): 输出栅格路径。
        threshold (float): 中位数阈值，小于该值的团块将被清除。
        connectivity (int): 连通性（4 或 8），默认使用8邻接。
    """
    with rasterio.open(input_tif) as src:
        data = src.read(1)
        profile = src.profile

        # 标记非0的连通区域
        mask = data != 0
        structure = np.array([[1,1,1],[1,1,1],[1,1,1]]) if connectivity == 8 else np.array([[0,1,0],[1,1,1],[0,1,0]])
        labeled_array, num_features = label(mask, structure=structure)

        print(f"共检测到 {num_features} 个栅格团块")

        # 复制数据用于输出
        filtered_data = data.copy()

        for region_label in range(1, num_features + 1):
            region_mask = labeled_array == region_label
            region_values = data[region_mask]

            # 计算中位数
            median_val = np.median(region_values)

            # 若中位数 < 阈值，则清除团块
            if median_val < threshold:
                filtered_data[region_mask] = 0

        # 更新并写入
        profile.update(dtype=rasterio.float32, nodata=0.0)

        with rasterio.open(output_tif, 'w', **profile) as dst:
            dst.write(filtered_data.astype(rasterio.float32), 1)

    print(f"✅ 团块过滤完成：输出为 {output_tif}")

def main():
    tif_gee = fr"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\SIDs_Grid_Y15\25W14Nru_ls578_Index.tif"
    temp_trush = fr'E:\_OrderingProject\draft0621'
    tif_temp1 = fr"{temp_trush}\temp1.tif"

    extract_pixels_gt_threshold(
        input_tif=tif_gee,
        output_tif=tif_temp1,
        threshold=1.0,
    )

    tif_temp2 = fr"{temp_trush}\temp2.tif"
    filter_by_local_max(
        input_tif=tif_temp1,
        output_tif=tif_temp2,
        window_size=31,
        max_threshold=10.0,
    )

    tif_temp3 = fr"{temp_trush}\temp3.tif"
    remove_small_clusters(
        input_tif=tif_temp2,
        output_tif=tif_temp3,
        min_cluster_size=4,
        nodata_value=0.0
    )

    tif_temp4 = fr"{temp_trush}\temp4.tif"
    fill_internal_holes(
        input_tif=tif_temp3,
        output_tif=tif_temp4,
        fill_value=20.0
    )

    tif_temp5 = fr"{temp_trush}\temp5.tif"
    filter_clusters_by_median(
        input_tif=tif_temp4,
        output_tif=tif_temp5,
        threshold=10.0,
    )


if __name__ == "__main__":
    main()
