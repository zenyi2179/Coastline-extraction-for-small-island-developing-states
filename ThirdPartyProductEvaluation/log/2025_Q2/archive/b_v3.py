import os
import arcpy
import rasterio
import numpy as np
import geopandas as gpd
from shapely.geometry import shape
from rasterio.features import shapes
from scipy.ndimage import label
from pathlib import Path

# 设置工作环境
arcpy.env.overwriteOutput = True


def select_valid_polygons(valid_pixel_shp: str, country_shp: str, output_shp: str) -> None:
    """
    按位置选择有效的像素多边形，并导出符合条件的结果。

    参数：
    valid_pixel_shp (str)：有效像素矢量文件路径。
    country_shp (str)：国家边界矢量文件路径。
    output_shp (str)：筛选后导出的矢量文件路径。
    """
    try:
        # 创建输出目录（如果不存在）
        os.makedirs(os.path.dirname(output_shp), exist_ok=True)

        # 按位置选择中心点在国家边界内的有效像素
        selected_layer = arcpy.management.SelectLayerByLocation(
            in_layer=[valid_pixel_shp],
            overlap_type="INTERSECT",
            select_features=country_shp,
            search_distance="200 Meters",
            selection_type="NEW_SELECTION"
        )

        # 导出符合条件的多边形
        arcpy.conversion.ExportFeatures(in_features=selected_layer, out_features=output_shp)

        # 清除选择
        arcpy.management.SelectLayerByAttribute(selected_layer, "CLEAR_SELECTION")

        print(f"- 有效多边形已导出至：{output_shp}")
    except Exception as e:
        print(f"警告：选择有效多边形时出错 - {str(e)}")


def tif_to_merged_regions_shp(input_tif: str, output_shp: str, threshold: float = 0.0) -> None:
    """
    将.tif中值大于指定阈值的连通区域合并为一个或多个面，并保存为shapefile。

    参数:
        input_tif (str): 输入的.tif文件路径。
        output_shp (str): 输出的.shp文件路径。
        threshold (float): 像元阈值，大于此值的区域将被合并为矢量面。
    """
    try:
        # 创建输出目录（如果不存在）
        os.makedirs(os.path.dirname(output_shp), exist_ok=True)

        with rasterio.open(input_tif) as src:
            data = src.read(1)  # 读取第一个波段
            transform = src.transform
            crs = src.crs

            # 生成二值掩码
            binary_mask = (data > threshold).astype(np.uint8)

            # 连通区域标记
            labeled_array, num_features = label(binary_mask)

            if num_features > 0:
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
            else:
                print(f"无有效矢量区域，未生成输出文件")
    except Exception as e:
        print(f"警告：处理栅格数据时出错 - {str(e)}")


def read_txt_to_list(file_path: str) -> list[str]:
    """读取文本文件内容并返回一个列表"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        print(f"错误：读取文件 {file_path} 失败 - {str(e)}")
        return []


def get_files_absolute_paths(folder_path: str, suffix: str = None) -> list[str]:
    """
    获取指定文件夹下所有指定后缀的文件的绝对路径名称。

    参数:
        folder_path (str): 指定文件夹的路径。
        suffix (str): 文件后缀（可选），如 '.shp'。如果不指定，则获取所有文件的路径。
    """
    if not os.path.exists(folder_path):
        print(f"警告：文件夹 {folder_path} 不存在")
        return []

    return [
        os.path.abspath(os.path.join(root, file))
        for root, _, files in os.walk(folder_path)
        for file in files
        if suffix is None or file.endswith(suffix)
    ]


def main():
    """主函数，执行整个处理流程"""
    # 项目根路径
    project_root = Path(r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData")

    # 输入数据路径
    sids_file = "SIDS_37.txt"
    sids_boundary_dir = project_root / "j_SIDS_Polygon"

    # 输出数据路径
    temp_dir = project_root / "temp"
    draft_dir = temp_dir / "_draft"
    tif_input_dir = temp_dir / "a_tif_GeeData"
    shp_output_dir = temp_dir / "b_shp_GeeData"

    # # 处理的年份和国家代码
    years = ['2010', '2015']
    # sids_list = read_txt_to_list(str(sids_file))

    # 使用示例数据进行测试
    # years = ['2010']  # 示例仅处理 2010 年
    sids_list = ['ATG']  # 示例仅处理国家代码为 ATG 的国家

    # 遍历年份和国家代码
    for year in years:
        for sids in sids_list:
            print(f"\n处理 {sids} {year} 数据...")

            # 检查国家边界文件
            country_shp = sids_boundary_dir / sids / f"{sids}_{year[-2:]}.shp"
            if not country_shp.exists():
                print(f"跳过 {sids}：边界文件 {country_shp} 不存在")
                continue

            # 获取TIF文件列表
            tif_folder = tif_input_dir / sids / year
            tif_files = get_files_absolute_paths(str(tif_folder), suffix='.tif')

            if not tif_files:
                print(f"跳过 {sids} {year}：未找到TIF文件")
                continue

            # 处理每个TIF文件
            for tif_file in tif_files:
                try:
                    tif_name = os.path.splitext(os.path.basename(tif_file))[0]

                    # 临时输出文件路径
                    temp_shp = draft_dir / f"{tif_name}.shp"

                    # 将.tif文件中的连通区域转换为矢量面
                    tif_to_merged_regions_shp(
                        input_tif=str(tif_file),
                        output_shp=str(temp_shp)
                    )

                    # 最终输出文件路径
                    out_shp = shp_output_dir / sids / year / f"{tif_name}.shp"

                    # 按位置选择有效的像素多边形
                    if os.path.exists(temp_shp):
                        select_valid_polygons(
                            valid_pixel_shp=str(temp_shp),
                            country_shp=str(country_shp),
                            output_shp=str(out_shp)
                        )
                    else:
                        print(f"警告：临时文件 {temp_shp} 不存在，跳过选择步骤")
                except Exception as e:
                    print(f"错误：处理文件 {tif_file} 时出错 - {str(e)}")


if __name__ == "__main__":
    main()
