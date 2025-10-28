#!/usr/bin/env python3
"""
海岸线变化分析系统 - 海岸线提取模块
提供海岸线提取、图幅处理、阈值提取等功能
"""

import os
import time
from typing import List, Optional
import arcpy
import rasterio
from rasterio.warp import calculate_default_transform
from rasterio.enums import Resampling
from pyproj import CRS
from scipy.ndimage import zoom

from config import ProjectConfig, PathConfig, ProcessingParameters
from utils import TimeTracker, FileUtils
from data_processing import Rasterizer
from spatial_analysis import SpatialAnalyzer


class CoastlineExtractor:
    """海岸线提取器"""
    
    def __init__(self):
        self.config = ProjectConfig()
        self.path_config = PathConfig()
        self.params = ProcessingParameters()
        self.rasterizer = Rasterizer()
        self.spatial_analyzer = SpatialAnalyzer()
    
    def downscale_by_interpolation(self, input_tif: str, output_tif: str, 
                                 zoom_ratio: int = 2) -> None:
        """
        通过插值降尺度
        
        Args:
            input_tif: 输入TIFF路径
            output_tif: 输出TIFF路径
            zoom_ratio: 缩放比例
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始插值降尺度: {input_tif}")
            
            # 目标坐标系
            target_crs = CRS.from_epsg(4326)  # WGS 84
            
            with rasterio.open(input_tif) as source:
                src_crs = source.crs
                transform = source.transform
                band_count = source.count
                
                # 对每个波段进行处理
                resampled_bands = []
                for band in range(1, band_count + 1):
                    data = source.read(band)
                    resampled_data = zoom(data, zoom_ratio, order=1)  # 双线性插值
                    resampled_bands.append(resampled_data)
                
                # 计算新的地理变换
                new_transform, new_width, new_height = calculate_default_transform(
                    src_crs, target_crs, 
                    source.width * zoom_ratio, 
                    source.height * zoom_ratio, 
                    *source.bounds
                )
                
                # 写入新文件
                with rasterio.open(
                    output_tif,
                    'w',
                    driver='GTiff',
                    height=new_height,
                    width=new_width,
                    count=band_count,
                    dtype=resampled_bands[0].dtype,
                    crs=target_crs,
                    transform=new_transform,
                ) as destination:
                    for band in range(1, band_count + 1):
                        destination.write(resampled_bands[band - 1], band)
            
            TimeTracker.end_timing(start_time, "插值降尺度")
            print(f"[INFO] | 插值降尺度完成: {output_tif}")
            
        except Exception as error:
            print(f"[ERROR] | 插值降尺度失败: {error}")
            raise
    
    def filter_valid_pixel_to_shapefile(self, input_tif_path: str, 
                                      output_shp_path: str, 
                                      threshold: int = 5) -> None:
        """
        过滤有效像素并输出为Shapefile
        
        Args:
            input_tif_path: 输入TIFF路径
            output_shp_path: 输出Shapefile路径
            threshold: 阈值
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始过滤有效像素: {input_tif_path}")
            
            import fiona
            from fiona.crs import from_epsg
            from rasterio import features
            import numpy as np
            
            with rasterio.open(input_tif_path) as source:
                # 读取栅格数据
                band_data = source.read(1)
                mask = band_data >= threshold
                
                # 获取矢量化形状
                shapes = features.shapes(mask.astype(np.int16), transform=source.transform)
                
                # 定义Shapefile schema
                schema = {
                    'geometry': 'Polygon',
                    'properties': {'value': 'int'},
                }
                crs = from_epsg(source.crs.to_epsg())
                
                # 确保输出目录存在
                os.makedirs(os.path.dirname(output_shp_path), exist_ok=True)
                
                # 写入Shapefile
                with fiona.open(output_shp_path, 'w', driver='ESRI Shapefile',
                              crs=crs, schema=schema) as shapefile:
                    for shape, value in shapes:
                        if value == 1:  # 保留有效区域
                            shapefile.write({
                                'geometry': shape,
                                'properties': {'value': int(threshold)},
                            })
            
            TimeTracker.end_timing(start_time, "过滤有效像素")
            print(f"[INFO] | 有效像素过滤完成: {output_shp_path}")
            
        except Exception as error:
            print(f"[ERROR] | 过滤有效像素失败: {error}")
            raise
    
    def process_country_maps(self, year: int, country_code: str, 
                           threshold: int = 5) -> None:
        """
        处理国家地图数据
        
        Args:
            year: 年份
            country_code: 国家代码
            threshold: 阈值
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始处理 {country_code} {year} 年地图数据")
            
            arcpy.env.overwriteOutput = True
            
            # 获取影像文件列表
            dbf_path = os.path.join(
                self.path_config.arc_data, "d_SIDS_Boundary", "SIDS_Grids", 
                "SIDS_grid_link", f"{country_code}_grid.dbf"
            )
            
            records_list = FileUtils.read_dbf_to_list(dbf_path=dbf_path, should_print=False)
            print(f"[INFO] | 读取到 {len(records_list)} 条记录")
            
            for record in records_list:
                try:
                    map_name = record[4]  # 地图名称
                    
                    # 步骤1: 影像降尺度
                    input_tif = os.path.join(
                        self.path_config.gee_data, f"SIDs_Grid_Y{year % 100:02}", 
                        f"{map_name}_ls578_Index.tif"
                    )
                    
                    zoomed_tif = os.path.join(
                        self.path_config.arc_data, "temp", "bandInterpolation", 
                        f"{country_code}_{map_name}_zoom.tif"
                    )
                    os.makedirs(os.path.dirname(zoomed_tif), exist_ok=True)
                    
                    self.downscale_by_interpolation(input_tif, zoomed_tif)
                    
                    # 步骤2: 过滤有效像元并生成矢量
                    valid_pixel_shp = os.path.join(
                        self.path_config.arc_data, "temp", "filterValidPixel", 
                        f"{country_code}_{map_name}_valid_pixel.shp"
                    )
                    os.makedirs(os.path.dirname(valid_pixel_shp), exist_ok=True)
                    
                    self.filter_valid_pixel_to_shapefile(zoomed_tif, valid_pixel_shp, threshold)
                    
                    # 步骤3: 创建输出文件夹
                    output_folder = os.path.join(
                        self.path_config.arc_data, "e_SIDS_Shp", country_code, str(year)
                    )
                    os.makedirs(output_folder, exist_ok=True)
                    
                    # 步骤4: 筛选国家范围
                    country_shp = os.path.join(
                        self.path_config.arc_data, "d_SIDS_Boundary", "SIDS", 
                        "AdminDivision", f"{country_code}.shp"
                    )
                    output_shp = os.path.join(output_folder, f"{country_code}_{map_name}.shp")
                    
                    self.spatial_analyzer.select_by_location(
                        valid_pixel_shp, country_shp, output_shp
                    )
                    
                    # 删除临时文件
                    if os.path.isfile(zoomed_tif):
                        os.remove(zoomed_tif)
                        print(f"[INFO] | 删除临时文件: {zoomed_tif}")
                        
                except Exception as error:
                    print(f"[ERROR] | 处理 {map_name} 时发生错误: {error}")
                    continue
            
            TimeTracker.end_timing(start_time, f"处理 {country_code} 地图数据")
            print(f"[INFO] | {country_code} {year} 年地图数据处理完成")
            
        except Exception as error:
            print(f"[ERROR] | 处理 {country_code} 地图数据失败: {error}")
            raise
    
    def merge_submaps(self, country_code: str, year: int) -> None:
        """
        合并子图幅
        
        Args:
            country_code: 国家代码
            year: 年份
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始合并 {country_code} {year} 子图幅")
            
            arcpy.env.overwriteOutput = True
            
            # 获取子图幅文件列表
            folder_path = os.path.join(
                self.path_config.arc_data, "e_SIDS_Shp", country_code, str(year)
            )
            shp_files = FileUtils.get_files_absolute_paths(folder_path, ".shp")
            
            # 合并子图幅
            merge_shp = os.path.join(
                self.path_config.qgis, "a_SIDS_Shp_Merge", country_code, 
                f"{country_code}_{str(year)[-2:]}.shp"
            )
            os.makedirs(os.path.dirname(merge_shp), exist_ok=True)
            
            arcpy.management.Merge(shp_files, merge_shp)
            
            TimeTracker.end_timing(start_time, "合并子图幅")
            print(f"[INFO] | 子图幅合并完成: {merge_shp}")
            
        except Exception as error:
            print(f"[ERROR] | 合并子图幅失败: {error}")
            raise
    
    def dissolve_country_features(self, country_code: str, year: int) -> None:
        """
        融合国家要素
        
        Args:
            country_code: 国家代码
            year: 年份
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始融合 {country_code} {year} 要素")
            
            arcpy.env.overwriteOutput = True
            
            # 输入要素路径
            input_features = os.path.join(
                self.path_config.qgis, "a_SIDS_Shp_Merge", country_code, 
                f"{country_code}_{str(year)[-2:]}.shp"
            )
            
            # 输出要素路径
            output_features = os.path.join(
                self.path_config.qgis, "b_SIDS_Shp_Dissolve", country_code, 
                f"{country_code}_{str(year)[-2:]}.shp"
            )
            os.makedirs(os.path.dirname(output_features), exist_ok=True)
            
            # 执行融合
            arcpy.analysis.PairwiseDissolve(input_features, output_features)
            
            TimeTracker.end_timing(start_time, "融合国家要素")
            print(f"[INFO] | 国家要素融合完成: {output_features}")
            
        except Exception as error:
            print(f"[ERROR] | 融合国家要素失败: {error}")
            raise


class ThresholdExtractor:
    """阈值提取器"""
    
    def __init__(self):
        self.config = ProjectConfig()
        self.path_config = PathConfig()
    
    def extract_by_threshold(self, countries: List[str], years: List[int], 
                           threshold: int = 10) -> None:
        """
        按阈值提取海岸线
        
        Args:
            countries: 国家列表
            years: 年份列表
            threshold: 提取阈值
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始阈值提取海岸线，阈值: {threshold}")
            
            extractor = CoastlineExtractor()
            
            for year in years:
                for country_code in countries:
                    print(f"[INFO] | 处理 {year} 年 {country_code} 数据...")
                    extractor.process_country_maps(
                        year=year, 
                        country_code=country_code, 
                        threshold=threshold
                    )
            
            TimeTracker.end_timing(start_time, "阈值提取海岸线")
            print(f"[INFO] | 阈值提取海岸线完成")
            
        except Exception as error:
            print(f"[ERROR] | 阈值提取海岸线失败: {error}")
            raise


if __name__ == "__main__":
    # 海岸线提取测试
    print("[INFO] | 海岸线提取模块加载完成")