import numpy as np
import rasterio
from scipy.ndimage import label


def remove_small_clusters(data, min_cluster_size=50):
    """
    移除小于指定大小的连通区域（使用8邻接规则）。

    参数:
        data (np.ndarray): 输入的二维栅格数据。
        min_cluster_size (int): 需要保留的最小斑块大小（像元数）。

    返回:
        np.ndarray: 已清除小团块的数组。
    """
    mask = data != 0
    structure = np.array([[1, 1, 1],
                          [1, 1, 1],
                          [1, 1, 1]], dtype=np.uint8)
    labeled_array, _ = label(mask, structure=structure)
    counts = np.bincount(labeled_array.ravel())

    filtered_data = np.copy(data)
    for label_id, count in enumerate(counts):
        if label_id == 0:
            continue
        if count < min_cluster_size:
            filtered_data[labeled_array == label_id] = 0
    return filtered_data


def apply_cluster_filter(input_path, output_path, min_cluster_size=50):
    """
    处理输入 GeoTIFF，去除小团块并保存。

    参数:
        input_path (str): 输入文件路径。
        output_path (str): 输出文件路径。
        min_cluster_size (int): 最小像元数（保留斑块大小）。
    """
    with rasterio.open(input_path) as src:
        profile = src.profile
        data = src.read(1)
        filtered_data = remove_small_clusters(data, min_cluster_size)
        profile.update(dtype=rasterio.float32)
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(filtered_data.astype(np.float32), 1)


def main():
    """主函数：处理单个 GeoTIFF 文件"""
    tif_input = r'C:\Users\23042\Desktop\test\43E13Sru_ls578_Index_f_otsu.tif'
    tif_output = r'C:\Users\23042\Desktop\test\43E13Sru_ls578_Index_f_otsu_re.tif'
    min_cluster_size = 4
    apply_cluster_filter(tif_input, tif_output, min_cluster_size)


if __name__ == '__main__':
    main()
