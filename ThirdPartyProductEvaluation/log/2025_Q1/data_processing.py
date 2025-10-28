#!/usr/bin/env python3
"""
海岸线变化分析系统 - 数据处理核心功能
提供数据格式转换、子像素提取、平滑处理等核心功能
"""

import os
import time
from typing import List, Optional, Tuple
import geopandas as gpd
import rasterio
import numpy as np
import xarray as xr
from rasterio import Affine
from rasterio.features import rasterize
from shapely.geometry import LineString, MultiLineString, mapping
from dea_tools.spatial import subpixel_contours
import arcpy

from config import ProjectConfig, PathConfig, ProcessingParameters
from utils import TimeTracker


class DataFormatConverter:
    """数据格式转换器"""
    
    def __init__(self):
        self.path_config = PathConfig()
    
    def geojson_to_shapefile(self, input_geojson: str, output_shp: str) -> None:
        """
        GeoJSON转换为Shapefile
        
        Args:
            input_geojson: 输入GeoJSON路径
            output_shp: 输出Shapefile路径
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始GeoJSON转换: {input_geojson}")
            
            # 读取GeoJSON文件
            geo_dataframe = gpd.read_file(input_geojson)
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_shp), exist_ok=True)
            
            # 保存为Shapefile
            geo_dataframe.to_file(output_shp, driver='ESRI Shapefile')
            
            TimeTracker.end_timing(start_time, "GeoJSON转换")
            print(f"[INFO] | GeoJSON转换完成: {output_shp}")
            
        except Exception as error:
            print(f"[ERROR] | GeoJSON转换失败: {error}")
            raise
    
    def line_to_polygon(self, input_shp: str, output_shp: str) -> None:
        """
        线要素转换为面要素
        
        Args:
            input_shp: 输入线要素路径
            output_shp: 输出面要素路径
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始线转面转换: {input_shp}")
            
            arcpy.env.overwriteOutput = True
            
            # 临时文件路径
            temp_shp = os.path.join(self.path_config.arc_data, "temp", "temp.shp")
            os.makedirs(os.path.dirname(temp_shp), exist_ok=True)
            
            # 要素转面
            arcpy.management.FeatureToPolygon(
                in_features=[input_shp], 
                out_feature_class=temp_shp, 
                cluster_tolerance="", 
                attributes="ATTRIBUTES", 
                label_features=""
            )
            
            # 融合面要素
            arcpy.management.Dissolve(
                in_features=temp_shp, 
                out_feature_class=output_shp, 
                dissolve_field=[], 
                statistics_fields=[], 
                multi_part="SINGLE_PART", 
                unsplit_lines="DISSOLVE_LINES", 
                concatenation_separator=""
            )
            
            # 清理临时文件
            if os.path.exists(temp_shp):
                arcpy.Delete_management(temp_shp)
            
            TimeTracker.end_timing(start_time, "线转面转换")
            print(f"[INFO] | 线转面转换完成: {output_shp}")
            
        except Exception as error:
            print(f"[ERROR] | 线转面转换失败: {error}")
            raise
    
    def polygon_to_line(self, input_shp: str, output_shp: str) -> None:
        """
        面要素转换为线要素
        
        Args:
            input_shp: 输入面要素路径
            output_shp: 输出线要素路径
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始面转线转换: {input_shp}")
            
            arcpy.env.overwriteOutput = True
            arcpy.management.PolygonToLine(input_shp, output_shp)
            
            TimeTracker.end_timing(start_time, "面转线转换")
            print(f"[INFO] | 面转线转换完成: {output_shp}")
            
        except Exception as error:
            print(f"[ERROR] | 面转线转换失败: {error}")
            raise


class SubpixelExtractor:
    """子像素提取器"""
    
    def __init__(self):
        self.params = ProcessingParameters()
    
    def add_zero_buffer(self, input_tif: str, output_tif: str, buffer_size: int = 1) -> None:
        """
        为TIFF文件添加零值边界
        
        Args:
            input_tif: 输入TIFF路径
            output_tif: 输出TIFF路径
            buffer_size: 缓冲区大小
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始添加零值边界: {input_tif}")
            
            with rasterio.open(input_tif) as source:
                # 获取源文件元数据
                profile = source.profile.copy()
                width, height = source.width, source.height
                
                # 计算新尺寸
                new_width = width + 2 * buffer_size
                new_height = height + 2 * buffer_size
                
                # 更新仿射变换
                new_transform = source.transform * Affine.translation(-buffer_size, -buffer_size)
                
                # 更新元数据
                profile.update({
                    'width': new_width,
                    'height': new_height,
                    'transform': new_transform
                })
                
                # 创建新数据数组
                new_data = np.zeros((source.count, new_height, new_width), dtype=source.dtypes[0])
                
                # 读取原始数据并放置到中央
                original_data = source.read()
                new_data[:, buffer_size:buffer_size + height, buffer_size:buffer_size + width] = original_data
                
                # 写入新文件
                with rasterio.open(output_tif, 'w', **profile) as destination:
                    destination.write(new_data)
            
            TimeTracker.end_timing(start_time, "添加零值边界")
            print(f"[INFO] | 零值边界添加完成: {output_tif}")
            
        except Exception as error:
            print(f"[ERROR] | 添加零值边界失败: {error}")
            raise
    
    def process_multilinestring(self, geometry: MultiLineString, x_offset: float, y_offset: float) -> List[LineString]:
        """
        处理MultiLineString几何对象
        
        Args:
            geometry: MultiLineString几何对象
            x_offset: X方向偏移量
            y_offset: Y方向偏移量
            
        Returns:
            处理后的LineString列表
        """
        processed_lines = []
        
        if isinstance(geometry, MultiLineString):
            for component in geometry.geoms:
                coords = list(component.coords)
                start_point = coords[0]
                end_point = coords[-1]
                
                # 应用坐标偏移
                coords = [(x + x_offset, y + y_offset) for x, y in coords]
                
                # 闭合线段
                if start_point != end_point:
                    coords.append(coords[0])
                
                processed_lines.append(LineString(coords))
        else:
            print(f"[WARN] | 几何对象不是MultiLineString类型")
        
        return processed_lines
    
    def fix_subpixel_extraction(self, input_geojson: str, output_geojson: str, 
                               x_offset: float, y_offset: float) -> None:
        """
        修复子像素提取结果
        
        Args:
            input_geojson: 输入GeoJSON路径
            output_geojson: 输出GeoJSON路径
            x_offset: X方向偏移量
            y_offset: Y方向偏移量
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始修复子像素提取: {input_geojson}")
            
            geo_dataframe = gpd.read_file(input_geojson)
            
            for index, row in geo_dataframe.iterrows():
                geometry = row['geometry']
                
                if isinstance(geometry, MultiLineString):
                    closed_components = self.process_multilinestring(geometry, x_offset, y_offset)
                    closed_multilinestring = MultiLineString(closed_components)
                    geo_dataframe.at[index, 'geometry'] = closed_multilinestring
                else:
                    print(f"[WARN] | 要素 {index + 1} 不是MultiLineString")
            
            # 保存修复后的结果
            geo_dataframe.to_file(output_geojson, driver="GeoJSON")
            
            TimeTracker.end_timing(start_time, "修复子像素提取")
            print(f"[INFO] | 子像素提取修复完成: {output_geojson}")
            
        except Exception as error:
            print(f"[ERROR] | 修复子像素提取失败: {error}")
            raise
    
    def extract_subpixel_contours(self, input_tif: str, z_values: int, output_geojson: str) -> None:
        """
        提取子像素等高线
        
        Args:
            input_tif: 输入TIFF路径
            z_values: Z值阈值
            output_geojson: 输出GeoJSON路径
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始子像素等高线提取: {input_tif}")
            
            # 添加零值边界
            temp_buffer_tif = os.path.join(self.path_config.arc_data, "GEE_Filtering", "temp_zero_buffer.tif")
            os.makedirs(os.path.dirname(temp_buffer_tif), exist_ok=True)
            self.add_zero_buffer(input_tif, temp_buffer_tif, self.params.SUBPIXEL_BUFFER_SIZE)
            
            # 读取栅格数据
            with rasterio.open(temp_buffer_tif) as source:
                raster_data = source.read(1)
                transform = source.transform
                crs = source.crs
                height, width = raster_data.shape
                
                # 计算偏移量
                x_offset = transform[0] / 2
                y_offset = transform[4] / 2
                
                # 创建坐标数组
                x_coords = [transform * (col, 0) for col in range(width)]
                y_coords = [transform * (0, row) for row in range(height)]
                x_coords = [x[0] for x in x_coords]
                y_coords = [y[1] for y in y_coords]
                
                # 转换为xarray DataArray
                data_array = xr.DataArray(
                    raster_data,
                    coords=[y_coords, x_coords],
                    dims=["y", "x"],
                    attrs={'crs': str(crs), 'transform': transform}
                )
            
            # 设置坐标参考系
            data_array = data_array.rio.write_crs("EPSG:4326", inplace=True)
            
            # 临时GeoJSON文件
            temp_geojson = os.path.join(self.path_config.arc_data, "GEE_Geojson", "temp.geojson")
            os.makedirs(os.path.dirname(temp_geojson), exist_ok=True)
            
            # 子像素等高线提取
            subpixel_contours(da=data_array, z_values=z_values, attribute_df=None, output_path=temp_geojson)
            
            # 修复提取结果
            self.fix_subpixel_extraction(temp_geojson, output_geojson, x_offset, y_offset)
            
            # 清理临时文件
            for temp_file in [temp_buffer_tif, temp_geojson]:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            TimeTracker.end_timing(start_time, "子像素等高线提取")
            print(f"[INFO] | 子像素等高线提取完成: {output_geojson}")
            
        except Exception as error:
            print(f"[ERROR] | 子像素等高线提取失败: {error}")
            raise


