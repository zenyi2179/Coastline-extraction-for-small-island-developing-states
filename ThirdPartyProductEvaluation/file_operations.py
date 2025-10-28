#!/usr/bin/env python3
"""
海岸线变化分析系统 - 文件操作功能
提供文件管理、批量处理、数据清理等文件操作功能
"""

import os
from typing import List
from config import ProjectConfig
from utils import TimeTracker, FileUtils, log_execution


class FileManager:
    """文件管理器"""
    
    def __init__(self) -> None:
        self.config = ProjectConfig()
        self.file_utils = FileUtils()
    
    @log_execution
    def delete_empty_shapefiles(self, directory_path: str) -> int:
        """
        删除空Shapefile文件
        
        Args:
            directory_path: 目录路径
            
        Returns:
            删除的文件数量
        """
        deleted_count = 0
        threshold = self.config.processing_params["empty_file_threshold"]
        
        if not os.path.exists(directory_path):
            print(f"[WARN]  | 目录不存在: {directory_path}")
            return deleted_count
        
        # 获取所有Shapefile文件
        shapefiles = []
        for file_name in os.listdir(directory_path):
            if file_name.endswith('.shp'):
                shapefiles.append(file_name)
        
        print(f"[INFO]  | 在 {directory_path} 中找到 {len(shapefiles)} 个Shapefile文件")
        
        for shapefile in shapefiles:
            shapefile_path = os.path.join(directory_path, shapefile)
            file_size = self.file_utils.get_file_size(shapefile_path)
            
            # 检查文件大小是否小于阈值
            if 0 < file_size <= threshold:
                base_name = os.path.splitext(shapefile)[0]
                deleted_count += self._delete_shapefile_and_associated_files(
                    directory_path, base_name
                )
        
        print(f"[INFO]  | 共删除 {deleted_count} 个空文件")
        return deleted_count
    
    def _delete_shapefile_and_associated_files(
        self, 
        directory_path: str, 
        base_name: str
    ) -> int:
        """删除Shapefile及其关联文件"""
        deleted_count = 0
        
        # 删除所有关联文件
        for file_name in os.listdir(directory_path):
            if file_name.startswith(base_name):
                file_path = os.path.join(directory_path, file_name)
                if self.file_utils.delete_file_and_associated_files(file_path):
                    deleted_count += 1
        
        return deleted_count
    
    @log_execution
    def clean_all_output_directories(self) -> None:
        """清理所有输出目录中的空文件"""
        directories_to_clean = [
            self.config.get_output_path("gmssd_2015"),
            self.config.get_output_path("gsv"),
            self.config.get_output_path("osm"),
        ]
        
        # 添加GCL年份目录
        for year in self.config.processing_years:
            directories_to_clean.append(
                self.config.get_output_path("gcl_fcs30", year)
            )
        
        # 添加SIDS海岸线年份目录
        for year in self.config.processing_years:
            directories_to_clean.append(
                self.config.get_output_path("sids_cl", year)
            )
        
        total_deleted = 0
        for directory in directories_to_clean:
            if os.path.exists(directory):
                deleted_count = self.delete_empty_shapefiles(directory)
                total_deleted += deleted_count
        
        print(f"[INFO]  | 总计删除 {total_deleted} 个空文件")
    
    @log_execution
    def organize_data_by_continent(self) -> None:
        """按大陆组织数据"""
        for continent in self.config.continents:
            continent_path = os.path.join(
                self.config.project_root, 
                f"GMSSD_2015\\{continent}"
            )
            
            if not os.path.exists(continent_path):
                print(f"[WARN]  | 大陆目录不存在: {continent_path}")
                continue
            
            # 获取大陆目录中的所有Shapefile
            shapefiles = self.file_utils.get_shapefiles_in_directory(continent_path)
            print(f"[INFO]  | 在 {continent} 中找到 {len(shapefiles)} 个Shapefile文件")


class BatchProcessor:
    """批处理器"""
    
    def __init__(self) -> None:
        self.config = ProjectConfig()
        self.file_manager = FileManager()
    
    @log_execution
    def process_all_continents(self) -> None:
        """处理所有大陆的数据"""
        sids_boundary_path = self.config.data_sources["sids_boundary"]
        
        for continent in self.config.continents:
            self._process_single_continent(continent, sids_boundary_path)
    
    def _process_single_continent(self, continent: str, boundary_path: str) -> None:
        """处理单个大陆的数据"""
        continent_path = os.path.join(
            self.config.project_root, 
            f"GMSSD_2015\\{continent}"
        )
        
        if not os.path.exists(continent_path):
            print(f"[WARN]  | 大陆目录不存在: {continent_path}")
            return
        
        # 获取所有Shapefile文件
        shapefiles = []
        for file_name in os.listdir(continent_path):
            if file_name.endswith('.shp'):
                shapefiles.append(file_name)
        
        print(f"[INFO]  | 在 {continent} 中找到 {len(shapefiles)} 个Shapefile文件")
        
        # 处理每个Shapefile
        for shapefile in shapefiles:
            input_path = os.path.join(continent_path, shapefile)
            output_dir = os.path.join(
                self.config.get_output_path("gmssd_2015"), 
                "_draft"
            )
            self.file_utils.ensure_directory_exists(output_dir)
            
            output_path = os.path.join(output_dir, shapefile)
            
            # 这里可以调用数据提取功能
            print(f"[INFO]  | 处理: {input_path} -> {output_path}")


if __name__ == "__main__":
    # 文件操作测试
    file_manager = FileManager()
    batch_processor = BatchProcessor()
    
    with TimeTracker("文件操作测试"):
        # 测试清理空文件
        test_dir = r"E:\test_directory"
        file_manager.delete_empty_shapefiles(test_dir)
        
        # 测试批量处理
        batch_processor.process_all_continents()