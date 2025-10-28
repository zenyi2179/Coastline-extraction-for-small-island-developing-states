#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海岸线变化分析项目 - 文件操作模块

作用：文件管理、批量处理、数据迁移、空间文件操作
主要类：FileManager, BatchProcessor
使用示例：from file_operations import FileManager, delete_folder
"""

import os
import shutil
from typing import List, Optional
import arcpy

from config import PROJECT_CONFIG
from utils import FileUtils, TimeTracker


class FileManager:
    """文件管理器"""
    
    def __init__(self):
        self.paths = PROJECT_CONFIG.paths
        
    def delete_folder(self, folder_path: str) -> None:
        """
        删除文件夹及其内容
        
        Args:
            folder_path: 文件夹路径
        """
        try:
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
                print(f"[INFO]  | 文件夹已删除: {folder_path}")
            else:
                print(f"[WARN]  | 文件夹不存在: {folder_path}")
        except PermissionError:
            print(f"[ERROR] | 没有权限删除文件夹: {folder_path}")
        except Exception as e:
            print(f"[ERROR] | 删除文件夹失败 {folder_path}: {e}")
    
    def cleanup_temp_files(self, folder_path: str) -> None:
        """
        清理临时文件
        
        Args:
            folder_path: 文件夹路径
        """
        temp_files = FileUtils.get_files_absolute_paths(folder_path)
        for file_path in temp_files:
            if 'temp' in os.path.basename(file_path).lower():
                try:
                    os.remove(file_path)
                    print(f"[INFO]  | 删除临时文件: {file_path}")
                except Exception as e:
                    print(f"[WARN]  | 删除临时文件失败 {file_path}: {e}")


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self):
        self.file_utils = FileUtils()
        self.file_manager = FileManager()
        
    def process_sids_countries(self, 
                             years: Optional[List[str]] = None,
                             countries: Optional[List[str]] = None) -> None:
        """
        批量处理 SIDS 国家数据
        
        Args:
            years: 处理的年份列表，默认为所有年份
            countries: 处理的国家列表，默认为所有国家
        """
        if years is None:
            years = PROJECT_CONFIG.processing.YEARS
        if countries is None:
            countries = PROJECT_CONFIG.SIDS_LIST
            
        with TimeTracker("批量处理SIDS国家数据"):
            for year in years:
                for country in countries:
                    print(f"[INFO]  | 处理国家: {country}, 年份: {year}")
                    # 这里可以调用具体的数据处理流程
                    
    def batch_delete_evaluation_folders(self, 
                                      years: Optional[List[int]] = None,
                                      countries: Optional[List[str]] = None) -> None:
        """
        批量删除精度评估文件夹
        
        Args:
            years: 年份列表
            countries: 国家列表
        """
        if years is None:
            years = [2000, 2010, 2015, 2020]
        if countries is None:
            countries = PROJECT_CONFIG.SIDS_LIST
            
        with TimeTracker("批量删除评估文件夹"):
            for country in countries:
                for year in years:
                    folder_path = os.path.join(
                        PROJECT_CONFIG.paths.ACCURACY_EVALUATION, 
                        country, 
                        str(year)
                    )
                    self.file_manager.delete_folder(folder_path)


def merge_shapefiles_arcpy(input_features: List[str], output_feature: str) -> None:
    """
    使用 ArcPy 合并多个 Shapefile
    
    Args:
        input_features: 输入要素列表
        output_feature: 输出要素路径
    """
    try:
        arcpy.env.overwriteOutput = True
        FileUtils.ensure_directory_exists(output_feature)
        
        arcpy.management.Merge(
            inputs=input_features,
            output=output_feature
        )
        print(f"[INFO]  | Shapefile 合并完成: {output_feature}")
    except Exception as e:
        print(f"[ERROR] | 合并 Shapefile 失败: {e}")
        raise


def export_features_arcpy(input_features: str, output_features: str) -> None:
    """
    使用 ArcPy 导出要素
    
    Args:
        input_features: 输入要素路径
        output_features: 输出要素路径
    """
    try:
        arcpy.env.overwriteOutput = True
        FileUtils.ensure_directory_exists(output_features)
        
        arcpy.conversion.ExportFeatures(
            in_features=input_features,
            out_features=output_features
        )
        print(f"[INFO]  | 要素导出完成: {output_features}")
    except Exception as e:
        print(f"[ERROR] | 导出要素失败: {e}")
        raise