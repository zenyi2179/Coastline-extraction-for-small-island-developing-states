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


def read_txt_to_list(file_path: str) -> list[str]:
    """读取文本文件内容并返回一个列表"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        print(f"错误：读取文件 {file_path} 失败 - {str(e)}")
        return []

def get_files_absolute_paths(folder_path, suffix=None):
    """
    获取指定文件夹下所有指定后缀的文件的绝对路径名称

    :param folder_path: 指定文件夹的路径
    :param suffix: 文件后缀（可选），如 '.shp'。如果不指定，则获取所有文件的路径
    :return: 指定后缀的文件的绝对路径名称列表
    """
    files_paths = []
    # 遍历指定文件夹
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 如果指定了后缀，则判断文件后缀是否匹配
            if suffix is None or file.endswith(suffix):
                # 获取文件的绝对路径并添加到列表中
                files_paths.append(os.path.abspath(os.path.join(root, file)))
    return files_paths

def main():# 初始化处理的国家和年份
    vector_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\c_shp_fixed\ATG\2010\ATG_62W17Nlb.shp"
    # 新建文件夹
    tif_fixed = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\d_tif_fixed\ATG_62W17Nlb.tif'
    os.makedirs(os.path.dirname(tif_fixed), exist_ok=True)

    # 样板tif
    reference_raster = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\a_tif_GeeData\ATG\2010\ATG_62W16Nlu.tif"

    # 执行转换
    vector_to_raster(vector_path, tif_fixed, reference_raster, value=20)


if __name__ == '__main__':
    main()
