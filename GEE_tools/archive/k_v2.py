# -*- coding:utf-8 -*-
"""
作者：23242
日期：2024年09月18日
"""
from dea_tools.spatial import subpixel_contours
import rasterio
import xarray as xr
import rioxarray  # Import rioxarray to access rio features
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString


# 定义函数用于输出组件的首尾点，并封闭线段
def process_multilinestring(geometry):
    if isinstance(geometry, MultiLineString):
        for i, component in enumerate(geometry.geoms):  # 使用 .geoms 来迭代 MultiLineString 中的每个 LineString
            coords = list(component.coords)
            start_point = coords[0]
            end_point = coords[-1]
            # # 输出每个组件的首尾点
            # print(f"Component {i + 1}:")
            # print(f"  Start Point (Index: 0): Longitude: {start_point[0]}, Latitude: {start_point[1]}")
            # print(f"  End Point (Index: {len(coords) - 1}): Longitude: {end_point[0]}, Latitude: {end_point[1]}")
            # print('-' * 50)

            # 检查首尾点是否一致，不一致则封闭
            if start_point != end_point:
                # print(f"  Closing Component {i + 1}...")
                coords.append(start_point)  # 封闭
            # else:
            #     print(f"  Component {i + 1} is already closed.")
            # print('-' * 50)
            # 返回封闭后的 LineString
            yield LineString(coords)
    else:
        print("Geometry is not MultiLineString.")
        return None


def fix_subpixel_extraction(input_geojson, output_geojson):
    # 读取 GeoJSON 文件
    # input_geojson = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\k_subPixelWaterlineExtraction\UID_114940_subpixel.geojson"
    gdf = gpd.read_file(input_geojson)

    # 处理所有要素的几何
    for idx, row in gdf.iterrows():
        geometry = row['geometry']
        # print(f"Processing Feature {idx + 1}...")
        if isinstance(geometry, MultiLineString):
            closed_components = list(process_multilinestring(geometry))  # 封闭每个组件
            # 创建封闭后的 MultiLineString 几何
            closed_multilinestring = MultiLineString(closed_components)
            gdf.at[idx, 'geometry'] = closed_multilinestring  # 更新封闭后的几何
        else:
            print(f"Feature {idx + 1} is not a MultiLineString.")

    # 输出结果
    # output_geojson = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\k_subPixelWaterlineExtraction\UID_114940_subpixel_closed.geojson"
    gdf.to_file(output_geojson, driver="GeoJSON")
    print(f"Subpixel_closed MultiLineString output: {output_geojson}")


def subpixel_extraction(input_tif, z_values, subpixel_tif):
    # 定义 TIFF 文件路径
    # tif_file = r'E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE_valid\ISID_224209_zoom_ND_extract.tif'
    # subpixel_tif = fr"E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE\ISID_224209_zoom_ND_extract.geojson"
    tif_file = input_tif

    # 使用 rasterio 读取 TIFF 文件
    with rasterio.open(tif_file) as src:
        # 读取栅格数据
        raster_data = src.read(1)  # 读取第一个波段

        # 获取 TIFF 文件的元数据（如坐标系和变换信息）
        transform = src.transform
        crs = src.crs

        # 创建坐标数组
        height, width = raster_data.shape
        x_coords = [transform * (col, 0) for col in range(width)]  # 计算X轴坐标
        y_coords = [transform * (0, row) for row in range(height)]  # 计算Y轴坐标

        # 提取X和Y坐标
        x_coords = [x[0] for x in x_coords]
        y_coords = [y[1] for y in y_coords]

        # 将数据转换为 xarray DataArray
        data_array = xr.DataArray(
            raster_data,
            coords=[y_coords, x_coords],  # 设置坐标
            dims=["y", "x"],  # 定义维度名称
            attrs={
                'crs': str(crs),  # 设置坐标系
                'transform': transform  # 设置变换信息
            }
        )

    # 使用 rioxarray 设置 CRS
    data_array = data_array.rio.write_crs("EPSG:4326", inplace=True)

    # 打印 DataArray 的信息
    # print(data_array)


    # 未修复前
    subpixel_tif_temp = subpixel_tif.split('.geojson')[0] + '_temp.geojson'
    subpixel_contours(da=data_array, z_values=z_values, attribute_df=None, output_path=subpixel_tif_temp)
    # 修复闭合线段
    fix_subpixel_extraction(subpixel_tif_temp, subpixel_tif)


if __name__ == '__main__':
    # 定义 TIFF 文件路径
    tif_file = r'E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE_valid\ISID_224209_zoom_ND_extract.tif'
    subpixel_tif = fr"E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE\ISID_224209_zoom_ND_extract.geojson"
    subpixel_extraction(input_tif=tif_file, z_values=0, subpixel_tif=subpixel_tif)

# E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE
# E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\ISID_224209.tif

# pip install --upgrade shapely odc-geo

# #    D:\ArcGISPro3\Pro\bin\Python\envs\arcgispro-py3\python.exe -m pip install --user --upgrade fiona -i https://pypi.doubanio.com/simple/
# , output_path=fr"E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE"