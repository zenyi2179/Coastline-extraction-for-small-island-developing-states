import rasterio
import numpy as np
from scipy.ndimage import label, find_objects


# 定义函数：读取图像，筛选大于10的值，去除面积小于4的区域，并保留包含2x2正方形的区域
def filter_image_with_2x2_subregions(image_path, threshold=10, min_size=4):
    # 读取图像
    with rasterio.open(image_path) as src:
        image = src.read(1)  # 读取单波段数据
        profile = src.profile  # 获取图像元数据

    # 筛选出大于阈值的像素
    binary_mask = image > threshold

    # 定义 8 邻域连接的结构
    structure = np.array([[1, 1, 1],
                          [1, 1, 1],
                          [1, 1, 1]])

    # 使用 label() 函数标记连通区域，使用 8 邻域连接
    labeled_array, num_features = label(binary_mask, structure=structure)

    # 找到所有连通区域
    object_slices = find_objects(labeled_array)

    # 创建一个空数组，存储筛选后的图像
    filtered_image = np.zeros_like(image)

    # 遍历所有连通区域，筛选出面积大于等于 min_size 且包含 2x2 子区域的块
    for i, slice_tuple in enumerate(object_slices):
        region = labeled_array[slice_tuple] == (i + 1)  # 获取每个连通区域的掩膜
        area = np.sum(region)  # 计算区域的面积（像素数）

        # 如果区域面积大于等于 min_size
        if area >= min_size:
            # 检查该区域是否包含 2x2 的正方形子区域
            region_shape = region.shape
            contains_2x2 = False
            for x in range(region_shape[0] - 1):
                for y in range(region_shape[1] - 1):
                    # 检查2x2子区域
                    if np.all(region[x:x + 2, y:y + 2]):
                        contains_2x2 = True
                        break
                if contains_2x2:
                    break

            # 如果存在 2x2 的正方形子区域，则保留该区域
            if contains_2x2:
                filtered_image[slice_tuple] += image[slice_tuple] * region

    return filtered_image, profile


# 保存处理后的图像
def save_filtered_image(output_path, filtered_image, profile):
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(filtered_image, 1)


# 执行筛选操作
input_image_path = r'E:\_GoogleDrive\_DGS_GSV_Landsat\_UID_36584_gaussian.tif'
output_image_path = r'E:\_GoogleDrive\_DGS_GSV_Landsat\_UID_36584_gaussian_filtered.tif'

# 调用函数，筛选并保存图像
filtered_image, profile = filter_image_with_2x2_subregions(input_image_path, threshold=10, min_size=4)
save_filtered_image(output_image_path, filtered_image, profile)

print(f"处理后的图像已保存到: {output_image_path}")