class PolygonSmoother:
    """面要素平滑器"""
    
    def __init__(self):
        self.params = ProcessingParameters()
    
    def smooth_polygon(self, input_features: str, output_features: str) -> None:
        """
        平滑面要素
        
        Args:
            input_features: 输入要素路径
            output_features: 输出要素路径
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始面要素平滑: {input_features}")
            
            arcpy.env.overwriteOutput = True
            
            # 执行平滑处理
            arcpy.cartography.SmoothPolygon(
                in_features=input_features,
                out_feature_class=output_features,
                algorithm=self.params.SMOOTH_ALGORITHM,
                tolerance=self.params.SMOOTH_TOLERANCE,
                endpoint_option=self.params.SMOOTH_ENDPOINT_OPTION,
                error_option="NO_CHECK"
            )
            
            TimeTracker.end_timing(start_time, "面要素平滑")
            print(f"[INFO] | 面要素平滑完成: {output_features}")
            
        except Exception as error:
            print(f"[ERROR] | 面要素平滑失败: {error}")
            raise


class Rasterizer:
    """栅格化处理器"""
    
    def __init__(self):
        self.params = ProcessingParameters()
    
    def vector_to_raster(self, vector_path: str, raster_path: str, 
                        reference_raster: str, value: int = 10) -> None:
        """
        矢量数据转换为栅格
        
        Args:
            vector_path: 输入矢量路径
            raster_path: 输出栅格路径
            reference_raster: 参考栅格路径
            value: 栅格像元值
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始矢量转栅格: {vector_path}")
            
            # 读取矢量数据
            vector_data = gpd.read_file(vector_path)
            crs = vector_data.crs
            bounds = vector_data.total_bounds
            
            # 获取参考栅格像元大小
            with rasterio.open(reference_raster) as reference:
                pixel_size = reference.res[0]
            
            # 计算输出栅格尺寸
            width = int((bounds[2] - bounds[0]) / pixel_size)
            height = int((bounds[3] - bounds[1]) / pixel_size)
            
            # 计算仿射变换
            transform = rasterio.Affine(pixel_size, 0, bounds[0], 0, -pixel_size, bounds[3])
            
            # 获取几何数据
            geometries = vector_data.geometry
            
            # 栅格化
            rasterized_data = rasterize(
                [(mapping(geometry), value) for geometry in geometries],
                out_shape=(height, width),
                transform=transform,
                fill=0,
                dtype='uint8'
            )
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(raster_path), exist_ok=True)
            
            # 保存栅格文件
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
                nodata=0
            ) as destination:
                destination.write(rasterized_data, 1)
            
            TimeTracker.end_timing(start_time, "矢量转栅格")
            print(f"[INFO] | 矢量转栅格完成: {raster_path}")
            
        except Exception as error:
            print(f"[ERROR] | 矢量转栅格失败: {error}")
            raise


if __name__ == "__main__":
    # 功能测试
    print("[INFO] | 数据处理核心功能模块加载完成")