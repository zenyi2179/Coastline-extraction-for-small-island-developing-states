#!/usr/bin/env python3
"""
海岸线变化分析系统 - 数据提取功能
提供按位置选择、掩膜裁剪等数据提取和筛选功能
"""

import os
import arcpy
from typing import List, Optional
from config import ProjectConfig
from utils import TimeTracker, ArcPyUtils, log_execution


class DataExtractor:
    """数据提取器"""
    
    def __init__(self) -> None:
        self.config = ProjectConfig()
        self.arcpy_utils = ArcPyUtils()
    
    @log_execution
    def extract_by_location(
        self,
        input_data: str,
        boundary_data: str,
        output_data: str,
        search_distance: str = None
    ) -> bool:
        """
        按位置提取数据
        
        Args:
            input_data: 输入数据路径
            boundary_data: 边界数据路径
            output_data: 输出数据路径
            search_distance: 搜索距离，默认为配置中的距离
            
        Returns:
            提取是否成功
        """
        if search_distance is None:
            search_distance = self.config.processing_params["search_distance"]
        
        try:
            # 按位置选择要素
            selected_layer = arcpy.management.SelectLayerByLocation(
                in_layer=[input_data],
                overlap_type="INTERSECT",
                select_features=boundary_data,
                search_distance=search_distance,
                selection_type="NEW_SELECTION"
            )
            
            # 导出选择的要素
            arcpy.conversion.ExportFeatures(
                in_features=selected_layer,
                out_features=output_data
            )
            
            # 清除选择
            self.arcpy_utils.clear_selection(selected_layer)
            
            print(f"[INFO]  | 位置提取成功: {output_data}")
            return True
            
        except Exception as error:
            print(f"[ERROR] | 位置提取失败: {error}")
            return False
    
    @log_execution
    def extract_by_mask(
        self,
        input_data: str,
        boundary_data: str,
        mask_data: str,
        output_data: str,
        search_distance: str = None
    ) -> bool:
        """
        使用掩膜提取数据
        
        Args:
            input_data: 输入数据路径
            boundary_data: 边界数据路径
            mask_data: 掩膜数据路径
            output_data: 输出数据路径
            search_distance: 搜索距离，默认为配置中的距离
            
        Returns:
            提取是否成功
        """
        if search_distance is None:
            search_distance = self.config.processing_params["clip_distance"]
        
        try:
            # 按位置选择要素
            selected_layer = arcpy.management.SelectLayerByLocation(
                in_layer=[input_data],
                overlap_type="INTERSECT",
                select_features=boundary_data,
                search_distance=search_distance,
                selection_type="NEW_SELECTION"
            )
            
            # 使用掩膜裁剪
            arcpy.analysis.PairwiseClip(
                in_features=selected_layer,
                clip_features=mask_data,
                out_feature_class=output_data
            )
            
            # 清除选择
            self.arcpy_utils.clear_selection(selected_layer)
            
            print(f"[INFO]  | 掩膜提取成功: {output_data}")
            return True
            
        except Exception as error:
            print(f"[ERROR] | 掩膜提取失败: {error}")
            return False
    
    @log_execution
    def extract_gcl_fcs30_data(
        self,
        countries: List[str],
        year: int,
        output_base_dir: str,
        operation_type: str = "both"
    ) -> None:
        """
        提取GCL_FCS30数据
        
        Args:
            countries: 国家代码列表
            year: 处理年份
            output_base_dir: 输出基础目录
            operation_type: 操作类型，可选 'insert', 'extract', 'both'
        """
        insert_countries = countries  # 这里可以根据需要进一步分类
        extract_countries = countries  # 这里可以根据需要进一步分类
        
        origin_data_dir = os.path.join(
            self.config.get_output_path("gcl_fcs30", year), 
            "_draft"
        )
        input_data_path = os.path.join(origin_data_dir, f"GCL{year}.shp")
        
        if not os.path.exists(input_data_path):
            print(f"[ERROR] | 输入数据不存在: {input_data_path}")
            return
        
        if operation_type in ["insert", "both"]:
            for country in insert_countries:
                self._process_single_country(
                    country=country,
                    input_data=input_data_path,
                    output_base_dir=output_base_dir,
                    data_type="GCL",
                    year=year,
                    use_mask=False
                )
        
        if operation_type in ["extract", "both"]:
            for country in extract_countries:
                self._process_single_country(
                    country=country,
                    input_data=input_data_path,
                    output_base_dir=output_base_dir,
                    data_type="GCL",
                    year=year,
                    use_mask=True
                )
    
    def _process_single_country(
        self,
        country: str,
        input_data: str,
        output_base_dir: str,
        data_type: str,
        year: int,
        use_mask: bool = False
    ) -> None:
        """处理单个国家数据"""
        country_output_dir = os.path.join(output_base_dir, country)
        os.makedirs(country_output_dir, exist_ok=True)
        
        output_file_name = f"{country}_{data_type}_{year}.shp"
        output_path = os.path.join(country_output_dir, output_file_name)
        
        admin_boundary = self.config.get_admin_boundary_path(country)
        
        if use_mask:
            mask_boundary = self.config.get_mask_boundary_path(country)
            self.extract_by_mask(input_data, admin_boundary, mask_boundary, output_path)
        else:
            self.extract_by_location(input_data, admin_boundary, output_path)
    
    @log_execution
    def extract_gmssd_data(
        self,
        countries: List[str],
        output_base_dir: str,
        operation_type: str = "insert"
    ) -> None:
        """
        提取GMSSD数据
        
        Args:
            countries: 国家代码列表
            output_base_dir: 输出基础目录
            operation_type: 操作类型，可选 'insert', 'extract', 'both'
        """
        origin_data_dir = os.path.join(
            self.config.get_output_path("gmssd_2015"), 
            "_draft"
        )
        
        data_files = []
        for file_name in os.listdir(origin_data_dir):
            if file_name.endswith('.shp'):
                data_files.append(os.path.join(origin_data_dir, file_name))
        
        if not data_files:
            print(f"[WARN]  | 在 {origin_data_dir} 中未找到Shapefile文件")
            return
        
        for country in countries:
            self._process_gmssd_country(
                country=country,
                data_files=data_files,
                output_base_dir=output_base_dir,
                operation_type=operation_type
            )
    
    def _process_gmssd_country(
        self,
        country: str,
        data_files: List[str],
        output_base_dir: str,
        operation_type: str
    ) -> None:
        """处理单个国家的GMSSD数据"""
        country_output_dir = os.path.join(output_base_dir, country)
        os.makedirs(country_output_dir, exist_ok=True)
        
        admin_boundary = self.config.get_admin_boundary_path(country)
        
        for data_file in data_files:
            file_name = os.path.basename(data_file)
            name_parts = file_name.split('_')
            output_file_name = f"{country}_{name_parts[0]}_{name_parts[1]}.shp"
            output_path = os.path.join(country_output_dir, output_file_name)
            
            if operation_type in ["insert", "both"]:
                self.extract_by_location(data_file, admin_boundary, output_path)
            
            if operation_type in ["extract", "both"]:
                mask_boundary = self.config.get_mask_boundary_path(country, "v2")
                self.extract_by_mask(data_file, admin_boundary, mask_boundary, output_path)


if __name__ == "__main__":
    # 数据提取测试
    extractor = DataExtractor()
    
    with TimeTracker("数据提取测试"):
        test_countries = ["ATG", "BHS"]
        extractor.extract_gcl_fcs30_data(
            countries=test_countries,
            year=2020,
            output_base_dir=r"E:\test_output",
            operation_type="insert"
        )