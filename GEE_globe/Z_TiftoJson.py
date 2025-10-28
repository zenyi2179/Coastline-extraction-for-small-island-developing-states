from dea_tools.spatial import subpixel_contours
import rasterio
import numpy as np
import xarray as xr
import rioxarray
import os
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from rasterio import Affine


# 添加默认条带用于封闭
def add_zero_buffer(input_tif, output_tif, buffer_size=1):
    """
    给指定 GeoTIFF 文件的边界添加一圈栅格值为 0 的像元值。

    参数:
    input_tif (str): 输入的 GeoTIFF 文件路径
    output_tif (str): 输出的 GeoTIFF 文件路径
    buffer_size (int): 要添加的像元缓冲大小，默认值为 1（即一圈像元）
    """
    # 打开输入的 GeoTIFF 文件
    with rasterio.open(input_tif) as src:
        # 获取输入栅格的元数据
        profile = src.profile.copy()

        # 获取原始图像的宽度和高度
        width, height = src.width, src.height

        # 计算新的宽度和高度
        new_width = width + 2 * buffer_size
        new_height = height + 2 * buffer_size

        # 创建新的仿射变换，扩展边界
        new_transform = src.transform * Affine.translation(-buffer_size, -buffer_size)

        # 更新元数据以反映新的宽度、高度和变换
        profile.update({
            'width': new_width,
            'height': new_height,
            'transform': new_transform
        })

        # 创建一个新的数组，初始化为 0，表示边界缓冲的像元值为 0
        new_data = np.zeros((src.count, new_height, new_width), dtype=src.dtypes[0])

        # 读取原始图像数据
        original_data = src.read()

        # 将原始图像放置在新的数据中央
        new_data[:, buffer_size:buffer_size + height, buffer_size:buffer_size + width] = original_data

        # 写入新的 GeoTIFF 文件
        with rasterio.open(output_tif, 'w', **profile) as dst:
            dst.write(new_data)

    print(f'Periphery of fusion boundary: {output_tif}.')


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
            start_point = coords[0]  # 线段起点
            end_point = coords[-1]  # 线段终点

            # 添加偏移量到每个坐标
            coords = [(x + x_offset, y + y_offset) for x, y in coords]

            # 如果首尾点不同，则添加首点以封闭线段
            if start_point != end_point:
                coords.append(coords[0])  # 闭合线段
            yield LineString(coords)  # 返回封闭后的 LineString
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
    # 添加外围封闭栅格圈
    temp_zero_buffer = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Filtering\temp_zero_buffer.tif'
    add_zero_buffer(input_tif=input_tif, output_tif=temp_zero_buffer, buffer_size=1)

    tif_file = temp_zero_buffer
    with rasterio.open(tif_file) as src:
        raster_data = src.read(1)  # 读取栅格数据
        transform = src.transform  # 获取仿射变换
        crs = src.crs  # 获取坐标参考系
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
    subpixel_tif_temp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Geojson\temp.geojson"

    # 进行子像素等高线提取
    subpixel_contours(da=data_array, z_values=z_values, attribute_df=None, output_path=subpixel_tif_temp)
    # subpixel_contours(da=data_array, z_values=z_values, attribute_df=None, output_path=subpixel_tif)

    # 调用修复函数，应用坐标偏移并保存最终结果
    fix_subpixel_extraction(subpixel_tif_temp, subpixel_tif, x_offset, y_offset)


def main():
    # 初始 57 国家
    sids_cou_list = ["BMU",
                     "KNA",
                     "MSR",
                     "NRU",
                     "BRB",
                     "DMA",
                     "GUM",
                     "NIU",
                     "SGP",
                     "VCT",
                     "AIA",
                     "CYM",
                     "VGB",
                     "VIR",
                     "ABW",
                     "ASM",
                     "CUW",
                     "GRD",
                     "LCA",
                     "MTQ",
                     "SXM",
                     "ATG",
                     "GLP",
                     "STP",
                     "TCA",
                     "COM",
                     "WSM",
                     "TTO",
                     "MUS",
                     "TUV",
                     "PLW",
                     "MNP",
                     "JAM",
                     "PRI",
                     "CPV",
                     "TLS",
                     "TON",
                     "COK",
                     "BLZ",
                     "GNB",
                     "SYC",
                     "HTI",
                     "DOM",
                     "VUT",
                     "MDV",
                     "NCL",
                     "KIR",
                     "MHL",
                     "FSM",
                     "FJI",
                     "SUR",
                     "SLB",
                     "BHS",
                     "CUB",
                     "GUY",
                     "PYF",
                     "PNG",
                     ]
    # 去掉 KIR FJI PYF
    sids_cou_list = ["BMU",
                     "KNA",
                     "MSR",
                     "NRU",
                     "BRB",
                     "DMA",
                     "GUM",
                     "NIU",
                     "SGP",
                     "VCT",
                     "AIA",
                     "CYM",
                     "VGB",
                     "VIR",
                     "ABW",
                     "ASM",
                     "CUW",
                     "GRD",
                     "LCA",
                     "MTQ",
                     "SXM",
                     "ATG",
                     "GLP",
                     "STP",
                     "TCA",
                     "COM",
                     "WSM",
                     "TTO",
                     "MUS",
                     "TUV",
                     "PLW",
                     "MNP",
                     "JAM",
                     "PRI",
                     "CPV",
                     "TLS",
                     "TON",
                     "COK",
                     "BLZ",
                     "GNB",
                     "SYC",
                     "HTI",
                     "DOM",
                     "VUT",
                     "MDV",
                     "NCL",
                     "MHL",
                     "FSM",
                     "SUR",
                     "SLB",
                     "BHS",
                     "CUB",
                     "GUY",
                     "PNG",
                     ]
    sids_cou_list = [
                     "GUY",
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
    # sids_cou_list = [
    #     "MUS",
    # ]
    # for sids_cou in sids_cou_list:
    #     # for year in [2000, 2010, 2020]:
    #     for year in [2010]:
    #         # input_tif = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\h_SIDS_Tif\{sids_cou}\{sids_cou}_{str(year)[-2:]}.tif'  # 新建文件夹
    #         input_tif = fr"C:\Users\23242\Desktop\check\250412\{sids_cou}\{sids_cou}_{str(year)[-2:]}_2_2.tif"
    #         os.makedirs(name=fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Geojson\{sids_cou}",
    #                     exist_ok=True)
    #         output_json = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Geojson\{sids_cou}\{sids_cou}_{str(year)[-2:]}_2_2.geojson"
    #
    #         subpixel_extraction(input_tif=input_tif, z_values=10, subpixel_tif=output_json)
