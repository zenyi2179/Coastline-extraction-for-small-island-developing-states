from dea_tools.spatial import subpixel_contours
import rasterio
import xarray as xr
import rioxarray
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
import os


# 定义函数用于处理 MultiLineString，并封闭线段和进行坐标偏移
def process_multilinestring(geometry, x_offset, y_offset):
    """
    处理 MultiLineString，进行坐标偏移并封闭线段。

    :param geometry: 输入的 MultiLineString 对象
    :param x_offset: X 方向偏移量
    :param y_offset: Y 方向偏移量
    :yield: 处理后的 LineString 对象
    """
    if isinstance(geometry, MultiLineString):
        # 遍历 MultiLineString 中的每个组件
        for component in geometry.geoms:
            coords = list(component.coords)  # 获取坐标列表
            start_point = coords[0]          # 线段起点
            end_point = coords[-1]           # 线段终点

            # 添加偏移量到每个坐标
            coords = [(x + x_offset, y + y_offset) for x, y in coords]

            # 如果首尾点不同，则添加首点以封闭线段
            if start_point != end_point:
                coords.append(coords[0])  # 闭合线段
            yield LineString(coords)      # 返回封闭后的 LineString
    else:
        print("Geometry is not MultiLineString.")
        return None


# 定义函数用于修复子像素提取，并将结果保存为 GeoJSON
def fix_subpixel_extraction(input_geojson, output_geojson, x_offset, y_offset):
    """
    处理 MultiLineString 几何对象，并对其应用坐标偏移，保存为 GeoJSON。

    :param input_geojson: 输入的 GeoJSON 文件路径
    :param output_geojson: 输出的 GeoJSON 文件路径
    :param x_offset: X 方向偏移量
    :param y_offset: Y 方向偏移量
    """
    gdf = gpd.read_file(input_geojson)  # 读取输入的 GeoJSON
    for idx, row in gdf.iterrows():
        geometry = row['geometry']  # 获取几何对象
        # 检查几何是否为 MultiLineString
        if isinstance(geometry, MultiLineString):
            closed_components = list(process_multilinestring(geometry, x_offset, y_offset))
            closed_multilinestring = MultiLineString(closed_components)
            gdf.at[idx, 'geometry'] = closed_multilinestring  # 更新几何对象
        else:
            print(f"Feature {idx + 1} is not a MultiLineString.")
    gdf.to_file(output_geojson, driver="GeoJSON")  # 保存到输出文件
    print(f"Subpixel_closed MultiLineString output: {output_geojson}")


# 定义函数进行子像素提取，并生成 GeoJSON
def subpixel_extraction(input_tif, z_values, subpixel_tif):
    """
    从 TIF 文件进行子像素提取，并生成 GeoJSON。

    :param input_tif: 输入的 TIF 文件路径
    :param z_values: 提取等高线的 Z 值
    :param subpixel_tif: 输出的 GeoJSON 文件路径
    """
    tif_file = input_tif
    with rasterio.open(tif_file) as src:
        raster_data = src.read(1)       # 读取栅格数据
        transform = src.transform       # 获取仿射变换
        crs = src.crs                   # 获取坐标参考系
        height, width = raster_data.shape

        # 计算偏移量（半个像素的长度）
        x_offset = transform[0] / 2
        y_offset = transform[4] / 2

        # 创建 x, y 坐标数组
        x_coords = [transform * (col, 0) for col in range(width)]
        y_coords = [transform * (0, row) for row in range(height)]
        x_coords = [x[0] for x in x_coords]
        y_coords = [y[1] for y in y_coords]

        # 将栅格数据转换为 xarray DataArray
        data_array = xr.DataArray(
            raster_data,
            coords=[y_coords, x_coords],
            dims=["y", "x"],
            attrs={
                'crs': str(crs),
                'transform': transform
            }
        )

    # 写入坐标参考系为 EPSG:4326
    data_array = data_array.rio.write_crs("EPSG:4326", inplace=True)

    # 创建临时的 GeoJSON 文件
    subpixel_tif_temp = subpixel_tif.split('.geojson')[0] + '_temp.geojson'

    # 进行子像素等高线提取
    # subpixel_contours(da=data_array, z_values=z_values, attribute_df=None, output_path=subpixel_tif_temp)
    subpixel_contours(da=data_array, z_values=z_values, attribute_df=None, output_path=subpixel_tif)

    # # 调用修复函数，应用坐标偏移并保存最终结果
    # fix_subpixel_extraction(subpixel_tif_temp, subpixel_tif, x_offset, y_offset)

def main():
    sids_cou_list = [
        "MUS",
    ]
    for sids_cou in sids_cou_list:
        for year in [2000, 2010, 2020]:
            input_tif = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\h_SIDS_Tif\{sids_cou}\{sids_cou}_{str(year)[-2:]}.tif'  # 新建文件夹
            os.makedirs(name=fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Geojson\{sids_cou}",
                        exist_ok=True)
            output_json = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Geojson\{sids_cou}\{sids_cou}_{str(year)[-2:]}.geojson"

            subpixel_extraction(input_tif=input_tif, z_values=0, subpixel_tif=output_json)


if __name__ == '__main__':
    main()
