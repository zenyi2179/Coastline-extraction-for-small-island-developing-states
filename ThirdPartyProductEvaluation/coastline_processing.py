#!/usr/bin/env python3
"""
海岸线变化分析系统 - 海岸线处理功能
提供海岸线提取、验证、转换等专用处理功能
"""

import os
import arcpy
from typing import List
from config import ProjectConfig
from utils import TimeTracker, log_execution
from spatial_analysis import GeometryProcessor


class CoastlineProcessor:
    """海岸线处理器"""
    
    def __init__(self) -> None:
        self.config = ProjectConfig()
        self.geometry_processor = GeometryProcessor()
    
    @log_execution
    def extract_valid_coastline(self, input_data: str, output_data: str) -> bool:
        """
        提取有效海岸线
        
        Args:
            input_data: 输入数据路径
            output_data: 输出数据路径
            
        Returns:
            提取是否成功
        """
        return self.geometry_processor.feature_to_line(input_data, output_data)
    
    @log_execution
    def extract_inland_lines(
        self, 
        input_data: str, 
        mask_data: str, 
        output_data: str
    ) -> bool:
        """
        提取内陆线
        
        Args:
            input_data: 输入数据路径
            mask_data: 掩膜数据路径
            output_data: 输出数据路径
            
        Returns:
            提取是否成功
        """
        try:
            # 临时线要素
            temp_line = r"in_memory\temp_coastline"
            
            # 转换为线
            self.geometry_processor.feature_to_line(input_data, temp_line)
            
            # 使用掩膜裁剪
            self.geometry_processor.clip_features(temp_line, mask_data, output_data)
            
            print(f"[INFO]  | 内陆线提取成功: {output_data}")
            return True
            
        except Exception as error:
            print(f"[ERROR] | 内陆线提取失败: {error}")
            return False
    
    @log_execution
    def process_sids_coastlines(
        self,
        insert_countries: List[str],
        extract_countries: List[str],
        output_directory: str,
        year: int,
        operation_type: str = "insert"
    ) -> None:
        """
        处理SIDS海岸线
        
        Args:
            insert_countries: 插入处理国家列表
            extract_countries: 提取处理国家列表
            output_directory: 输出目录
            year: 处理年份
            operation_type: 操作类型，可选 'insert', 'extract', 'both'
        """
        mask_directory = self.config.data_sources["boundary_mask"]
        source_directory = self.config.data_sources["sids_optimize"]
        
        print(f"[INFO]  | 执行操作: {operation_type}")
        
        if operation_type in ["insert", "both"]:
            for country in insert_countries:
                self._process_insert_country(
                    country=country,
                    source_directory=source_directory,
                    output_directory=output_directory,
                    year=year
                )
        
        if operation_type in ["extract", "both"]:
            for country in extract_countries:
                self._process_extract_country(
                    country=country,
                    source_directory=source_directory,
                    mask_directory=mask_directory,
                    output_directory=output_directory,
                    year=year
                )
    
    def _process_insert_country(
        self,
        country: str,
        source_directory: str,
        output_directory: str,
        year: int
    ) -> None:
        """处理插入类型国家"""
        country_output_dir = os.path.join(output_directory, country)
        os.makedirs(country_output_dir, exist_ok=True)
        
        input_data = os.path.join(
            source_directory, 
            f"{country}\\{country}_{str(year)[-2:]}.shp"
        )
        output_data = os.path.join(
            country_output_dir, 
            f"{country}_CL_{str(year)[-2:]}.shp"
        )
        
        if not os.path.exists(input_data):
            print(f"[WARN]  | 输入数据不存在: {input_data}")
            return
        
        self.extract_valid_coastline(input_data, output_data)
        print(f"[INFO]  | 插入处理完成: {output_data}")
    
    def _process_extract_country(
        self,
        country: str,
        source_directory: str,
        mask_directory: str,
        output_directory: str,
        year: int
    ) -> None:
        """处理提取类型国家"""
        country_output_dir = os.path.join(output_directory, country)
        os.makedirs(country_output_dir, exist_ok=True)
        
        input_data = os.path.join(
            source_directory, 
            f"{country}\\{country}_{str(year)[-2:]}.shp"
        )
        mask_data = os.path.join(mask_directory, f"{country}_v3.shp")
        output_data = os.path.join(
            country_output_dir, 
            f"{country}_CL_{str(year)[-2:]}.shp"
        )
        
        if not os.path.exists(input_data):
            print(f"[WARN]  | 输入数据不存在: {input_data}")
            return
        
        if not os.path.exists(mask_data):
            print(f"[WARN]  | 掩膜数据不存在: {mask_data}")
            return
        
        self.extract_inland_lines(input_data, mask_data, output_data)
        print(f"[INFO]  | 提取处理完成: {output_data}")
    
    @log_execution
    def batch_process_coastlines_by_year(
        self,
        insert_countries: List[str],
        extract_countries: List[str],
        years: List[int],
        operation_type: str = "insert"
    ) -> None:
        """
        按年份批量处理海岸线
        
        Args:
            insert_countries: 插入处理国家列表
            extract_countries: 提取处理国家列表
            years: 处理年份列表
            operation_type: 操作类型
        """
        for year in years:
            output_directory = self.config.get_output_path("sids_cl", year)
            self.process_sids_coastlines(
                insert_countries=insert_countries,
                extract_countries=extract_countries,
                output_directory=output_directory,
                year=year,
                operation_type=operation_type
            )


class CoastlineValidator:
    """海岸线验证器"""
    
    @staticmethod
    @log_execution
    def validate_coastline_geometry(coastline_data: str) -> bool:
        """
        验证海岸线几何
        
        Args:
            coastline_data: 海岸线数据路径
            
        Returns:
            几何是否有效
        """
        try:
            # 检查要素数量
            feature_count = arcpy.management.GetCount(coastline_data)
            count = int(feature_count[0])
            
            if count == 0:
                print(f"[WARN]  | 海岸线数据为空: {coastline_data}")
                return False
            
            # 检查几何类型
            desc = arcpy.Describe(coastline_data)
            geometry_type = desc.shapeType
            
            if geometry_type not in ["Polyline", "Polygon"]:
                print(f"[WARN]  | 不支持的几何类型: {geometry_type}")
                return False
            
            print(f"[INFO]  | 海岸线验证通过: {coastline_data} (要素数: {count})")
            return True
            
        except Exception as error:
            print(f"[ERROR] | 海岸线验证失败: {error}")
            return False


if __name__ == "__main__":
    # 海岸线处理测试
    processor = CoastlineProcessor()
    validator = CoastlineValidator()
    
    with TimeTracker("海岸线处理测试"):
        test_insert_countries = ["ATG", "BHS"]
        test_extract_countries = ["BLZ"]
        test_years = [2015]
        
        processor.batch_process_coastlines_by_year(
            insert_countries=test_insert_countries,
            extract_countries=test_extract_countries,
            years=test_years,
            operation_type="insert"
        )