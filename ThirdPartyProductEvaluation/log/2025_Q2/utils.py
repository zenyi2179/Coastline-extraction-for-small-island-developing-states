#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海岸线变化分析项目 - 工具函数模块

作用：提供时间跟踪、文件操作、数据读取等通用功能
主要类：TimeTracker, FileUtils
使用示例：from utils import TimeTracker, read_txt_to_list
"""

import os
import time
from pathlib import Path
from typing import List, Optional, Any, Union
import numpy as np
from dbfread import DBF


class TimeTracker:
    """时间跟踪器"""
    
    def __init__(self, task_name: str = "任务"):
        self.task_name = task_name
        self.start_time: Optional[float] = None
        
    def __enter__(self):
        self.start_time = time.time()
        print(f"[INFO]  | {self.task_name}启动")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            elapsed = time.time() - self.start_time
            hours, remainder = divmod(elapsed, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{int(hours):02d}h{int(minutes):02d}m{int(seconds):02d}s"
            status = "完成" if exc_type is None else "失败"
            print(f"[TIME]  | {self.task_name}{status} | 总耗时: {time_str}")


class FileUtils:
    """文件操作工具类"""
    
    @staticmethod
    def read_txt_to_list(file_path: str) -> List[str]:
        """
        读取文本文件内容为列表
        
        Args:
            file_path: 文本文件路径
            
        Returns:
            行内容组成的字符串列表
            
        Raises:
            FileNotFoundError: 文件不存在
            IOError: 文件读取失败
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return [line.strip() for line in file.readlines()]
        except FileNotFoundError:
            print(f"[ERROR] | 文件不存在: {file_path}")
            raise
        except Exception as e:
            print(f"[ERROR] | 读取文件失败 {file_path}: {e}")
            raise IOError(f"读取文件失败: {file_path}") from e
    
    @staticmethod
    def get_files_absolute_paths(folder_path: str, suffix: Optional[str] = None) -> List[str]:
        """
        获取指定文件夹下所有指定后缀文件的绝对路径
        
        Args:
            folder_path: 指定文件夹路径
            suffix: 文件后缀（可选），如 '.shp'
            
        Returns:
            指定后缀文件的绝对路径列表
        """
        if not os.path.exists(folder_path):
            print(f"[WARN]  | 文件夹不存在: {folder_path}")
            return []
            
        files_paths = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if suffix is None or file.endswith(suffix):
                    absolute_path = os.path.abspath(os.path.join(root, file))
                    files_paths.append(absolute_path)
        return files_paths
    
    @staticmethod
    def read_dbf_to_list(dbf_path: str, should_print: bool = False) -> List[List[Any]]:
        """
        读取 DBF 文件内容为二维列表
        
        Args:
            dbf_path: DBF 文件路径
            should_print: 是否打印内容
            
        Returns:
            二维列表，每个子列表代表一条记录
        """
        try:
            records_list = []
            dbf_table = DBF(dbf_path, encoding='utf-8')
            
            for record in dbf_table:
                records_list.append(list(record.values()))
                
            if should_print:
                print(f"[INFO]  | DBF 记录列表: {records_list}")
                
            return records_list
        except Exception as e:
            print(f"[ERROR] | 读取 DBF 文件失败 {dbf_path}: {e}")
            return []
    
    @staticmethod
    def ensure_directory_exists(file_path: str) -> None:
        """
        确保文件所在目录存在
        
        Args:
            file_path: 文件路径
        """
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            print(f"[INFO]  | 创建目录: {directory}")


def calculate_statistics_from_dbf(dbf_file_path: str) -> Optional[Dict[str, float]]:
    """
    计算 DBF 文件中 NEAR_DIST 列的统计数据
    
    Args:
        dbf_file_path: DBF 文件路径
        
    Returns:
        包含统计数据的字典，失败返回 None
    """
    try:
        near_dist_values = []
        dbf_table = DBF(dbf_file_path, encoding='utf-8')
        
        for record in dbf_table:
            if 'NEAR_DIST' in record:
                value = record['NEAR_DIST']
                if value >= 0:
                    near_dist_values.append(value)
        
        if not near_dist_values:
            return None
            
        values_array = np.array(near_dist_values)
        
        # 计算各阈值计数
        count_30 = np.sum(values_array < 30)
        count_60 = np.sum(values_array < 60)
        count_90 = np.sum(values_array < 90)
        count_120 = np.sum(values_array < 120)
        count_150 = np.sum(values_array < 150)
        
        count_all = len(values_array)
        
        # 计算百分比
        percent_30 = count_30 / count_all * 100
        percent_60 = count_60 / count_all * 100
        percent_90 = count_90 / count_all * 100
        percent_120 = count_120 / count_all * 100
        percent_150 = count_150 / count_all * 100
        
        # 计算统计量
        mean_value = np.mean(values_array)
        std_dev = np.std(values_array)
        rmse = np.sqrt(np.mean(values_array ** 2))
        
        return {
            'count_30': count_30,
            'count_60': count_60,
            'count_90': count_90,
            'count_120': count_120,
            'count_150': count_150,
            'count_all': count_all,
            'percent_30': percent_30,
            'percent_60': percent_60,
            'percent_90': percent_90,
            'percent_120': percent_120,
            'percent_150': percent_150,
            'mean_value': mean_value,
            'std_dev': std_dev,
            'rmse': rmse
        }
        
    except Exception as e:
        print(f"[ERROR] | 计算统计数据失败 {dbf_file_path}: {e}")
        return None