#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海岸线变化分析项目 - 海岸线提取模块

作用：子像素海岸线提取、轮廓闭合、自动构面等核心功能
主要类：CoastlineExtractor, SubpixelProcessor
使用示例：from coastline_extraction import CoastlineExtractor
"""

import os
import tempfile
from typing import Optional
import numpy as np
import rasterio
from rasterio import Affine
import xarray as xr
import rioxarray
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from shapely.ops import polygonize
from dea_tools.spatial import subpixel_contours

from config import PROJECT_CONFIG
from utils import TimeTracker, FileUtils


class SubpixelProcessor:
    """子像素处理器"""
    
    @staticmethod
    def add_zero_buffer_to_array(data: np.ndarray, buffer_size: int = 1) -> np.ndarray:
        """
        为栅格数组添加零值缓冲区
        
        Args:
            data: 原始二维数组
            buffer_size: 缓冲宽度
            
        Returns:
            扩展后的二维数组
        """
        return np.pad(data, pad_width=buffer_size, mode='constant', constant_values=0)
    
    @staticmethod
    def process_multilinestring_geometry(geometry: MultiLineString) -> list:
        """
        处理 MultiLineString 几何，闭合线段
        
        Args:
            geometry: 输入的 MultiLineString 对象
            
        Returns:
            闭合后的 LineString 对象列表
        """
        closed_lines = []
        if isinstance(geometry, MultiLineString):
            for component in geometry.geoms:
                coords = list(component.coords)
                if coords[0] != coords[-1]:  # 若未闭合，则闭合
                    coords.append(coords[0])
                closed_lines.append(LineString(coords))
        return closed_lines
    
    @staticmethod
    def fix_subpixel_extraction(input_geojson: str, 
                              output_geojson: str, 
                              x_offset: float, 
                              y_offset: float) -> None:
        """
        修复子像素提取结果，应用坐标偏移
        
        Args:
            input_geojson: 输入 GeoJSON 文件路径
            output_geojson: 输出 GeoJSON 文件路径
            x_offset: X 方向偏移量
            y_offset: Y 方向偏移量
        """
        gdf = gpd.read_file(input_geojson)
        
        for idx, row in gdf.iterrows():
            geometry = row.geometry
            if isinstance(geometry, MultiLineString):
                closed_components = []
                for component in geometry.geoms:
                    coords = [(x + x_offset, y + y_offset) for x, y in component.coords]
                    if coords[0] != coords[-1]:
                        coords.append(coords[0])
                    closed_components.append(LineString(coords))
                gdf.at[idx, 'geometry'] = MultiLineString(closed_components)
        
        gdf.to_file(output_geojson, driver="GeoJSON")
        print(f"[INFO]  | 子像素修复完成: {output_geojson}")


class CoastlineExtractor:
    """海岸线提取器"""
    
    def __init__(self):
        self.processor = SubpixelProcessor()
    
    def extract_subpixel_contours(self, 
                                input_tif_path: str, 
                                output_geojson_path: str, 
                                z_values: int = 0) -> None:
        """
        提取子像素轮廓线
        
        Args:
            input_tif_path: 输入 TIF 文件路径
            output_geojson_path: 输出 GeoJSON 文件路径
            z_values: 等值线提取值
        """
        with TimeTracker("子像素轮廓提取"):
            FileUtils.ensure_directory_exists(output_geojson_path)
            
            # 创建临时缓冲文件
            fd, temp_buffer_path = tempfile.mkstemp(suffix='.tif')
            os.close(fd)
            
            try:
                # 添加零值缓冲区
                with rasterio.open(input_tif_path) as src:
                    data = src.read(1)
                    transform = src.transform
                    crs = src.crs
                    
                    data_buffered = self.processor.add_zero_buffer_to_array(data, buffer_size=1)
                    transform_buffered = transform * Affine.translation(-1, -1)
                    
                    profile = src.profile.copy()
                    profile.update({
                        'width': data_buffered.shape[1],
                        'height': data_buffered.shape[0],
                        'transform': transform_buffered
                    })
                    
                    with rasterio.open(temp_buffer_path, 'w', **profile) as dst:
                        dst.write(data_buffered, 1)
                
                # 计算偏移量
                x_offset = transform_buffered[0] / 2
                y_offset = transform_buffered[4] / 2
                
                # 构建 DataArray
                with rasterio.open(temp_buffer_path) as src:
                    raster_data = src.read(1)
                    transform_final = src.transform
                    crs_final = src.crs
                    height, width = raster_data.shape
                    
                    x_coords = [transform_final * (col, 0) for col in range(width)]
                    y_coords = [transform_final * (0, row) for row in range(height)]
                    x_coords = [x[0] for x in x_coords]
                    y_coords = [y[1] for y in y_coords]
                    
                    data_array = xr.DataArray(
                        raster_data,
                        coords=[y_coords, x_coords],
                        dims=["y", "x"],
                        attrs={'crs': str(crs_final), 'transform': transform_final}
                    ).rio.write_crs("EPSG:4326", inplace=True)
                
                # 创建临时 GeoJSON 文件
                fd, temp_geojson_path = tempfile.mkstemp(suffix='.geojson')
                os.close(fd)
                
                # 提取子像素轮廓
                subpixel_contours(
                    da=data_array, 
                    z_values=z_values, 
                    attribute_df=None, 
                    output_path=temp_geojson_path
                )
                
                # 修复提取结果
                self.processor.fix_subpixel_extraction(
                    temp_geojson_path, 
                    output_geojson_path, 
                    x_offset, 
                    y_offset
                )
                
            finally:
                # 清理临时文件
                if os.path.exists(temp_buffer_path):
                    os.remove(temp_buffer_path)
                if os.path.exists(temp_geojson_path):
                    os.remove(temp_geojson_path)
    
    def polygonize_from_lines(self, line_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        从线要素自动构面
        
        Args:
            line_gdf: 包含线要素的 GeoDataFrame
            
        Returns:
            构面后的 Polygon GeoDataFrame
        """
        all_lines = []
        for geom in line_gdf.geometry:
            if isinstance(geom, LineString):
                all_lines.append(geom)
            elif isinstance(geom, MultiLineString):
                all_lines.extend(geom.geoms)
        
        polygons = list(polygonize(all_lines))
        if not polygons:
            raise ValueError("无法从线要素构建闭合面")
        
        return gpd.GeoDataFrame(geometry=polygons, crs=line_gdf.crs)
    
    def extract_coastline_polygons(self, 
                                 input_tif_path: str, 
                                 output_shp_path: str, 
                                 z_value: int = 0) -> None:
        """
        从栅格数据提取海岸线多边形
        
        Args:
            input_tif_path: 输入 TIF 文件路径
            output_shp_path: 输出面要素 Shapefile 路径
            z_value: 等值线提取值
        """
        with TimeTracker("海岸线多边形提取"):
            FileUtils.ensure_directory_exists(output_shp_path)
            
            # 创建临时 GeoJSON 文件
            fd, temp_geojson_path = tempfile.mkstemp(suffix='.geojson')
            os.close(fd)
            
            try:
                # 提取子像素轮廓
                self.extract_subpixel_contours(input_tif_path, temp_geojson_path, z_value)
                
                # 读取线要素
                line_gdf = gpd.read_file(temp_geojson_path)
                
                # 自动构面
                polygon_gdf = self.polygonize_from_lines(line_gdf)
                
                # 保存结果
                polygon_gdf.to_file(output_shp_path)
                print(f"[INFO]  | 海岸线多边形提取完成: {output_shp_path}")
                
            finally:
                # 清理临时文件
                if os.path.exists(temp_geojson_path):
                    os.remove(temp_geojson_path)


