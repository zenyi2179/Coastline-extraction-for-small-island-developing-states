import arcpy
import rasterio
import numpy as np
import geopandas as gpd
from shapely.geometry import shape
from rasterio.features import shapes


def export_raster_to_shp(input_path, output_shp_path, threshold=20):
    """
    从栅格文件中提取像元值大于指定阈值的区域并导出为shp文件。

    参数：
        input_path (str): 输入栅格文件路径
        output_shp_path (str): 导出shp文件路径
        threshold (int): 提取的阈值，默认值为20
    """
    try:
        # 打开输入栅格文件
        with rasterio.open(input_path) as src:
            # 读取第一个波段的数据
            data = src.read(1)
            # 创建布尔掩膜，找到大于阈值的像元
            mask = data > threshold
            # 将符合条件的区域转换为几何形状
            shapes_gen = shapes(data, mask=mask, transform=src.transform)
            # 提取几何信息和属性信息
            geometries = [
                {"geometry": shape(geom), "value": value}
                for geom, value in shapes_gen
                if value > threshold
            ]

            # 转换为GeoDataFrame
            gdf = gpd.GeoDataFrame(geometries, crs=src.crs)
            # 将结果保存为shp文件
            gdf.to_file(output_shp_path, driver="ESRI Shapefile")

        print(f"成功导出符合条件的区域为shp文件：{output_shp_path}")

    except Exception as e:
        print(f"导出过程中出错: {e}")


def select_valid_shp(origin_shp, intersect_shp, output_shp):  # 模型5

    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    # Process: 按位置选择图层 (按位置选择图层) (management)
    select_layer = arcpy.management.SelectLayerByLocation(in_layer=[origin_shp], overlap_type="INTERSECT",
                                                          select_features=intersect_shp)

    # Process: 导出要素 (导出要素) (conversion)
    arcpy.conversion.ExportFeatures(in_features=select_layer, out_features=output_shp)
    print(fr"导出筛选后的shp：{output_shp}.")


def select_valid_range(gee_tif, mndwi_20, extract_shp, select_shp):
    export_raster_to_shp(input_path=gee_tif, output_shp_path=mndwi_20)
    select_valid_shp(origin_shp=extract_shp, intersect_shp=mndwi_20, output_shp=select_shp)


# 使用示例
if __name__ == '__main__':
    gee_tif = r'E:\_GoogleDrive\SouthChinaSea\111E16Nru_MNDWI.tif'
    mndwi_20 = r'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\MNDWI_20.shp'
    extract_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Landsat_output\YY_2015\111E16Nru_extract.shp"
    select_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Select\111E16Nru_select.shp"
    select_valid_range(gee_tif, mndwi_20, extract_shp, select_shp)
