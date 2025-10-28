#!/usr/bin/env python3
import math
import os
import tempfile
import time
from typing import Optional

import arcpy
import geopandas as gpd
import pandas as pd
from shapely.geometry import box


def create_aligned_grid(
        input_polyline: str,
        output_polygon: str,
        grid_size: float,
        block_step: float = 10.0,
) -> str:
    """创建对齐的方形格网并筛选与线要素相交的有效格网。

    Args:
        input_polyline: 输入的线状Shapefile文件路径
        output_polygon: 输出的多边形格网Shapefile文件路径
        grid_size: 正方形格网的边长（单位：米）
        block_step: 经纬度分块步长（单位：度），默认为10.0

    Returns:
        输出的合并后格网Shapefile文件路径

    Raises:
        FileNotFoundError: 输入文件不存在
        ValueError: 未生成任何格网数据
    """
    start_time = time.time()
    print(f"[INFO]  | 任务启动，PID={os.getpid()}")
    print(f"[INFO]  | 输入文件：{input_polyline}")
    print(f"[INFO]  | 输出文件：{output_polygon}")
    print(f"[INFO]  | 格网大小：{grid_size} 米")
    print(f"[INFO]  | 分块步长：{block_step} 度")

    # 检查输入文件是否存在
    if not arcpy.Exists(input_polyline):
        raise FileNotFoundError(f"[ERROR] | 输入文件不存在：{input_polyline}")

    # 创建输出目录
    output_dir = os.path.dirname(output_polygon)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # 环境设置
    arcpy.env.overwriteOutput = True

    # 坐标系定义
    projected_crs = arcpy.SpatialReference(3857)  # Web Mercator，单位：米
    geographic_crs = arcpy.SpatialReference(4326)  # WGS84，经纬度

    # 创建临时文件夹
    temp_dir = tempfile.mkdtemp()
    print(f"[INFO]  | 临时文件夹：{temp_dir}")

    # 读取线状数据并转换为地理坐标系用于分块
    print("[INFO]  | 正在读取线状数据...")
    lines_gdf = gpd.read_file(input_polyline)
    print(f"[INFO]  | 读取到 {len(lines_gdf)} 条线要素")

    # 确保数据为地理坐标系
    if lines_gdf.crs.to_epsg() != 4326:
        lines_gdf = lines_gdf.to_crs(epsg=4326)
        print("[INFO]  | 已将数据转换为WGS84地理坐标系")

    # 获取数据整体范围（经纬度）
    total_bounds = lines_gdf.total_bounds  # minx, miny, maxx, maxy
    min_lon, min_lat, max_lon, max_lat = total_bounds
    print(
        f"[INFO]  | 数据经纬度范围：经度 {min_lon:.6f}° 至 {max_lon:.6f}°，"
        f"纬度 {min_lat:.6f}° 至 {max_lat:.6f}°"
    )

    # 计算经纬度分块
    lon_blocks = []
    current_lon = math.floor(min_lon / block_step) * block_step
    while current_lon < max_lon:
        next_lon = current_lon + block_step
        lon_blocks.append((current_lon, next_lon))
        current_lon = next_lon

    lat_blocks = []
    current_lat = math.floor(min_lat / block_step) * block_step
    while current_lat < max_lat:
        next_lat = current_lat + block_step
        lat_blocks.append((current_lat, next_lat))
        current_lat = next_lat

    total_blocks = len(lon_blocks) * len(lat_blocks)
    print(
        f"[INFO]  | 经纬度分块完成：经度 {len(lon_blocks)} 块，"
        f"纬度 {len(lat_blocks)} 块，共 {total_blocks} 块"
    )

    # 存储所有分块结果的路径
    block_results = []

    # 处理每个分块
    for lon_idx, (lon_min, lon_max) in enumerate(lon_blocks):
        for lat_idx, (lat_min, lat_max) in enumerate(lat_blocks):
            block_id = f"block_{lon_idx}_{lat_idx}"
            print(
                f"[INFO]  | 处理分块 {block_id}："
                f"经度 {lon_min:.1f}°-{lon_max:.1f}°，"
                f"纬度 {lat_min:.1f}°-{lat_max:.1f}°"
            )

            # 创建分块边界框
            block_bbox = box(lon_min, lat_min, lon_max, lat_max)
            block_gdf = gpd.GeoDataFrame(geometry=[block_bbox], crs="EPSG:4326")

            # 筛选当前分块内的线要素
            lines_in_block = gpd.clip(lines_gdf, block_gdf)

            if len(lines_in_block) == 0:
                print(f"[INFO]  | 分块 {block_id} 内无数据，跳过")
                continue

            # 保存分块内的线要素为临时文件（投影坐标系）
            temp_line_file = os.path.join(temp_dir, f"{block_id}_lines.shp")
            lines_in_block_proj = lines_in_block.to_crs(epsg=projected_crs.factoryCode)
            lines_in_block_proj.to_file(temp_line_file)

            # 获取分块在投影坐标系下的范围
            block_bounds_proj = lines_in_block_proj.total_bounds
            x_min, y_min, x_max, y_max = block_bounds_proj

            # 对齐网格到指定大小
            x_min = math.floor(x_min / grid_size) * grid_size
            y_min = math.floor(y_min / grid_size) * grid_size
            x_max = math.ceil(x_max / grid_size) * grid_size
            y_max = math.ceil(y_max / grid_size) * grid_size

            # 计算网格行列数
            cols = int((x_max - x_min) / grid_size)
            rows = int((y_max - y_min) / grid_size)

            if cols == 0 or rows == 0:
                print(f"[INFO]  | 分块 {block_id} 网格行列数为零，跳过")
                continue

            # 创建对齐的渔网网格
            temp_fishnet = os.path.join(temp_dir, f"{block_id}_fishnet.shp")
            try:
                arcpy.CreateFishnet_management(
                    out_feature_class=temp_fishnet,
                    origin_coord=f"{x_min} {y_min}",
                    y_axis_coord=f"{x_min} {y_min + grid_size}",
                    cell_width=grid_size,
                    cell_height=grid_size,
                    number_rows=rows,
                    number_columns=cols,
                    corner_coord=f"{x_max} {y_max}",
                    labels="NO_LABELS",
                    geometry_type="POLYGON"
                )
                print(f"[INFO]  | 分块 {block_id} 创建渔网完成：{rows}行×{cols}列")
            except Exception as e:
                print(f"[ERROR] | 分块 {block_id} 创建渔网失败：{str(e)}")
                continue

            # 筛选与线要素相交的网格
            temp_selected = os.path.join(temp_dir, f"{block_id}_selected.shp")
            try:
                # 使用空间选择筛选与线要素相交的网格
                arcpy.MakeFeatureLayer_management(temp_fishnet, "fishnet_lyr")
                arcpy.MakeFeatureLayer_management(temp_line_file, "lines_lyr")

                arcpy.SelectLayerByLocation_management(
                    in_layer="fishnet_lyr",
                    overlap_type="INTERSECT",
                    select_features="lines_lyr",
                    selection_type="NEW_SELECTION"
                )

                # 检查是否有选中的要素
                result = arcpy.GetCount_management("fishnet_lyr")
                count = int(result.getOutput(0))

                if count == 0:
                    print(f"[INFO]  | 分块 {block_id} 没有与线要素相交的网格，跳过")
                    # 清理图层
                    arcpy.Delete_management("fishnet_lyr")
                    arcpy.Delete_management("lines_lyr")
                    continue

                # 将选中的要素保存到新文件
                arcpy.CopyFeatures_management("fishnet_lyr", temp_selected)

                # 清理图层
                arcpy.Delete_management("fishnet_lyr")
                arcpy.Delete_management("lines_lyr")

                print(f"[INFO]  | 分块 {block_id} 空间选择完成，选中 {count} 个网格")
            except Exception as e:
                print(f"[ERROR] | 分块 {block_id} 空间选择失败：{str(e)}")
                # 确保清理图层
                try:
                    arcpy.Delete_management("fishnet_lyr")
                except:
                    pass
                try:
                    arcpy.Delete_management("lines_lyr")
                except:
                    pass
                continue

            # 添加分块ID字段，便于后续追踪
            arcpy.AddField_management(
                in_table=temp_selected, field_name="BLOCK_ID", field_type="TEXT", field_length=50
            )
            arcpy.CalculateField_management(
                in_table=temp_selected, field="BLOCK_ID", expression=f"'{block_id}'", expression_type="PYTHON3"
            )

            # 定义输出坐标系
            arcpy.DefineProjection_management(temp_selected, projected_crs)

            block_results.append(temp_selected)
            print(f"[INFO]  | 分块 {block_id} 处理完成")

    # 合并所有分块结果
    if not block_results:
        raise ValueError("[ERROR] | 没有生成任何格网数据，请检查输入数据和参数")

    print(f"[INFO]  | 开始合并 {len(block_results)} 个分块结果...")

    # 合并所有分块的矢量格网
    temp_merged = os.path.join(temp_dir, "merged_grid.shp")
    arcpy.Merge_management(inputs=block_results, output=temp_merged)

    # 定义坐标系
    arcpy.DefineProjection_management(temp_merged, projected_crs)

    # 最终筛选：确保所有网格都与原始线要素相交
    print("[INFO]  | 执行最终筛选，移除不与原始线要素相交的网格...")

    # 创建原始线要素的投影版本用于空间选择
    lines_projected = os.path.join(temp_dir, "lines_projected.shp")
    lines_gdf.to_crs(epsg=projected_crs.factoryCode).to_file(lines_projected)

    arcpy.MakeFeatureLayer_management(temp_merged, "grid_lyr")
    arcpy.MakeFeatureLayer_management(lines_projected, "input_lyr")

    arcpy.SelectLayerByLocation_management(
        in_layer="grid_lyr",
        overlap_type="INTERSECT",
        select_features="input_lyr",
        selection_type="NEW_SELECTION"
    )

    # 检查是否有选中的要素
    result = arcpy.GetCount_management("grid_lyr")
    count = int(result.getOutput(0))

    if count == 0:
        print("[WARNING] | 最终筛选没有选中任何网格，可能存在问题")
    else:
        print(f"[INFO]  | 最终筛选选中 {count} 个网格")

    # 将最终选中的要素保存
    arcpy.CopyFeatures_management("grid_lyr", output_polygon)

    # 定义输出坐标系
    arcpy.DefineProjection_management(output_polygon, projected_crs)

    # 清理图层
    arcpy.Delete_management("grid_lyr")
    arcpy.Delete_management("input_lyr")

    # 清理临时文件 - 使用延迟删除策略
    try:
        import shutil
        # 先尝试正常删除
        shutil.rmtree(temp_dir)
        print("[INFO]  | 临时文件已清理")
    except Exception as e:
        print(f"[WARNING] | 清理临时文件失败：{str(e)}")
        # 如果失败，尝试使用arcpy删除
        try:
            # 获取临时目录中的所有文件
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if file_path.endswith('.shp') or file_path.endswith('.shx') or file_path.endswith('.dbf'):
                            arcpy.Delete_management(file_path)
                    except:
                        pass
            # 最后尝试删除目录
            shutil.rmtree(temp_dir, ignore_errors=True)
            print("[INFO]  | 已使用备用方法清理临时文件")
        except:
            print("[WARNING] | 无法完全清理临时文件，部分文件可能被锁定")

    # 获取最终格网数量
    final_count = int(arcpy.GetCount_management(output_polygon).getOutput(0))
    elapsed = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - start_time))
    print(f"[INFO]  | 总共生成 {final_count} 个格网单元")
    print(f"[INFO]  | 任务完成，文件已保存到：{output_polygon}")
    print(f"[TIME]  | 总耗时: {elapsed}")

    return output_polygon


def main() -> None:
    """主函数，负责调用生成格网的功能。"""
    try:
        # 检查ArcPy是否可用
        if "arcpy" not in globals():
            raise ImportError("[ERROR] | ArcPy模块不可用，请在ArcGIS环境中运行此脚本")

        # list_grid_size = [12000, 4800]
        list_grid_size = [900]

        for grid_size in list_grid_size:

            input_polyline = fr"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\Analyze\fractal_dimension\polyline_merge\polyline_merge.shp"
            output_polygon = fr"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\Analyze\fractal_dimension\grids\grids_{grid_size}m.shp"


            create_aligned_grid(
                input_polyline=input_polyline,
                output_polygon=output_polygon,
                grid_size=grid_size,
                block_step=10.0,
            )
    except Exception as err:
        print(f"[ERROR] | 发生错误：{err}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()