def smooth_polygon_features(input_shp: str, 
                          output_shp: str, 
                          tolerance: str = "90 Meters") -> None:
    """
    平滑多边形要素
    
    Args:
        input_shp: 输入面要素 Shapefile
        output_shp: 输出面要素 Shapefile  
        tolerance: 平滑容忍度
    """
    try:
        arcpy.env.overwriteOutput = True
        FileUtils.ensure_directory_exists(output_shp)
        
        temp_merge = r'in_memory\shp_merge'
        temp_dissolve = r'in_memory\shp_dissolve'
        
        # 合并要素
        arcpy.management.Merge(inputs=[input_shp], output=temp_merge)
        
        # 融合要素
        arcpy.analysis.PairwiseDissolve(
            in_features=temp_merge, 
            out_feature_class=temp_dissolve,
            multi_part="MULTI_PART"
        )
        
        # 平滑要素
        arcpy.cartography.SmoothPolygon(
            in_features=temp_dissolve,
            out_feature_class=output_shp,
            algorithm="PAEK",
            tolerance=tolerance,
            endpoint_option="FIXED_ENDPOINT",
            error_option="NO_CHECK"
        )
        
        # 计算几何属性
        arcpy.management.CalculateGeometryAttributes(
            in_features=output_shp,
            geometry_property=[
                ["Leng_Geo", "PERIMETER_LENGTH_GEODESIC"], 
                ["Area_Geo", "AREA_GEODESIC"]
            ],
            length_unit="KILOMETERS", 
            area_unit="SQUARE_KILOMETERS", 
            coordinate_format="SAME_AS_INPUT"
        )
        
        print(f"[INFO]  | 多边形平滑完成: {output_shp}")
        
    except Exception as e:
        print(f"[ERROR] | 多边形平滑失败: {e}")
        raise