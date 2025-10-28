from dea_tools.spatial import subpixel_contours
import rasterio
import numpy as np
import xarray as xr
import rioxarray
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from rasterio import Affine


def add_zero_buffer(input_tif, output_tif, buffer_size=1):
    """
    为指定 GeoTIFF 文件添加一圈值为 0 的像元边界。

    参数:
    input_tif (str): 输入的 GeoTIFF 文件路径
    output_tif (str): 输出的 GeoTIFF 文件路径
    buffer_size (int): 缓冲区大小，默认为 1，表示添加一圈像元
    """
    with rasterio.open(input_tif) as src:
        # 复制源栅格元数据并更新宽度、高度和仿射变换以扩展边界
        profile = src.profile.copy()
        width, height = src.width, src.height
        new_width = width + 2 * buffer_size
        new_height = height + 2 * buffer_size
        new_transform = src.transform * Affine.translation(-buffer_size, -buffer_size)

        # 更新栅格元数据
        profile.update({'width': new_width, 'height': new_height, 'transform': new_transform})

        # 创建新栅格数据数组，初始值为 0
        new_data = np.zeros((src.count, new_height, new_width), dtype=src.dtypes[0])

        # 将原始图像数据读取到数组并放置在新数据的中央
        original_data = src.read()
        new_data[:, buffer_size:buffer_size + height, buffer_size:buffer_size + width] = original_data

        # 将新数据写入到输出文件
        with rasterio.open(output_tif, 'w', **profile) as dst:
            dst.write(new_data)

    print(f'Peripheral buffering has been successfully added: {output_tif}')


def process_multilinestring(geometry, x_offset, y_offset):
    """
    对 MultiLineString 进行坐标偏移并封闭线段。

    参数:
    geometry (MultiLineString): 输入的 MultiLineString 对象
    x_offset (float): X 方向偏移量
    y_offset (float): Y 方向偏移量

    产出:
    Iterator[LineString]: 处理后的封闭 LineString 对象
    """
    if isinstance(geometry, MultiLineString):
        for component in geometry.geoms:
            # 获取坐标列表并应用坐标偏移
            coords = [(x + x_offset, y + y_offset) for x, y in component.coords]

            # 如果首尾点不同则添加起点，以封闭线段
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            yield LineString(coords)  # 返回封闭的 LineString
    else:
        print("The input geometry object is not a MultiLineString.")


def fix_subpixel_extraction(input_geojson, output_geojson, x_offset, y_offset):
    """
    处理 MultiLineString 对象，应用坐标偏移并将结果保存为 GeoJSON。

    参数:
    input_geojson (str): 输入 GeoJSON 文件路径
    output_geojson (str): 输出 GeoJSON 文件路径
    x_offset (float): X 方向偏移量
    y_offset (float): Y 方向偏移量
    """
    gdf = gpd.read_file(input_geojson)  # 读取 GeoJSON 文件
    for idx, row in gdf.iterrows():
        geometry = row['geometry']
        if isinstance(geometry, MultiLineString):
            # 应用坐标偏移和封闭处理
            closed_components = list(process_multilinestring(geometry, x_offset, y_offset))
            gdf.at[idx, 'geometry'] = MultiLineString(closed_components)
        else:
            print(f"Feature {idx + 1} is not a MultiLineString.")

    # 将处理后的几何保存为新的 GeoJSON 文件
    gdf.to_file(output_geojson, driver="GeoJSON")
    print(f"Generated processed GeoJSON file: {output_geojson}")


def subpixel_extraction(input_tif, z_values, subpixel_tif):
    """
    从栅格文件中进行子像素提取，并生成 GeoJSON。

    参数:
    input_tif (str): 输入的 TIF 文件路径
    z_values (float): 等高线提取的 Z 值
    subpixel_tif (str): 输出的 GeoJSON 文件路径
    """
    # 创建临时文件以添加外围缓冲
    temp_zero_buffer = r'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Filtering\temp_zero_buffer.tif'
    add_zero_buffer(input_tif=input_tif, output_tif=temp_zero_buffer, buffer_size=1)

    # 使用带缓冲的栅格数据
    with rasterio.open(temp_zero_buffer) as src:
        raster_data = src.read(1)
        transform = src.transform
        crs = src.crs
        height, width = raster_data.shape

        # 计算坐标偏移量
        x_offset = transform[0] / 2
        y_offset = transform[4] / 2

        # 创建 x 和 y 坐标数组
        x_coords = [transform * (col, 0) for col in range(width)]
        y_coords = [transform * (0, row) for row in range(height)]
        x_coords = [x[0] for x in x_coords]
        y_coords = [y[1] for y in y_coords]

        # 将栅格数据转换为 xarray DataArray，并写入坐标参考系为 EPSG:4326
        data_array = xr.DataArray(
            raster_data,
            coords=[y_coords, x_coords],
            dims=["y", "x"],
            attrs={'crs': str(crs), 'transform': transform}
        )
        data_array = data_array.rio.write_crs("EPSG:4326", inplace=True)

    # 临时 GeoJSON 文件路径
    subpixel_tif_temp = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Geojson\temp.geojson"

    # 进行子像素等高线提取
    subpixel_contours(da=data_array, z_values=z_values, attribute_df=None, output_path=subpixel_tif_temp)

    # 修复子像素提取结果并保存为最终的 GeoJSON
    fix_subpixel_extraction(subpixel_tif_temp, subpixel_tif, x_offset, y_offset)


if __name__ == '__main__':
    # 子像素提取执行，生成 GeoJSON 文件
    # subpixel_extraction(
    #     input_tif=r'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Filtering\114E22Nlb_filter.tif',
    #     z_values=10,
    #     subpixel_tif=r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Geojson\114E22Nlb_extract.geojson"
    # )
    subpixel_extraction(
        input_tif=r'C:\Users\23242\Desktop\draft1108\unet_resnet_2020_Band_1.tif',
        z_values=10,
        subpixel_tif=r'C:\Users\23242\Desktop\draft1108\unet_resnet_2020_Band_1.geojson'
    )
