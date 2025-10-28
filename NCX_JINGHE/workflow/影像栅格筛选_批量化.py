import os
import rasterio
import geopandas as gpd
import numpy as np
from rasterio.features import rasterize
from scipy.ndimage import label
from shapely.geometry import box
from worktools import get_files_by_extension


def build_vector_spatial_index(shp_path, target_crs):
    """
    构建矢量数据的空间索引（R-tree），用于批处理快速筛选相交要素。

    :param shp_path: 输入矢量文件路径（.shp）
    :param target_crs: 目标坐标参考系（与栅格一致）
    :return: (GeoDataFrame, sindex)，GeoDataFrame 和其空间索引对象
    """
    shp = gpd.read_file(shp_path)
    if shp.crs != target_crs:
        shp = shp.to_crs(target_crs)
    sindex = shp.sindex
    return shp, sindex


def extract_connected_patches(tif_path, shp_gdf, sindex, output_tif):
    """
    从二值栅格中提取与指定矢量相交的连通域，并输出到新的 GeoTIFF。

    :param tif_path: 输入二值 GeoTIFF 路径（值为 0 和 255）
    :param shp_gdf: 已加载的 GeoDataFrame（与栅格 CRS 一致）
    :param sindex: 对应 GeoDataFrame 的空间索引对象
    :param output_tif: 输出 GeoTIFF 路径
    """
    # 读取栅格
    with rasterio.open(tif_path) as src:
        raster_data = src.read(1)
        meta = src.meta.copy()
        transform = src.transform
        crs = src.crs
        tif_bounds_geom = box(*src.bounds)

    # 使用空间索引获取相交的矢量要素
    possible_matches_idx = list(sindex.intersection(tif_bounds_geom.bounds))
    if not possible_matches_idx:
        # 如果没有相交要素，直接输出空栅格
        output_mask = np.zeros_like(raster_data, dtype=np.uint8)
        meta.update(dtype=rasterio.uint8, count=1, nodata=0, compress='packbits')  # 启用 PACKBITS 压缩
        with rasterio.open(output_tif, 'w', **meta) as dst:
            dst.write(output_mask, 1)
        print(f"[INFO] {tif_path} 无相交矢量，输出空掩膜")
        return

    # 裁剪出相交的矢量部分
    shp_clipped = shp_gdf.iloc[possible_matches_idx]
    shp_clipped = gpd.clip(shp_clipped, gpd.GeoDataFrame(geometry=[tif_bounds_geom], crs=crs))

    if shp_clipped.empty:
        output_mask = np.zeros_like(raster_data, dtype=np.uint8)
        meta.update(dtype=rasterio.uint8, count=1, nodata=0, compress='packbits')  # 启用 PACKBITS 压缩
        with rasterio.open(output_tif, 'w', **meta) as dst:
            dst.write(output_mask, 1)
        print(f"[INFO] {tif_path} 裁剪后无矢量数据，输出空掩膜")
        return

    # 生成矢量掩膜
    shp_mask = rasterize(
        [(geom, 1) for geom in shp_clipped.geometry],
        out_shape=raster_data.shape,
        transform=transform,
        fill=0,
        dtype=np.uint8
    )

    # 找出 255 区域的连通域
    binary_mask = (raster_data == 255).astype(np.uint8)
    labeled_array, num_features = label(binary_mask)

    # 判断相交的连通域并输出
    output_mask = np.zeros_like(binary_mask, dtype=np.uint8)
    for region_id in range(1, num_features + 1):
        region_mask = (labeled_array == region_id)
        if np.any(shp_mask[region_mask] == 1):
            output_mask[region_mask] = 255

    # 保存结果，启用 PACKBITS 压缩
    meta.update(dtype=rasterio.uint8, count=1, nodata=0, compress='packbits')
    with rasterio.open(output_tif, 'w', **meta) as dst:
        dst.write(output_mask, 1)

    print(f"[INFO] 文件 {tif_path} 处理完成")


def main():
    """
    主程序：批量处理多个年份和多个 GeoTIFF 文件，提取与矢量相交的连通域。
    使用矢量空间索引提高性能。
    """
    # path_base = r'E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\temp'
    path_base = r'E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\temp\_reference_geedata'
    path_mask = r'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\_third_party_dataset'
    list_year = [2010, 2015, 2020]

    print(f"[INFO] 开始处理年份列表：{list_year}")

    for year in list_year:
        path_tif = os.path.join(path_base, fr'apply_cluster_filter\{year}')
        list_tif = get_files_by_extension(path_tif, '.tif', return_absolute_path=True)
        print(f"[INFO] {year} 年共找到 {len(list_tif)} 个 .tif 文件")

        if not list_tif:
            continue

        # 用第一张 TIF 的 CRS 初始化矢量数据和空间索引
        with rasterio.open(list_tif[0]) as src:
            tif_crs = src.crs

        shp_mask = os.path.join(path_mask, fr'SIDS_CL_{str(year)[-2:]}_37.shp')
        shp_gdf, sindex = build_vector_spatial_index(shp_mask, tif_crs)

        for tif_path in list_tif:
            tif_name = os.path.split(tif_path)[-1]
            tif_valid = os.path.join(path_base, fr'extract_connected_patches\{year}', tif_name)
            os.makedirs(os.path.dirname(tif_valid), exist_ok=True)

            extract_connected_patches(
                tif_path=tif_path,
                shp_gdf=shp_gdf,
                sindex=sindex,
                output_tif=tif_valid
            )


if __name__ == '__main__':
    main()