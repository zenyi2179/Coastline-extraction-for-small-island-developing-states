import os
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from shapely.geometry import mapping


def vector_to_raster(vector_path, raster_path, reference_raster, value=10):
    """
    将矢量文件转换为栅格，并赋值为指定的值。

    :param vector_path: 输入矢量文件路径 (Shapefile)
    :param raster_path: 输出栅格文件路径
    :param reference_raster: 参考栅格文件路径，仅用于获取像元大小信息
    :param value: 转换后的栅格像元值
    """
    try:
        # 读取矢量数据
        vector_data = gpd.read_file(vector_path)

        # 获取矢量数据的 CRS 和几何边界
        crs = vector_data.crs
        bounds = vector_data.total_bounds  # 获取矢量数据的边界框

        # 读取参考栅格的像元大小信息
        with rasterio.open(reference_raster) as ref_src:
            pixel_size = ref_src.res[0]  # 假设像元大小在 x 和 y 方向相同

        # 计算输出栅格的宽度和高度
        width = int((bounds[2] - bounds[0]) / pixel_size)
        height = int((bounds[3] - bounds[1]) / pixel_size)

        # 计算仿射变换矩阵
        transform = rasterio.Affine(pixel_size, 0, bounds[0], 0, -pixel_size, bounds[3])

        # 获取矢量文件的几何数据
        geometries = vector_data.geometry

        # 创建栅格化的图像
        rasterized_data = rasterize(
            [(mapping(geometry), value) for geometry in geometries],
            out_shape=(height, width),
            transform=transform,
            fill=0,  # 设置非矢量区域的值为 0
            dtype='uint8'
        )

        # 确保输出文件的目录存在
        output_dir = os.path.dirname(raster_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 保存为输出栅格文件
        with rasterio.open(
                raster_path,
                'w',
                driver='GTiff',
                height=height,
                width=width,
                count=1,
                dtype=rasterized_data.dtype,
                crs=crs,
                transform=transform,
                nodata=0  # 设置空值为 0
        ) as dst:
            dst.write(rasterized_data, 1)

        print(f"Tif saved as: {raster_path}")

    except Exception as e:
        print(f"发生错误: {e}")


def main():
    # 全 37 国家
    sids_cou_list = [
"DMA",
"DOM",
"FJI",
"FSM",
"GNB",
"GRD",
"GUY",
"HTI",
"JAM",
"KIR",
"KNA",
"LCA",
"MDV",
"MHL",
"MUS",
"NRU",
"PLW",
"PNG",
"SGP",
"SLB",
"STP",
"SUR",
"SYC",
"TLS",
"TON",
"TTO",
"TUV",
"VCT",
"VUT",
"WSM",
                     ]
    # sids_cou_list = ['ATG']
    for sids_cou in sids_cou_list:
        for year in [2015]:
            # 设置文件路径
            vector_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\g_QGIS\c_SIDS_no_holes\{sids_cou}\{sids_cou}_{str(year)[-2:]}.shp"
            # 新建文件夹
            os.makedirs(name=fr"E:\_OrderingProject\F_IslandsBoundaryChange\g_QGIS\h_SIDS_Tif\{sids_cou}", exist_ok=True)
            raster_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\h_SIDS_Tif\{sids_cou}\{sids_cou}_{str(year)[-2:]}.tif'

            # 样板tif
            reference_raster = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\bandInterpolation\_zoom.tif"

            # 执行转换
            try:
                vector_to_raster(vector_path, raster_path, reference_raster, value=10)
            except Exception as e:
                print(sids_cou, e)
                pass

if __name__ == '__main__':
    main()
