from shapely.geometry import Polygon, MultiPolygon
import os
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from shapely.geometry import mapping


def fix_holes_in_shp(input_shp: str, output_shp: str, min_area: float = 0.0) -> None:
    """
    修复Shapefile面要素中的空洞。

    参数:
        input_shp (str): 输入Shapefile路径
        output_shp (str): 输出Shapefile路径
        min_area (float): 保留的最小空洞面积，小于此面积的空洞将被填充
    """
    # 读取Shapefile
    gdf = gpd.read_file(input_shp)

    # 处理每个几何对象
    fixed_geometries = []
    for geom in gdf.geometry:
        if geom.geom_type == 'Polygon':
            # 处理单个多边形
            exterior = geom.exterior
            interiors = [interior for interior in geom.interiors if interior.area > min_area]
            fixed_geom = Polygon(exterior, interiors)
            fixed_geometries.append(fixed_geom)
        elif geom.geom_type == 'MultiPolygon':
            # 处理多个多边形
            fixed_polygons = []
            for poly in geom.geoms:
                exterior = poly.exterior
                interiors = [interior for interior in poly.interiors if interior.area > min_area]
                fixed_poly = Polygon(exterior, interiors)
                fixed_polygons.append(fixed_poly)
            fixed_geom = MultiPolygon(fixed_polygons)
            fixed_geometries.append(fixed_geom)
        else:
            # 非面要素直接添加
            fixed_geometries.append(geom)

    # 更新几何列
    gdf.geometry = fixed_geometries

    # 保存结果
    gdf.to_file(output_shp)
    print(f"已修复空洞并保存至: {output_shp}")


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


def read_dbf_to_list(dbf_path, if_print=0):
    """
    读取 DBF 文件并将内容存储为二维列表。

    参数:
    dbf_path (str): DBF 文件的路径。
    if_print (int): 是否打印二维列表的开关，0表示不打印，1表示打印。

    返回:
    list_of_records (list): 二维列表，每个子列表代表一条记录。
    """
    list_of_records = []
    dbf = DBF(dbf_path, encoding='utf-8')  # 打开 DBF 文件并设置编码为 'utf-8'

    # 获取并打印 DBF 文件的字段名称，即表头
    # print("Field names:", [field.name for field in dbf.fields])

    # 遍历 DBF 文件中的每条记录
    for record in dbf:
        # 将每条记录的值转换为列表，并添加到二维列表中
        list_of_records.append(list(record.values()))

    # 根据 if_print 参数决定是否打印二维列表
    if if_print:
        print("Records list:")
        print(list_of_records)

    return list_of_records


def shp_tif_fix(year, sids, shp_file):
    # 修复几何
    shp_input = (
        fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\b_shp_GeeData"
        fr"\{sids}\{year}\{os.path.basename(shp_file)}")
    print(shp_input)
    shp_fixed = (
        fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\c_shp_fixed"
        fr"\{sids}\{year}\{os.path.basename(shp_file)}")
    os.makedirs(os.path.dirname(shp_fixed), exist_ok=True)
    fix_holes_in_shp(input_shp=shp_input, output_shp=shp_fixed)
    # 修复栅格
    tif_fixed = (
        fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\d_tif_fixed"
        fr"\{sids}\{year}\{os.path.splitext(os.path.basename(shp_file))[0]}.tif")
    reference_raster = (
        r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\a_tif_GeeData\ATG\2010\ATG_62W16Nlu.tif"
    )
    os.makedirs(os.path.dirname(tif_fixed), exist_ok=True)

    # 执行转换
    vector_to_raster(vector_path=shp_fixed, raster_path=tif_fixed, reference_raster=reference_raster, value=20)


def main():
    # 初始化处理的国家和年份
    list_year = ['2010', '2015', '2020']
    list_sids = read_txt_to_list(file_path=fr"SIDS_37.txt")

    for year in ['2010', '2015']:
        # for year in list_year:
        for sids in ['ATG']:
            # for sids in list_sids:
            # 示例使用
            path_folder = (
                fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp"
                fr"\b_shp_GeeData\{sids}\{year}")
            list_map_files = get_files_absolute_paths(path_folder, suffix=fr'.shp')
            for shp_file in list_map_files:
                try:
                    shp_tif_fix(
                        year=year,
                        sids=sids,
                        shp_file=shp_file
                    )
                except Exception as e:
                    pass


if __name__ == '__main__':
    main()
