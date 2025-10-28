import rasterio
import numpy as np
from sklearn.decomposition import PCA

"""主成分分析"""

# 设置输入输出文件路径
input_path = 'E:\\_OrderingProject\\F_IslandsBoundaryChange\\a_ArcData\\GEE_valid\\ISID_224209_ND.tif'
output_path = 'E:\\_OrderingProject\\F_IslandsBoundaryChange\\a_ArcData\\GEE_valid\\ISID_224209_ND_PCA.tif'

# 打开输入的图像文件
with rasterio.open(input_path) as src:
    # 读取两个波段的数据
    band1 = src.read(1)  # 波段1
    band2 = src.read(2)  # 波段2

    # 将波段数据展平并组合成二维数组（像素点数 x 波段数）
    image_stack = np.dstack((band1, band2))
    rows, cols, bands = image_stack.shape
    image_reshaped = image_stack.reshape(rows * cols, bands)

    # 处理 NaN 值，替换为0或者图像的平均值
    image_reshaped = np.nan_to_num(image_reshaped, nan=np.nanmean(image_reshaped))

    # 执行主成分分析 (PCA)
    pca = PCA(n_components=2)  # 保留2个主成分
    pca_result = pca.fit_transform(image_reshaped)

    # 将结果重新变回图像的形状
    pca_band1 = pca_result[:, 0].reshape(rows, cols)
    pca_band2 = pca_result[:, 1].reshape(rows, cols)

    # 保存PCA结果
    with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            height=rows,
            width=cols,
            count=2,  # 两个主成分
            dtype=rasterio.float32,
            crs=src.crs,
            transform=src.transform
    ) as dst:
        dst.write(pca_band1, 1)  # 保存主成分1
        dst.write(pca_band2, 2)  # 保存主成分2

print(f"PCA result saved at {output_path}")
