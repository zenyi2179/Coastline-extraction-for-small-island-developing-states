import os
import rasterio
import numpy as np
from dbfread import DBF
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
    structure = np.array([[1,1,1], [1,1,1], [1,1,1]])  # 4邻域结构
    labeled, num_features = label(mask, structure=structure)  # 连通区域标记
    counts = np.bincount(labeled.ravel())  # 统计每个区域的像元数
    keep_mask = np.isin(labeled, np.where(counts >= min_cluster_size)[0])  # 创建保留区域掩码
    return np.where(keep_mask, data, nodata_value)

def fill_internal_holes(data: np.ndarray, fill_value: float = 20.0, max_hole_size: int = 500):
    """
    高效填补内部空洞，跳过像元数超过 max_hole_size 的区域（完全矢量化版本）
    """
    foreground = data != 0
    filled = binary_fill_holes(foreground)
    holes = filled & (~foreground)

    structure = np.ones((3, 3))  # 8邻域结构
    labeled, num_features = label(holes, structure=structure)

    # 计算每个空洞区域的像元数量
    counts = np.bincount(labeled.ravel())

    # 找出符合条件的区域索引（非0，且小于等于max_hole_size）
    valid_labels = np.where((counts > 0) & (counts <= max_hole_size))[0]

    # 构建保留掩码：只填补小于阈值的空洞区域
    mask_fill = np.isin(labeled, valid_labels)

    # 应用填补
    data_filled = data.copy()
    data_filled[mask_fill] = fill_value

    return data_filled

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

def read_txt_to_list(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    # 去除每行末尾的换行符
    lines = [line.strip() for line in lines]
    return lines


def read_dbf_to_list(dbf_path, if_print=0):
    """
    读取 DBF 文件并将内容存储为二维列表。

    参数:
    dbf_path (str): DBF 文件的路径。
    if_print (int): 是否打印二维列表的开关，0表示不打印，1表示打印。

    返回:
    list_of_records (list): 二维列表，每个子列表代表一条记录。
    """
    list_of_records = []
    dbf = DBF(dbf_path, encoding='utf-8')  # 打开 DBF 文件并设置编码为 'utf-8'

    # 获取并打印 DBF 文件的字段名称，即表头
    # print("Field names:", [field.name for field in dbf.fields])

    # 遍历 DBF 文件中的每条记录
    for record in dbf:
        # 将每条记录的值转换为列表，并添加到二维列表中
        list_of_records.append(list(record.values()))

    # 根据 if_print 参数决定是否打印二维列表
    if if_print:
        print("Records list:")
        print(list_of_records)

    return list_of_records

def tif_preprocessing(extract_threshold, fliter_threshold, tif_input, tif_output):
    # 打开原始 tif 文件并读取波段数据与 profile（元数据）
    with rasterio.open(tif_input) as src:
        data = src.read(1)
        profile = src.profile

    # 1️⃣ 步骤1：提取像元值 > 1 的区域
    data = extract_pixels_gt_threshold(data, threshold=extract_threshold)

    # 2️⃣ 步骤2：局部最大值滤波过滤背景噪点
    data = filter_by_local_max(data, window_size=31, max_threshold=fliter_threshold)

    # 3️⃣ 步骤3：移除面积小于 4 的栅格团块
    data = remove_small_clusters(data, min_cluster_size=4)

    # 4️⃣ 步骤4：封闭团块内的空洞，填充为20
    data = fill_internal_holes(data, fill_value=20.0)

    # 5️⃣ 步骤5：以中位数为指标清除不显著团块
    data = filter_clusters_by_median(data, threshold=fliter_threshold)

    # 更新输出影像 profile，并设置 nodata 值
    profile.update(dtype=rasterio.float32, count=1, nodata=0.0)

    # 写入最终处理结果
    with rasterio.open(tif_output, 'w', **profile) as dst:
        dst.write(data.astype(np.float32), 1)

    print(f"✅ 过滤流程完成，最终结果输出至：{tif_output}")


def main():
    # 初始化处理的国家和年份
    list_year = ['2010', '2015', '2020']
    list_sids = read_txt_to_list(file_path=fr"SIDS_37.txt")

    # for year in ['2015', '2020']:
    for year in list_year:
        # for sids in ['ATG']:
        for sids in list_sids:
            # 获得对应国家图幅
            dbf_grid_path = (
                fr".\SIDS_grid_link\{sids}_grid.dbf")
            list_sids_map = read_dbf_to_list(dbf_path=dbf_grid_path, if_print=0)
            # 国家图幅 ['63W16Nru', '62W16Nlu', '63W17Nrb', '62W17Nlb', '62W17Nlu']
            list_sids_map_name = [sublist[4] for sublist in list_sids_map]

            for map_name in list_sids_map_name:
                # 提取阈值
                if year == '2010':
                    extract_threshold = 1.0
                elif year == '2015':
                    extract_threshold = 5.0
                elif year == '2020':
                    extract_threshold = 9.0
                filter_threshold = 15.0
                # 输入原始遥感指数图像
                tif_input = (
                    fr"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData"
                    fr"\SIDs_Grid_Y{year[-2:]}\{map_name}_ls578_Index.tif")
                # 最终输出结果
                tif_output = (
                    fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\a_tif_GeeData"
                    fr"\{sids}\{year}\{sids}_{map_name}.tif")
                # 创建路径
                path_folder = os.path.dirname(tif_output)
                os.makedirs(path_folder, exist_ok=True)

                # 图像预处理
                try:
                    tif_preprocessing(extract_threshold, filter_threshold, tif_input, tif_output)
                except Exception as e:
                    pass


if __name__ == "__main__":
    main()
