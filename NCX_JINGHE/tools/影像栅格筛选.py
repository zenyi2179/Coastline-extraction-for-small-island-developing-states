import rasterio
import geopandas as gpd
import numpy as np
from rasterio.features import rasterize
from scipy.ndimage import label


def extract_connected_patches_fast(tif_path, shp_path, output_tif):
    """
    从二值栅格中提取与指定矢量相交的连通域，并输出到新的 GeoTIFF（高效版本）。

    :param tif_path: 输入二值 GeoTIFF 路径（值为 0 和 255）
    :param shp_path: 输入矢量文件路径（.shp）
    :param output_tif: 输出 GeoTIFF 路径
    """
    # 读取二值栅格
    with rasterio.open(tif_path) as src:
        raster_data = src.read(1)
        meta = src.meta.copy()
        transform = src.transform
        crs = src.crs

    # 读取矢量文件，并统一 CRS
    shp = gpd.read_file(shp_path)
    if shp.crs != crs:
        shp = shp.to_crs(crs)

    # 生成矢量对应的掩膜
    shp_mask = rasterize(
        [(geom, 1) for geom in shp.geometry],
        out_shape=raster_data.shape,
        transform=transform,
        fill=0,
        dtype=np.uint8
    )

    # 找出 255 区域的连通域
    binary_mask = (raster_data == 255).astype(np.uint8)
    labeled_array, num_features = label(binary_mask)

    # 计算每个连通域是否与矢量相交
    output_mask = np.zeros_like(binary_mask, dtype=np.uint8)
    for region_id in range(1, num_features + 1):
        region_mask = (labeled_array == region_id)
        if np.any(shp_mask[region_mask] == 1):  # 有相交
            output_mask[region_mask] = 255

    # 保存结果，确保无效部分为 0
    meta.update(dtype=rasterio.uint8, count=1, nodata=0)
    with rasterio.open(output_tif, 'w', **meta) as dst:
        dst.write(output_mask, 1)

    print(f"[INFO] 文件 {tif_path} 处理完成")


def main():
    """
    主程序入口，执行连通域提取并输出结果 GeoTIFF。
    """
    tif_origin = r'E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\temp\_reference_geedata\apply_cluster_filter\2015\24W15Nlb_ls578_Index.tif'
    shp_mask = r'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_15\CPV\_CPV_merge_BV.shp'
    tif_valid = r'E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\temp\_reference_geedata\apply_cluster_filter\tif_valid2.tif'

    extract_connected_patches_fast(tif_origin, shp_mask, tif_valid)


if __name__ == '__main__':
    main()
