#!/usr/bin/env python3
"""
海岸线变化分析系统 - 空间分析功能
提供空间查询、几何计算、统计分析等空间分析功能
"""

import os
import time
from typing import List, Dict, Any, Tuple, Optional
import arcpy
import numpy as np
import pandas as pd
from dbfread import DBF

from config import ProjectConfig, PathConfig, ProcessingParameters
from utils import TimeTracker, FileUtils


class SpatialAnalyzer:
    """空间分析器"""
    
    def __init__(self):
        self.config = ProjectConfig()
        self.path_config = PathConfig()
    
    def calculate_geometry_attributes(self, input_features: str, output_features: str) -> str:
        """
        计算几何属性
        
        Args:
            input_features: 输入要素路径
            output_features: 输出要素路径
            
        Returns:
            输出要素路径
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始计算几何属性: {input_features}")
            
            arcpy.env.overwriteOutput = True
            
            # 计算几何属性
            result_path = arcpy.management.CalculateGeometryAttributes(
                in_features=input_features,
                geometry_property=[
                    ["Leng_Geo", "PERIMETER_LENGTH_GEODESIC"], 
                    ["Area_Geo", "AREA_GEODESIC"]
                ],
                length_unit="KILOMETERS", 
                area_unit="SQUARE_KILOMETERS", 
                coordinate_format="SAME_AS_INPUT"
            )[0]
            
            TimeTracker.end_timing(start_time, "计算几何属性")
            print(f"[INFO] | 几何属性计算完成: {result_path}")
            
            return result_path
            
        except Exception as error:
            print(f"[ERROR] | 计算几何属性失败: {error}")
            raise
    
    def calculate_line_geometry(self, input_features: str, output_features: str) -> str:
        """
        计算线几何属性
        
        Args:
            input_features: 输入线要素路径
            output_features: 输出要素路径
            
        Returns:
            输出要素路径
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始计算线几何属性: {input_features}")
            
            arcpy.env.overwriteOutput = True
            
            # 计算线几何属性
            result_path = arcpy.management.CalculateGeometryAttributes(
                in_features=input_features,
                geometry_property=[["Leng_Geo", "LENGTH_GEODESIC"]],
                length_unit="KILOMETERS", 
                coordinate_format="SAME_AS_INPUT"
            )[0]
            
            TimeTracker.end_timing(start_time, "计算线几何属性")
            print(f"[INFO] | 线几何属性计算完成: {result_path}")
            
            return result_path
            
        except Exception as error:
            print(f"[ERROR] | 计算线几何属性失败: {error}")
            raise
    
    def select_by_location(self, input_features: str, select_features: str, 
                          output_features: str, overlap_type: str = "INTERSECT") -> None:
        """
        按位置选择要素
        
        Args:
            input_features: 输入要素
            select_features: 选择要素
            output_features: 输出要素
            overlap_type: 重叠类型
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始按位置选择: {input_features}")
            
            arcpy.env.overwriteOutput = True
            
            # 按位置选择
            selected_layer = arcpy.management.SelectLayerByLocation(
                in_layer=[input_features],
                overlap_type=overlap_type,
                select_features=select_features,
                search_distance="1 Kilometers",
                selection_type="NEW_SELECTION"
            )
            
            # 导出选择结果
            arcpy.conversion.ExportFeatures(
                in_features=selected_layer, 
                out_features=output_features
            )
            
            # 清除选择
            arcpy.management.SelectLayerByAttribute(selected_layer, "CLEAR_SELECTION")
            
            TimeTracker.end_timing(start_time, "按位置选择")
            print(f"[INFO] | 按位置选择完成: {output_features}")
            
        except Exception as error:
            print(f"[ERROR] | 按位置选择失败: {error}")
            raise
    
    def create_sample_points(self, input_features: str, near_features: str, 
                           output_points: str, search_radius: str = "500 Meters") -> None:
        """
        创建样本点
        
        Args:
            input_features: 输入要素
            near_features: 邻近要素
            output_points: 输出点要素
            search_radius: 搜索半径
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始创建样本点: {input_features}")
            
            arcpy.env.overwriteOutput = True
            
            # 复制要素
            temp_copy = "in_memory\\temp_copy"
            arcpy.management.CopyFeatures(
                in_features=input_features, 
                out_feature_class=temp_copy
            )
            
            # 邻近分析
            near_result = arcpy.analysis.Near(
                in_features=temp_copy, 
                near_features=[near_features], 
                search_radius=search_radius,
                location="LOCATION", 
                method="GEODESIC",
                field_names=[
                    ["NEAR_FID", "NEAR_FID"], 
                    ["NEAR_DIST", "NEAR_DIST"],
                    ["NEAR_X", "NEAR_X"], 
                    ["NEAR_Y", "NEAR_Y"]
                ]
            )[0]
            
            # XY表转点
            arcpy.management.XYTableToPoint(
                in_table=near_result, 
                out_feature_class=output_points,
                x_field="NEAR_X", 
                y_field="NEAR_Y"
            )
            
            # 清理临时数据
            arcpy.Delete_management(temp_copy)
            
            TimeTracker.end_timing(start_time, "创建样本点")
            print(f"[INFO] | 样本点创建完成: {output_points}")
            
        except Exception as error:
            print(f"[ERROR] | 创建样本点失败: {error}")
            raise


class StatisticsCalculator:
    """统计计算器"""
    
    def __init__(self):
        self.params = ProcessingParameters()
    
    def calculate_distance_statistics(self, dbf_file_path: str) -> Optional[Dict[str, float]]:
        """
        计算距离统计信息
        
        Args:
            dbf_file_path: DBF文件路径
            
        Returns:
            统计信息字典
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始计算距离统计: {dbf_file_path}")
            
            # 读取DBF文件
            dbf_table = DBF(dbf_file_path, encoding='utf-8')
            
            # 提取距离值
            distance_values = []
            for record in dbf_table:
                if 'NEAR_DIST' in record:
                    value = record['NEAR_DIST']
                    if value >= 0:
                        distance_values.append(value)
            
            if not distance_values:
                print(f"[WARN] | 未找到有效的距离数据: {dbf_file_path}")
                return None
            
            # 转换为numpy数组
            distances = np.array(distance_values)
            
            # 计算统计值
            count_30 = np.sum(distances <= 30)
            count_60 = np.sum(distances <= 60)
            count_90 = np.sum(distances <= 90)
            count_all = len(distances)
            
            percent_30 = (count_30 / count_all * 100) if count_all > 0 else 0
            percent_60 = (count_60 / count_all * 100) if count_all > 0 else 0
            percent_90 = (count_90 / count_all * 100) if count_all > 0 else 0
            
            mean_value = np.mean(distances)
            std_dev = np.std(distances)
            rmse = np.sqrt(np.mean(distances ** 2))
            
            statistics = {
                'count_30': count_30,
                'count_60': count_60,
                'count_90': count_90,
                'count_all': count_all,
                'percent_30': percent_30,
                'percent_60': percent_60,
                'percent_90': percent_90,
                'mean_value': mean_value,
                'std_dev': std_dev,
                'rmse': rmse
            }
            
            TimeTracker.end_timing(start_time, "计算距离统计")
            print(f"[INFO] | 距离统计计算完成: {dbf_file_path}")
            
            return statistics
            
        except Exception as error:
            print(f"[ERROR] | 计算距离统计失败: {error}")
            return None
    
    def calculate_dataset_statistics(self, data_2d: List[List[Any]]) -> Optional[Dict[str, float]]:
        """
        计算数据集统计信息
        
        Args:
            data_2d: 二维数据列表
            
        Returns:
            统计信息字典
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始计算数据集统计")
            
            # 提取距离值（假设在第四列）
            distance_values = []
            for record in data_2d:
                if len(record) > 3:
                    value = record[3]
                    if value >= 0:
                        distance_values.append(value)
            
            if not distance_values:
                print(f"[WARN] | 未找到有效的距离数据")
                return None
            
            # 转换为numpy数组并计算统计
            distances = np.array(distance_values)
            
            count_30 = np.sum(distances <= 30)
            count_60 = np.sum(distances <= 60)
            count_90 = np.sum(distances <= 90)
            count_all = len(distances)
            
            percent_30 = (count_30 / count_all * 100) if count_all > 0 else 0
            percent_60 = (count_60 / count_all * 100) if count_all > 0 else 0
            percent_90 = (count_90 / count_all * 100) if count_all > 0 else 0
            
            mean_value = np.mean(distances)
            std_dev = np.std(distances)
            rmse = np.sqrt(np.mean(distances ** 2))
            
            statistics = {
                'count_30': count_30,
                'count_60': count_60,
                'count_90': count_90,
                'count_all': count_all,
                'percent_30': percent_30,
                'percent_60': percent_60,
                'percent_90': percent_90,
                'mean_value': mean_value,
                'std_dev': std_dev,
                'rmse': rmse
            }
            
            TimeTracker.end_timing(start_time, "计算数据集统计")
            print(f"[INFO] | 数据集统计计算完成")
            
            return statistics
            
        except Exception as error:
            print(f"[ERROR] | 计算数据集统计失败: {error}")
            return None


class MergeCalculator:
    """合并计算器"""
    
    def __init__(self):
        self.path_config = PathConfig()
    
    def merge_and_calculate(self, input_data_list: List[str], output_data: str, 
                          geometry_type: str = "polygon") -> None:
        """
        合并要素并计算几何属性
        
        Args:
            input_data_list: 输入数据列表
            output_data: 输出数据路径
            geometry_type: 几何类型 ('polygon' 或 'line')
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始合并计算，共 {len(input_data_list)} 个要素")
            
            arcpy.env.overwriteOutput = True
            
            # 合并要素
            temp_merge = "in_memory\\shp_merge"
            arcpy.management.Merge(inputs=input_data_list, output=temp_merge)
            
            # 融合要素
            temp_dissolve = "in_memory\\shp_dissolve"
            arcpy.analysis.PairwiseDissolve(
                in_features=temp_merge, 
                out_feature_class=temp_dissolve,
                multi_part="MULTI_PART"
            )
            
            # 计算几何属性
            if geometry_type == "polygon":
                result_path = arcpy.management.CalculateGeometryAttributes(
                    in_features=temp_dissolve,
                    geometry_property=[
                        ["Leng_Geo", "PERIMETER_LENGTH_GEODESIC"], 
                        ["Area_Geo", "AREA_GEODESIC"]
                    ],
                    length_unit="KILOMETERS", 
                    area_unit="SQUARE_KILOMETERS", 
                    coordinate_format="SAME_AS_INPUT"
                )[0]
            else:  # line
                result_path = arcpy.management.CalculateGeometryAttributes(
                    in_features=temp_dissolve,
                    geometry_property=[["Leng_Geo", "LENGTH_GEODESIC"]],
                    length_unit="KILOMETERS", 
                    coordinate_format="SAME_AS_INPUT"
                )[0]
            
            # 复制到最终输出
            arcpy.management.CopyFeatures(result_path, output_data)
            
            # 清理临时数据
            for temp_feature in [temp_merge, temp_dissolve]:
                if arcpy.Exists(temp_feature):
                    arcpy.Delete_management(temp_feature)
            
            TimeTracker.end_timing(start_time, "合并计算")
            print(f"[INFO] | 合并计算完成: {output_data}")
            
        except Exception as error:
            print(f"[ERROR] | 合并计算失败: {error}")
            raise
    
    def process_sids_boundary_volume(self, country_list: List[str], year: int) -> None:
        """
        处理SIDS边界体积数据
        
        Args:
            country_list: 国家列表
            year: 年份
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始处理SIDS边界体积数据，年份: {year}")
            
            work_path = os.path.join(
                self.path_config.arc_data, "_ThirdProductEvaluation", 
                f"SIDS_CL_{str(year)[-2:]}"
            )
            
            for country in country_list:
                country_path = os.path.join(work_path, country)
                input_data_list = [
                    os.path.join(country_path, f"{country}_BV_{str(year)[-2:]}.shp")
                ]
                
                output_path = os.path.join(country_path, f"_{country}_merge_BV.shp")
                
                self.merge_and_calculate(input_data_list, output_path, "polygon")
            
            TimeTracker.end_timing(start_time, "处理SIDS边界体积数据")
            print(f"[INFO] | SIDS边界体积数据处理完成")
            
        except Exception as error:
            print(f"[ERROR] | 处理SIDS边界体积数据失败: {error}")
            raise
    
    def process_sids_coastline(self, country_list: List[str], year: int) -> None:
        """
        处理SIDS海岸线数据
        
        Args:
            country_list: 国家列表
            year: 年份
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始处理SIDS海岸线数据，年份: {year}")
            
            work_path = os.path.join(
                self.path_config.arc_data, "_ThirdProductEvaluation", 
                f"SIDS_CL_{str(year)[-2:]}"
            )
            
            for country in country_list:
                country_path = os.path.join(work_path, country)
                input_data_list = [
                    os.path.join(country_path, f"{country}_CL_{str(year)[-2:]}.shp")
                ]
                
                output_path = os.path.join(country_path, f"_{country}_merge_CL.shp")
                
                self.merge_and_calculate(input_data_list, output_path, "line")
            
            TimeTracker.end_timing(start_time, "处理SIDS海岸线数据")
            print(f"[INFO] | SIDS海岸线数据处理完成")
            
        except Exception as error:
            print(f"[ERROR] | 处理SIDS海岸线数据失败: {error}")
            raise


if __name__ == "__main__":
    # 空间分析测试
    print("[INFO] | 空间分析功能模块加载完成")