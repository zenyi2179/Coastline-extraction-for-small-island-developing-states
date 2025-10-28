import rasterio
import numpy as np
import geopandas as gpd
from shapely.geometry import shape
from rasterio.features import shapes
from scipy.ndimage import label


def tif_to_merged_regions_shp(input_tif: str, output_shp: str, threshold: float = 0.0):
    """
    将.tif中值大于指定阈值的连通区域合并为一个或多个面，并保存为shapefile。

    参数:
        input_tif (str): 输入的.tif文件路径。
        output_shp (str): 输出的.shp文件路径。
        threshold (float): 像元阈值，大于此值的区域将被合并为矢量面。
    """
    with rasterio.open(input_tif) as src:
        data = src.read(1)
        transform = src.transform
        crs = src.crs

        # 生成二值掩码（1 表示值 > 阈值）
        binary_mask = (data > threshold).astype(np.uint8)

        # 连通区域标记
        labeled_array, num_features = label(binary_mask)

        print(f"检测到 {num_features} 个连通区域")

        # 转换为矢量面
        shapes_gen = shapes(labeled_array, mask=binary_mask, transform=transform)
        geometries = [
            {"geometry": shape(geom), "properties": {"id": int(value)}}
            for geom, value in shapes_gen
            if value != 0
        ]

        # 构建 GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(geometries)
        gdf.crs = crs

        # 保存为 Shapefile
        gdf.to_file(output_shp, driver='ESRI Shapefile')

        print(f"成功输出为 shapefile：{output_shp}")

tif_to_merged_regions_shp(
    input_tif=r"E:\_OrderingProject\draft0621\ATG_62W17Nlb.tif",
    output_shp=r"E:\_OrderingProject\draft0621\ATG_62W17Nlb_regions.shp",
)
