#!/usr/bin/env python3
"""
海岸线变化分析系统 - 文件操作模块
提供文件管理、批量处理、数据迁移等功能
"""

import os
import shutil
from typing import List, Optional
import arcpy

from config import ProjectConfig, PathConfig
from utils import FileUtils, TimeTracker


class FileManager:
    """文件管理器"""
    
    def __init__(self):
        self.path_config = PathConfig()
    
    def copy_and_rename_files(self, source_dir: str, destination_dir: str, 
                             old_prefix: str, new_prefix: str) -> None:
        """
        复制并重命名文件
        
        Args:
            source_dir: 源目录
            destination_dir: 目标目录
            old_prefix: 原前缀
            new_prefix: 新前缀
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始文件复制重命名: {source_dir}")
            
            # 创建目标目录
            if not os.path.exists(destination_dir):
                os.makedirs(destination_dir)
                print(f"[INFO] | 创建目标目录: {destination_dir}")
            
            copied_count = 0
            
            for filename in os.listdir(source_dir):
                if filename.startswith(old_prefix):
                    # 构建新文件名
                    new_filename = filename.replace(old_prefix, new_prefix, 1)
                    
                    source_path = os.path.join(source_dir, filename)
                    destination_path = os.path.join(destination_dir, new_filename)
                    
                    # 复制文件
                    shutil.copy2(source_path, destination_path)
                    copied_count += 1
                    print(f"[INFO] | 复制重命名: {filename} → {new_filename}")
            
            TimeTracker.end_timing(start_time, "文件复制重命名")
            print(f"[INFO] | 文件复制重命名完成，共处理 {copied_count} 个文件")
            
        except Exception as error:
            print(f"[ERROR] | 文件复制重命名失败: {error}")
            raise
    
    def rename_matching_files(self, folder_path: str, old_prefix: str, 
                             new_prefix: str, extensions: Optional[List[str]] = None) -> None:
        """
        批量重命名匹配文件
        
        Args:
            folder_path: 文件夹路径
            old_prefix: 原前缀
            new_prefix: 新前缀
            extensions: 扩展名列表
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始批量重命名: {folder_path}")
            
            renamed_count = 0
            
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                
                if not os.path.isfile(file_path):
                    continue
                
                name, ext = os.path.splitext(filename)
                
                if filename.startswith(old_prefix):
                    # 检查扩展名
                    if extensions is not None:
                        if filename[len(old_prefix):] in extensions:
                            suffix = filename[len(old_prefix):]
                        else:
                            continue
                    else:
                        suffix = filename[len(old_prefix):]
                    
                    # 构建新文件名
                    new_filename = new_prefix + suffix
                    new_file_path = os.path.join(folder_path, new_filename)
                    
                    # 重命名文件
                    os.rename(file_path, new_file_path)
                    renamed_count += 1
                    print(f"[INFO] | 重命名成功: {filename} → {new_filename}")
            
            TimeTracker.end_timing(start_time, "批量重命名")
            print(f"[INFO] | 批量重命名完成，共处理 {renamed_count} 个文件")
            
        except Exception as error:
            print(f"[ERROR] | 批量重命名失败: {error}")
            raise
    
    def cleanup_temp_files(self, temp_directories: List[str]) -> None:
        """
        清理临时文件
        
        Args:
            temp_directories: 临时目录列表
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始清理临时文件")
            
            cleaned_count = 0
            
            for temp_dir in temp_directories:
                if os.path.exists(temp_dir):
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                os.remove(file_path)
                                cleaned_count += 1
                            except Exception as error:
                                print(f"[WARN] | 删除文件失败 {file_path}: {error}")
            
            TimeTracker.end_timing(start_time, "清理临时文件")
            print(f"[INFO] | 临时文件清理完成，共清理 {cleaned_count} 个文件")
            
        except Exception as error:
            print(f"[ERROR] | 清理临时文件失败: {error}")
            raise


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self):
        self.config = ProjectConfig()
        self.path_config = PathConfig()
    
    def process_all_countries(self, process_function, years: Optional[List[int]] = None,
                             countries: Optional[List[str]] = None, **kwargs) -> None:
        """
        批量处理所有国家数据
        
        Args:
            process_function: 处理函数
            years: 年份列表
            countries: 国家列表
            **kwargs: 其他参数
        """
        try:
            start_time = TimeTracker.start_timing()
            
            # 使用默认值
            if years is None:
                years = self.config.PROCESS_YEARS
            if countries is None:
                countries = self.config.SIDS_COUNTRIES
            
            total_tasks = len(years) * len(countries)
            completed_tasks = 0
            
            print(f"[INFO] | 开始批量处理，共 {total_tasks} 个任务")
            
            for year in years:
                for country in countries:
                    try:
                        print(f"[INFO] | 处理 {country} {year}...")
                        process_function(country, year, **kwargs)
                        completed_tasks += 1
                        print(f"[INFO] | 完成 {completed_tasks}/{total_tasks}: {country} {year}")
                        
                    except Exception as error:
                        print(f"[ERROR] | 处理 {country} {year} 失败: {error}")
                        continue
            
            TimeTracker.end_timing(start_time, "批量处理")
            print(f"[INFO] | 批量处理完成，成功 {completed_tasks}/{total_tasks} 个任务")
            
        except Exception as error:
            print(f"[ERROR] | 批量处理失败: {error}")
            raise
    
    def create_country_directories(self, countries: Optional[List[str]] = None) -> None:
        """
        创建国家数据目录结构
        
        Args:
            countries: 国家列表
        """
        try:
            start_time = TimeTracker.start_timing()
            
            if countries is None:
                countries = self.config.SIDS_COUNTRIES
            
            directory_types = [
                "h_SIDS_Tif",
                "GEE_Geojson", 
                "i_SIDS_Line",
                "j_SIDS_Polygon",
                "k_SIDS_Smooth"
            ]
            
            created_count = 0
            
            for country in countries:
                for dir_type in directory_types:
                    dir_path = os.path.join(self.path_config.arc_data, dir_type, country)
                    if not os.path.exists(dir_path):
                        os.makedirs(dir_path)
                        created_count += 1
            
            TimeTracker.end_timing(start_time, "创建目录结构")
            print(f"[INFO] | 目录结构创建完成，共创建 {created_count} 个目录")
            
        except Exception as error:
            print(f"[ERROR] | 创建目录结构失败: {error}")
            raise


class DataMigrator:
    """数据迁移器"""
    
    def __init__(self):
        self.config = ProjectConfig()
        self.path_config = PathConfig()
    
    def migrate_historical_files(self, source_countries: List[str], years: List[int]) -> None:
        """
        迁移历史文件
        
        Args:
            source_countries: 源国家列表
            years: 年份列表
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始历史文件迁移")
            
            migrated_count = 0
            
            for country in source_countries:
                for year in years:
                    # 源目录路径
                    source_folder = os.path.join(
                        self.path_config.arc_data, "f_SIDS_Optimize", country
                    )
                    
                    # 目标目录路径  
                    target_folder = os.path.join(
                        self.path_config.arc_data, "_ThirdProductEvaluation", 
                        f"SIDS_CL_{str(year)[-2:]}", country
                    )
                    
                    # 原始文件名前缀
                    original_prefix = f"{country}_{str(year)[-2:]}"
                    
                    # 新文件名前缀
                    new_prefix = f"{country}_BV_{str(year)[-2:]}"
                    
                    # 执行复制重命名
                    file_manager = FileManager()
                    file_manager.copy_and_rename_files(
                        source_folder, target_folder, original_prefix, new_prefix
                    )
                    
                    migrated_count += 1
            
            TimeTracker.end_timing(start_time, "历史文件迁移")
            print(f"[INFO] | 历史文件迁移完成，共处理 {migrated_count} 个国家-年份组合")
            
        except Exception as error:
            print(f"[ERROR] | 历史文件迁移失败: {error}")
            raise


class SpatialFileOperator:
    """空间文件操作器"""
    
    def __init__(self):
        self.path_config = PathConfig()
    
    def clip_features(self, input_features: str, clip_features: str, 
                     output_features: str) -> None:
        """
        裁剪要素
        
        Args:
            input_features: 输入要素
            clip_features: 裁剪要素
            output_features: 输出要素
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始要素裁剪: {input_features}")
            
            arcpy.env.overwriteOutput = True
            
            # 执行裁剪
            arcpy.analysis.PairwiseClip(
                in_features=input_features,
                clip_features=clip_features,
                out_feature_class=output_features
            )
            
            TimeTracker.end_timing(start_time, "要素裁剪")
            print(f"[INFO] | 要素裁剪完成: {output_features}")
            
        except Exception as error:
            print(f"[ERROR] | 要素裁剪失败: {error}")
            raise
    
    def merge_features(self, input_features_list: List[str], output_features: str) -> None:
        """
        合并要素
        
        Args:
            input_features_list: 输入要素列表
            output_features: 输出要素
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始要素合并，共 {len(input_features_list)} 个要素")
            
            arcpy.env.overwriteOutput = True
            
            # 执行合并
            arcpy.management.Merge(inputs=input_features_list, output=output_features)
            
            TimeTracker.end_timing(start_time, "要素合并")
            print(f"[INFO] | 要素合并完成: {output_features}")
            
        except Exception as error:
            print(f"[ERROR] | 要素合并失败: {error}")
            raise
    
    def dissolve_features(self, input_features: str, output_features: str, 
                         multi_part: str = "MULTI_PART") -> None:
        """
        融合要素
        
        Args:
            input_features: 输入要素
            output_features: 输出要素
            multi_part: 多部分处理选项
        """
        try:
            start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始要素融合: {input_features}")
            
            arcpy.env.overwriteOutput = True
            
            # 执行融合
            arcpy.analysis.PairwiseDissolve(
                in_features=input_features,
                out_feature_class=output_features,
                multi_part=multi_part
            )
            
            TimeTracker.end_timing(start_time, "要素融合")
            print(f"[INFO] | 要素融合完成: {output_features}")
            
        except Exception as error:
            print(f"[ERROR] | 要素融合失败: {error}")
            raise


if __name__ == "__main__":
    # 文件操作测试
    print("[INFO] | 文件操作模块加载完成")