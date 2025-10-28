import numpy as np
import cv2
import rasterio
import geopandas as gpd
from shapely.geometry import Polygon, LineString
from skimage.morphology import closing, square
import matplotlib.pyplot as plt


def raster_to_vector_edges(tif_path, output_shp, low_threshold=50, high_threshold=150, blur_ksize=5):
    """
    计算水陆边界线，并输出矢量（Shapefile），优化边缘检测效果。

    :param tif_path: 输入单波段 TIF 影像路径
    :param output_shp: 输出矢量 Shapefile 文件路径
    :param low_threshold: Canny 低阈值
    :param high_threshold: Canny 高阈值
    :param blur_ksize: 高斯模糊核大小（推荐奇数）
    """

    # 读取 TIF 栅格影像
    with rasterio.open(tif_path) as src:
        band = src.read(1)  # 读取单波段
        transform = src.transform  # 获取地理坐标变换信息
        crs = src.crs  # 获取坐标参考系统

    # 归一化影像数据（0-255 范围）
    band = (band - band.min()) / (band.max() - band.min()) * 255
    band = band.astype(np.uint8)

    # **高斯模糊平滑**，减少噪声 & 锯齿
    blurred = cv2.GaussianBlur(band, (blur_ksize, blur_ksize), 0)

    # **Canny 边缘检测**
    edges = cv2.Canny(blurred, low_threshold, high_threshold)

    # **形态学闭运算**（填补边界空缺，使边界连续）
    closed_edges = closing(edges, square(3)).astype(np.uint8) * 255

    # **提取轮廓**
    contours, _ = cv2.findContours(closed_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # **转换为地理坐标**
    geometries = []
    for contour in contours:
        if len(contour) > 5:  # 过滤掉过短的边界
            coords = [(transform * (x[0][0], x[0][1])) for x in contour]  # 像素坐标 -> 地理坐标
            polygon = Polygon(coords)
            geometries.append(polygon)  # 生成封闭多边形

    # **转换为矢量数据**
    gdf = gpd.GeoDataFrame(geometry=geometries, crs=crs)

    # **保存 Shapefile**
    gdf.to_file(output_shp, driver="ESRI Shapefile")

    # **可视化**
    fig, ax = plt.subplots(1, 3, figsize=(18, 6))
    ax[0].imshow(band, cmap='gray')
    ax[0].set_title("Original Raster")
    ax[0].axis('off')

    ax[1].imshow(edges, cmap='gray')
    ax[1].set_title("Canny Edge Detection")
    ax[1].axis('off')

    ax[2].imshow(closed_edges, cmap='gray')
    ax[2].set_title("Post-Processed (Closed Edges)")
    ax[2].axis('off')

    plt.show()

    print(f"优化后的水陆边界矢量已保存至: {output_shp}")


# 设置输入输出文件路径
tif_input = r"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\SIDs_Grid_Y20\149E10Srb_ls578_Index.tif"
shp_output = r"C:\Users\23242\Desktop\check\optimized_boundary.shp"

# 执行优化版水陆边界提取
raster_to_vector_edges(tif_input, shp_output)
