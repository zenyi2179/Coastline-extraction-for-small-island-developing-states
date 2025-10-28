#!/usr/bin/env python3
"""
海岸线变化分析系统 - 精度评估模块
提供精度统计、误差计算、样本点生成等评估功能
"""

import os
import time
from typing import List, Dict, Any, Optional
import pandas as pd

from config import ProjectConfig, PathConfig
from utils import TimeTracker, DataConversionUtils
from spatial_analysis import StatisticsCalculator, SpatialAnalyzer


class AccuracyEvaluator:
    """精度评估器"""
    
    def __init__(self):
        self.config = ProjectConfig()
        self.path_config = PathConfig()
        self.stats_calculator = StatisticsCalculator()
        self.spatial_analyzer = SpatialAnalyzer()
    
    def generate_sample_points(self, country_code: str, year: int, 
                             sample_line_type: str = "SIDS") -> None:
        """
        生成样本点
        
        Args:
            country_code: 国家代码
            year: 年份
            sample_line_type: 样本线类型 ('SIDS', 'OSM', 'GCL', 'GSV', 'GMSSD')
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始生成 {country_code} {year} 样本点，类型: {sample_line_type}")
            
            work_folder = os.path.join(
                self.path_config.arc_data, "_AccuracyEvaluation", country_code, str(year)
            )
            
            standard_points = os.path.join(work_folder, f"StP_{country_code}_{str(year)[-2:]}.shp")
            
            # 初始化第三方文件夹
            third_party_output = os.path.join(work_folder, "ThirdPartyDataSource")
            os.makedirs(third_party_output, exist_ok=True)
            
            # 配置样本线和样本点路径
            sample_config = self._get_sample_config(country_code, year, sample_line_type, third_party_output)
            
            if sample_config:
                sample_lines, sample_points = sample_config
                self.spatial_analyzer.create_sample_points(standard_points, sample_lines, sample_points)
            
            TimeTracker.end_timing(start_time, "生成样本点")
            print(f"[INFO] | 样本点生成完成: {country_code} {year}")
            
        except Exception as error:
            print(f"[ERROR] | 生成样本点失败: {error}")
            raise
    
    def _get_sample_config(self, country_code: str, year: int, 
                          sample_type: str, third_party_path: str) -> Optional[tuple]:
        """
        获取样本配置
        
        Args:
            country_code: 国家代码
            year: 年份
            sample_type: 样本类型
            third_party_path: 第三方数据路径
            
        Returns:
            样本线路径和样本点路径元组
        """
        year_suffix = str(year)[-2:]
        
        config_map = {
            "SIDS": (
                os.path.join(
                    self.path_config.arc_data, "_ThirdProductEvaluation",
                    f"SIDS_CL_{year_suffix}", country_code, 
                    f"{country_code}_CL_{year_suffix}.shp"
                ),
                os.path.join(
                    self.path_config.arc_data, "_AccuracyEvaluation",
                    country_code, str(year), f"SP_{country_code}_{year_suffix}.shp"
                )
            ),
            "OSM": (
                os.path.join(
                    self.path_config.arc_data, "_ThirdProductEvaluation",
                    "OSM", country_code, f"_{country_code}_merge.shp"
                ),
                os.path.join(third_party_path, f"OSM_SP_{country_code}_{year_suffix}.shp")
            ),
            "GCL": (
                os.path.join(
                    self.path_config.arc_data, "_ThirdProductEvaluation",
                    f"GCL_FCS30_{year_suffix}", country_code, f"_{country_code}_merge.shp"
                ),
                os.path.join(third_party_path, f"GCL_SP_{country_code}_{year_suffix}.shp")
            ),
            "GSV": (
                os.path.join(
                    self.path_config.arc_data, "_ThirdProductEvaluation",
                    "GSV", country_code, f"_{country_code}_merge.shp"
                ),
                os.path.join(third_party_path, f"GSV_SP_{country_code}_{year_suffix}.shp")
            ),
            "GMSSD": (
                os.path.join(
                    self.path_config.arc_data, "_ThirdProductEvaluation",
                    "GMSSD_2015", country_code, f"_{country_code}_merge.shp"
                ),
                os.path.join(third_party_path, f"GMSSD_SP_{country_code}_{year_suffix}.shp")
            )
        }
        
        return config_map.get(sample_type)
    
    def evaluate_country_accuracy(self, country_code: str, year: int) -> Dict[str, Any]:
        """
        评估国家精度
        
        Args:
            country_code: 国家代码
            year: 年份
            
        Returns:
            精度评估结果
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始评估 {country_code} {year} 精度")
            
            evaluation_results = {}
            
            # SIDS数据评估
            sids_folder = os.path.join(
                self.path_config.arc_data, "_AccuracyEvaluation", country_code, str(year)
            )
            sids_dbf = os.path.join(sids_folder, f"SP_{country_code}_{str(year)[-2:]}.dbf")
            
            if os.path.exists(sids_dbf):
                sids_stats = self.stats_calculator.calculate_distance_statistics(sids_dbf)
                evaluation_results["SIDS"] = sids_stats
            
            # 第三方数据评估
            third_party_folder = os.path.join(sids_folder, "ThirdPartyDataSource")
            
            # GCL评估
            gcl_dbf = os.path.join(third_party_folder, f"GCL_SP_{country_code}_{str(year)[-2:]}.dbf")
            if os.path.exists(gcl_dbf):
                gcl_stats = self.stats_calculator.calculate_distance_statistics(gcl_dbf)
                evaluation_results["GCL"] = gcl_stats
            
            # OSM评估 (仅2020年)
            if year == 2020:
                osm_dbf = os.path.join(third_party_folder, f"OSM_SP_{country_code}_{str(year)[-2:]}.dbf")
                if os.path.exists(osm_dbf):
                    osm_stats = self.stats_calculator.calculate_distance_statistics(osm_dbf)
                    evaluation_results["OSM"] = osm_stats
            
            # GSV评估 (仅2015年)
            if year == 2015:
                gsv_dbf = os.path.join(third_party_folder, f"GSV_SP_{country_code}_{str(year)[-2:]}.dbf")
                if os.path.exists(gsv_dbf):
                    gsv_stats = self.stats_calculator.calculate_distance_statistics(gsv_dbf)
                    evaluation_results["GSV"] = gsv_stats
            
            # GMSSD评估 (仅2015年)
            if year == 2015:
                gmssd_dbf = os.path.join(third_party_folder, f"GMSSD_SP_{country_code}_{str(year)[-2:]}.dbf")
                if os.path.exists(gmssd_dbf):
                    gmssd_stats = self.stats_calculator.calculate_distance_statistics(gmssd_dbf)
                    evaluation_results["GMSSD"] = gmssd_stats
            
            TimeTracker.end_timing(start_time, f"评估 {country_code} 精度")
            print(f"[INFO] | {country_code} {year} 精度评估完成")
            
            return evaluation_results
            
        except Exception as error:
            print(f"[ERROR] | 评估 {country_code} 精度失败: {error}")
            return {}


