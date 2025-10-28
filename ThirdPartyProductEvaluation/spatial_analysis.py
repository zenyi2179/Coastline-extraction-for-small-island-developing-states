#!/usr/bin/env python3
"""
海岸线变化分析系统 - 空间分析功能
提供几何计算、统计分析、数据合并等空间分析功能
"""

import os
import arcpy
from typing import List, Optional
from config import ProjectConfig
from utils import TimeTracker, ArcPyUtils, log_execution


class SpatialAnalyzer:
    """空间分析器"""
    
    def __init__(self) -> None:
        self.config = ProjectConfig()
        self.arcpy_utils = ArcPyUtils()
    
    @log_execution
    def merge_and_calculate_geometry(
        self,
        input_data_list: List[str],
        output_data: str,
        calculate_area: bool = True
    ) -> bool:
        """
        合并数据并计算几何属性
        
        Args:
            input_data_list: 输入数据路径列表
            output_data: 输出数据路径
            calculate_area: 是否计算面积
            
        Returns:
            处理是否成功
        """
        try:
            # 合并要素
            temp_merge = r"in_memory\temp_merge"
            arcpy.management.Merge(
                inputs=input_data_list,
                output=temp_merge
            )
            
            # 融合要素
            arcpy.analysis.PairwiseDissolve(
                in_features=temp_merge,
                out_feature_class=output_data,
                multi_part="MULTI_PART"
            )
            
            # 计算几何属性
            if calculate_area:
                self.arcpy_utils.calculate_geometry_stats(output_data, output_data)
            else:
                arcpy.management.CalculateGeometryAttributes(
                    in_features=output_data,
                    geometry_property=[["Leng_Geo", "LENGTH_GEODESIC"]],
                    length_unit="KILOMETERS",
                    coordinate_format="SAME_AS_INPUT"
                )
            
            print(f"[INFO]  | 合并计算完成: {output_data}")
            return True
            
        except Exception as error:
            print(f"[ERROR] | 合并计算失败: {error}")
            return False
    
    @log_execution
    def process_gsv_data(self, countries: List[str], work_directory: str) -> None:
        """
        处理GSV数据
        
        Args:
            countries: 国家代码列表
            work_directory: 工作目录
        """
        data_categories = ["Continent", "Big", "Small", "VerySmall"]
        
        for country in countries:
            country_directory = os.path.join(work_directory, country)
            
            if not os.path.exists(country_directory):
                print(f"[WARN]  | 国家目录不存在: {country_directory}")
                continue
            
            # 获取符合条件的文件
            selected_files = []
            for file_name in os.listdir(country_directory):
                if file_name.endswith('.shp'):
                    file_base_name = os.path.splitext(file_name)[0]
                    for category in data_categories:
                        if category in file_base_name:
                            selected_files.append(
                                os.path.join(country_directory, file_name)
                            )
                            break
            
            if selected_files:
                output_path = os.path.join(country_directory, f"_{country}_merge.shp")
                self.merge_and_calculate_geometry(selected_files, output_path)
    
    @log_execution
    def process_gmssd_data(self, countries: List[str], work_directory: str) -> None:
        """
        处理GMSSD数据
        
        Args:
            countries: 国家代码列表
            work_directory: 工作目录
        """
        for country in countries:
            country_directory = os.path.join(work_directory, country)
            
            if not os.path.exists(country_directory):
                print(f"[WARN]  | 国家目录不存在: {country_directory}")
                continue
            
            # 获取所有Shapefile文件
            input_files = []
            for file_name in os.listdir(country_directory):
                if file_name.endswith('.shp'):
                    input_files.append(os.path.join(country_directory, file_name))
            
            if input_files:
                output_path = os.path.join(country_directory, f"_{country}_merge.shp")
                self.merge_and_calculate_geometry(input_files, output_path)
    
    @log_execution
    def process_gcl_data(
        self, 
        countries: List[str], 
        year: int, 
        work_directory: str
    ) -> None:
        """
        处理GCL数据
        
        Args:
            countries: 国家代码列表
            year: 处理年份
            work_directory: 工作目录
        """
        for country in countries:
            country_directory = os.path.join(work_directory, country)
            
            if not os.path.exists(country_directory):
                print(f"[WARN]  | 国家目录不存在: {country_directory}")
                continue
            
            # 获取所有Shapefile文件
            input_files = []
            for file_name in os.listdir(country_directory):
                if file_name.endswith('.shp'):
                    input_files.append(os.path.join(country_directory, file_name))
            
            if input_files:
                output_path = os.path.join(country_directory, f"_{country}_merge.shp")
                self.merge_and_calculate_geometry(input_files, output_path)
    
    @log_execution
    def process_sids_coastline(
        self, 
        countries: List[str], 
        year: int, 
        work_directory: str
    ) -> None:
        """
        处理SIDS海岸线数据
        
        Args:
            countries: 国家代码列表
            year: 处理年份
            work_directory: 工作目录
        """
        for country in countries:
            country_directory = os.path.join(work_directory, country)
            input_file = os.path.join(
                country_directory, 
                f"{country}_CL_{str(year)[-2:]}.shp"
            )
            
            if not os.path.exists(input_file):
                print(f"[WARN]  | 海岸线文件不存在: {input_file}")
                continue
            
            output_path = os.path.join(country_directory, f"_{country}_merge_CL.shp")
            self.merge_and_calculate_geometry([input_file], output_path, False)


class GeometryProcessor:
    """几何处理器"""
    
    @staticmethod
    @log_execution
    def feature_to_line(
        input_features: str, 
        output_features: str, 
        preserve_attributes: bool = True
    ) -> bool:
        """
        将要素转换为线
        
        Args:
            input_features: 输入要素
            output_features: 输出要素
            preserve_attributes: 是否保留属性
            
        Returns:
            转换是否成功
        """
        try:
            attribute_option = "ATTRIBUTES" if preserve_attributes else "NO_ATTRIBUTES"
            
            arcpy.management.FeatureToLine(
                in_features=[input_features],
                out_feature_class=output_features,
                attributes=attribute_option
            )
            
            print(f"[INFO]  | 要素转线成功: {output_features}")
            return True
            
        except Exception as error:
            print(f"[ERROR] | 要素转线失败: {error}")
            return False
    
    @staticmethod
    @log_execution
    def clip_features(
        input_features: str, 
        clip_features: str, 
        output_features: str
    ) -> bool:
        """
        裁剪要素
        
        Args:
            input_features: 输入要素
            clip_features: 裁剪要素
            output_features: 输出要素
            
        Returns:
            裁剪是否成功
        """
        try:
            arcpy.analysis.PairwiseClip(
                in_features=input_features,
                clip_features=clip_features,
                out_feature_class=output_features
            )
            
            print(f"[INFO]  | 要素裁剪成功: {output_features}")
            return True
            
        except Exception as error:
            print(f"[ERROR] | 要素裁剪失败: {error}")
            return False


if __name__ == "__main__":
    # 空间分析测试
    analyzer = SpatialAnalyzer()
    geometry_processor = GeometryProcessor()
    
    with TimeTracker("空间分析测试"):
        test_countries = ["ATG", "BHS"]
        
        # 测试GSV数据处理
        test_work_dir = r"E:\test_work_directory"
        analyzer.process_gsv_data(test_countries, test_work_dir)