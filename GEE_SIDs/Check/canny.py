import numpy as np
import cv2
import rasterio
import geopandas as gpd
from shapely.geometry import Polygon, LineString
import matplotlib.pyplot as plt


def raster_to_vector_edges(tif_path, output_shp, low_threshold=10, high_threshold=150, min_contour_length=50):
    """
    计算水陆边界线，并输出封闭矢量（Shapefile）。

    :param tif_path: 输入单波段 TIF 影像路径
    :param output_shp: 输出矢量 Shapefile 文件路径
    :param low_threshold: Canny 低阈值
    :param high_threshold: Canny 高阈值
    :param min_contour_length: 最小轮廓长度（删除小碎片）
    """

    # 读取 TIF 栅格影像
    with rasterio.open(tif_path) as src:
        band = src.read(1)  # 读取单波段
        profile = src.profile  # 获取原始影像的元数据
        transform = src.transform  # 获取地理坐标变换信息

    # 归一化影像数据（0-255 范围）
    band = (band - band.min()) / (band.max() - band.min()) * 255
    band = band.astype(np.uint8)

    # 进行高斯滤波平滑影像
    blurred = cv2.GaussianBlur(band, (5, 5), 0)

    # 进行 Canny 边缘检测
    edges = cv2.Canny(blurred, low_threshold, high_threshold)

    # 提取边缘轮廓，使用 cv2.RETR_TREE 保持层级信息，cv2.CHAIN_APPROX_TC89_L1 进行优化
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_L1)

    # 存储矢量边界
    geometries = []
    for contour in contours:
        if len(contour) >= min_contour_length:  # 过滤掉过短的边界
            coords = [(transform * (x[0][0], x[0][1])) for x in contour]  # 像素坐标转地理坐标
            if len(coords) > 2:  # 至少 3 个点才能构成封闭多边形
                # geometries.append(Polygon(coords))  # 生成封闭多边形
                geometries.append(LineString(coords))

    # 将边界线转换为 GeoDataFrame
    gdf = gpd.GeoDataFrame(geometry=geometries, crs=src.crs)

    # 保存为 Shapefile
    gdf.to_file(output_shp, driver="ESRI Shapefile")

    # 可视化结果
    fig, ax = plt.subplots(1, 2, figsize=(12, 6))
    ax[0].imshow(band, cmap='gray')
    ax[0].set_title("Original Raster")
    ax[0].axis('off')

    ax[1].imshow(edges, cmap='gray')
    ax[1].set_title("Canny Edge Detection")
    ax[1].axis('off')

    plt.show()

    print(f"水陆边界矢量已保存至: {output_shp}")


# 设置输入输出文件路径
tif_input = r"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\SIDs_Grid_Y20\149E10Srb_ls578_Index.tif"
shp_output = r"C:\Users\23242\Desktop\check\output_boundary.shp"

# 执行水陆边界提取
raster_to_vector_edges(tif_input, shp_output)