class BatchAccuracyEvaluator:
    """批量精度评估器"""
    
    def __init__(self):
        self.config = ProjectConfig()
        self.evaluator = AccuracyEvaluator()
    
    def evaluate_all_countries(self, years: Optional[List[int]] = None,
                             countries: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        评估所有国家精度
        
        Args:
            years: 年份列表
            countries: 国家列表
            
        Returns:
            所有评估结果
        """
        try:
            start_time = TimeTracker.start_timing()
            
            if years is None:
                years = [2010, 2015, 2020]
            if countries is None:
                countries = self.config.SIDS_COUNTRIES
            
            all_results = {}
            
            for year in years:
                year_results = {}
                for country in countries:
                    print(f"[INFO] | 评估 {country} {year}...")
                    country_results = self.evaluator.evaluate_country_accuracy(country, year)
                    year_results[country] = country_results
                
                all_results[year] = year_results
            
            TimeTracker.end_timing(start_time, "批量精度评估")
            print(f"[INFO] | 批量精度评估完成")
            
            return all_results
            
        except Exception as error:
            print(f"[ERROR] | 批量精度评估失败: {error}")
            return {}
    
    def export_accuracy_statistics(self, years: Optional[List[int]] = None,
                                 countries: Optional[List[str]] = None) -> None:
        """
        导出精度统计信息
        
        Args:
            years: 年份列表
            countries: 国家列表
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始导出精度统计信息")
            
            if years is None:
                years = [2010, 2015, 2020]
            if countries is None:
                countries = self.config.SIDS_COUNTRIES
            
            # 创建输出文件夹
            output_folder = os.path.join(
                self.path_config.base_path, "f_Python", "_ThirdProductEvaluation", 
                "_log", "20250614", "统计文件夹"
            )
            os.makedirs(output_folder, exist_ok=True)
            
            for year in years:
                # SIDS数据统计
                sids_data = []
                for country in countries:
                    folder_path = os.path.join(
                        self.path_config.arc_data, "_AccuracyEvaluation", country, str(year)
                    )
                    dbf_file = os.path.join(folder_path, f"SP_{country}_{str(year)[-2:]}.dbf")
                    
                    statistics = self.evaluator.stats_calculator.calculate_distance_statistics(dbf_file)
                    if statistics:
                        country_data = [year, country] + list(statistics.values())
                        sids_data.append(country_data)
                
                # 保存SIDS统计
                if sids_data:
                    output_file = os.path.join(output_folder, f"SIDS_{year}.xlsx")
                    headers = [
                        'year', 'gid', 'mean_value', 'std_dev', 'rmse', 
                        'percent_30', 'percent_60', 'percent_90',
                        'count_30', 'count_60', 'count_90', 'count_all'
                    ]
                    DataConversionUtils.save_to_excel([headers] + sids_data, output_file)
            
            TimeTracker.end_timing(start_time, "导出精度统计")
            print(f"[INFO] | 精度统计信息导出完成")
            
        except Exception as error:
            print(f"[ERROR] | 导出精度统计信息失败: {error}")
            raise


class DatasetAccuracyCalculator:
    """数据集精度计算器"""
    
    def __init__(self):
        self.config = ProjectConfig()
        self.stats_calculator = StatisticsCalculator()
    
    def calculate_dataset_accuracy(self, dataset_type: str, year: int) -> Dict[str, float]:
        """
        计算数据集精度
        
        Args:
            dataset_type: 数据集类型
            year: 年份
            
        Returns:
            数据集精度统计
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始计算 {dataset_type} {year} 数据集精度")
            
            all_data = []
            
            for country in self.config.SIDS_COUNTRIES:
                folder_path = self._get_dataset_folder_path(dataset_type, country, year)
                dbf_file = self._get_dataset_dbf_file(dataset_type, country, year, folder_path)
                
                if dbf_file and os.path.exists(dbf_file):
                    dbf_table = self.stats_calculator.file_utils.read_dbf_to_list(dbf_file)
                    all_data.extend(dbf_table)
            
            if all_data:
                statistics = self.stats_calculator.calculate_dataset_statistics(all_data)
                TimeTracker.end_timing(start_time, f"计算 {dataset_type} 数据集精度")
                return statistics or {}
            
            TimeTracker.end_timing(start_time, f"计算 {dataset_type} 数据集精度")
            return {}
            
        except Exception as error:
            print(f"[ERROR] | 计算 {dataset_type} 数据集精度失败: {error}")
            return {}
    
    def _get_dataset_folder_path(self, dataset_type: str, country: str, year: int) -> str:
        """获取数据集文件夹路径"""
        base_path = self.path_config.arc_data
        
        if dataset_type == "SIDS":
            return os.path.join(base_path, "_AccuracyEvaluation", country, str(year))
        else:
            return os.path.join(base_path, "_AccuracyEvaluation", country, str(year), "ThirdPartyDataSource")
    
    def _get_dataset_dbf_file(self, dataset_type: str, country: str, year: int, folder_path: str) -> str:
        """获取数据集DBF文件路径"""
        year_suffix = str(year)[-2:]
        
        file_map = {
            "SIDS": f"SP_{country}_{year_suffix}.dbf",
            "GCL": f"GCL_SP_{country}_{year_suffix}.dbf",
            "OSM": f"OSM_SP_{country}_{year_suffix}.dbf",
            "GSV": f"GSV_SP_{country}_{year_suffix}.dbf",
            "GMSSD": f"GMSSD_SP_{country}_{year_suffix}.dbf"
        }
        
        filename = file_map.get(dataset_type)
        return os.path.join(folder_path, filename) if filename else ""


if __name__ == "__main__":
    # 精度评估测试
    print("[INFO] | 精度评估模块加载完成")