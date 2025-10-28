import rasterio
import numpy as np
from scipy.ndimage import maximum_filter, label, binary_fill_holes

def extract_pixels_gt_threshold(data: np.ndarray, threshold: float = 5.0, nodata_value: float = 0.0):
    """
    提取像元值大于 threshold 的区域，其他区域赋值为 nodata_value。
    """
    return np.where(data > threshold, data, nodata_value)

def filter_by_local_max(data: np.ndarray, window_size: int = 31, max_threshold: float = 10.0, nodata_value: float = 0.0):
    """
    使用最大滤波器在局部窗口中计算最大值，如果窗口最大值小于 max_threshold，
    则将中心像元置为 nodata_value。
    """
    local_max = maximum_filter(data, size=window_size, mode='nearest')
    return np.where(local_max < max_threshold, nodata_value, data)

def remove_small_clusters(data: np.ndarray, min_cluster_size: int = 4, nodata_value: float = 0.0):
    """
    标记非零像元的连通区域，去除像元数少于 min_cluster_size 的小团块（设置为 nodata_value）。
    使用 4 邻接结构。
    """
    mask = data != 0
    structure = np.array([[0,1,0], [1,1,1], [0,1,0]])  # 4邻域结构
    labeled, num_features = label(mask, structure=structure)  # 连通区域标记
    counts = np.bincount(labeled.ravel())  # 统计每个区域的像元数
    keep_mask = np.isin(labeled, np.where(counts >= min_cluster_size)[0])  # 创建保留区域掩码
    return np.where(keep_mask, data, nodata_value)

def fill_internal_holes(data: np.ndarray, fill_value: float = 20.0):
    """
    填补前景区域（data != 0）内部的空洞（封闭的 0 区域），将其像元值赋值为 fill_value。
    """
    foreground = data != 0  # 前景布尔掩码
    filled = binary_fill_holes(foreground)  # 填补空洞
    holes = filled & (~foreground)  # 新填补的空洞区域
    data_copy = data.copy()
    data_copy[holes] = fill_value  # 赋值空洞区域
    return data_copy

def filter_clusters_by_median(data: np.ndarray, threshold: float = 10.0, connectivity: int = 8):
    """
    对每个非零连通团块，计算其像元中位数。若中位数小于 threshold，则整个团块赋值为 0。
    支持 8 或 4 邻接。
    """
    mask = data != 0
    structure = np.ones((3,3)) if connectivity == 8 else np.array([[0,1,0],[1,1,1],[0,1,0]])
    labeled, num_features = label(mask, structure=structure)  # 标记连通区域
    filtered_data = data.copy()

    for region_label in range(1, num_features + 1):
        region_mask = labeled == region_label
        region_values = data[region_mask]
        median_val = np.median(region_values)  # 计算中位数

        if median_val < threshold:
            filtered_data[region_mask] = 0  # 低于阈值则清除团块

    return filtered_data

def main():
    # 输入原始遥感指数图像
    tif_input = r"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\SIDs_Grid_Y15\25W14Nru_ls578_Index.tif"
    # 最终输出结果
    tif_output = r"E:\_OrderingProject\draft0621\temp5.tif"

    # 打开原始 tif 文件并读取波段数据与 profile（元数据）
    with rasterio.open(tif_input) as src:
        data = src.read(1)
        profile = src.profile

    # 1️⃣ 步骤1：提取像元值 > 1 的区域
    data = extract_pixels_gt_threshold(data, threshold=1.0)

    # 2️⃣ 步骤2：局部最大值滤波过滤背景噪点
    data = filter_by_local_max(data, window_size=31, max_threshold=10.0)

    # 3️⃣ 步骤3：移除面积小于 4 的栅格团块
    data = remove_small_clusters(data, min_cluster_size=4)

    # 4️⃣ 步骤4：封闭团块内的空洞，填充为20
    data = fill_internal_holes(data, fill_value=20.0)

    # 5️⃣ 步骤5：以中位数为指标清除不显著团块
    data = filter_clusters_by_median(data, threshold=10.0)

    # 更新输出影像 profile，并设置 nodata 值
    profile.update(dtype=rasterio.float32, count=1, nodata=0.0)

    # 写入最终处理结果
    with rasterio.open(tif_output, 'w', **profile) as dst:
        dst.write(data.astype(np.float32), 1)

    print(f"✅ 过滤流程完成，最终结果输出至：{tif_output}")

if __name__ == "__main__":
    main()
