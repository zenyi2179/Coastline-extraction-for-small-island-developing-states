#!/usr/bin/env python3
"""
海岸线变化分析系统 - 工具函数
提供通用工具函数和辅助方法
"""

import os
import math
import time
from typing import List, Tuple, Optional, Any, Dict
from dbfread import DBF
import pandas as pd


class TimeTracker:
    """时间跟踪器"""
    
    @staticmethod
    def format_time(seconds: float) -> str:
        """
        格式化时间为 HH:MM:SS
        
        Args:
            seconds: 总秒数
            
        Returns:
            格式化时间字符串
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    
    @staticmethod
    def start_timing() -> float:
        """
        开始计时
        
        Returns:
            开始时间戳
        """
        return time.time()
    
    @staticmethod
    def end_timing(start_time: float, task_name: str = "任务") -> None:
        """
        结束计时并打印耗时
        
        Args:
            start_time: 开始时间戳
            task_name: 任务名称
        """
        elapsed_time = time.time() - start_time
        formatted_time = TimeTracker.format_time(elapsed_time)
        print(f"[TIME] | {task_name} 总耗时: {formatted_time}")


class CoordinateUtils:
    """坐标工具类"""
    
    @staticmethod
    def determine_map_position(longitude: float, latitude: float, should_print: bool = True) -> str:
        """
        根据经纬度确定地图位置
        
        Args:
            longitude: 经度
            latitude: 纬度
            should_print: 是否打印结果
            
        Returns:
            地图位置字符串
        """
        abs_lon = int(abs(longitude - 1)) if longitude < 0 else int(abs(longitude))
        abs_lat = int(abs(latitude - 1)) if latitude < 0 else int(abs(latitude))
        
        we_direction = 'W' if longitude < 0 else 'E'
        ns_direction = 'N' if latitude > 0 else 'S'
        
        lr_position = 'l' if longitude < abs_lon + 0.5 else 'r'
        ub_position = 'b' if latitude < abs_lat + 0.5 else 'u'
        
        map_position = f'{abs_lon}{we_direction}{abs_lat}{ns_direction}{lr_position}{ub_position}'
        
        if should_print:
            print(f"[INFO] | 坐标 [{longitude}, {latitude}] 转换为: {map_position}")
        
        return map_position
    
    @staticmethod
    def get_grid_coordinates(longitude: float, latitude: float) -> Tuple[float, float]:
        """
        获取网格坐标
        
        Args:
            longitude: 经度
            latitude: 纬度
            
        Returns:
            网格左下角坐标 (经度, 纬度)
        """
        grid_longitude = math.floor(longitude * 2) / 2
        grid_latitude = math.floor(latitude * 2) / 2
        return grid_longitude, grid_latitude


class FileUtils:
    """文件工具类"""
    
    @staticmethod
    def read_dbf_to_list(dbf_path: str, should_print: bool = False) -> List[List[Any]]:
        """
        读取DBF文件到二维列表
        
        Args:
            dbf_path: DBF文件路径
            should_print: 是否打印内容
            
        Returns:
            二维数据列表
        """
        records_list = []
        try:
            dbf_table = DBF(dbf_path, encoding='utf-8')
            for record in dbf_table:
                records_list.append(list(record.values()))
            
            if should_print:
                print(f"[INFO] | DBF记录列表: {records_list}")
                
        except Exception as error:
            print(f"[ERROR] | 读取DBF文件失败: {error}")
            
        return records_list
    
    @staticmethod
    def list_files_with_extension(folder_path: str, extension: str, should_print: bool = False) -> List[str]:
        """
        获取指定扩展名的文件列表
        
        Args:
            folder_path: 文件夹路径
            extension: 文件扩展名
            should_print: 是否打印列表
            
        Returns:
            匹配的文件名列表
        """
        if not os.path.isdir(folder_path):
            raise ValueError(f"[ERROR] | 路径不存在或不是文件夹: {folder_path}")
        
        matching_files = [
            filename for filename in os.listdir(folder_path) 
            if filename.endswith(extension)
        ]
        
        if should_print:
            print(f"[INFO] | 匹配文件列表: {matching_files}")
            
        return matching_files
    
    @staticmethod
    def get_files_absolute_paths(folder_path: str, suffix: Optional[str] = None) -> List[str]:
        """
        获取文件夹下所有指定后缀文件的绝对路径
        
        Args:
            folder_path: 文件夹路径
            suffix: 文件后缀
            
        Returns:
            绝对路径列表
        """
        absolute_paths = []
        for root_dir, dirs, files in os.walk(folder_path):
            for file in files:
                if suffix is None or file.endswith(suffix):
                    full_path = os.path.abspath(os.path.join(root_dir, file))
                    absolute_paths.append(full_path)
        return absolute_paths


class DataConversionUtils:
    """数据转换工具类"""
    
    @staticmethod
    def read_dbf_field(dbf_file_path: str, field_name: str) -> float:
        """
        读取DBF文件指定字段的第一个值
        
        Args:
            dbf_file_path: DBF文件路径
            field_name: 字段名称
            
        Returns:
            字段值或0
        """
        try:
            dbf_table = DBF(dbf_file_path)
            values = [record[field_name] for record in dbf_table if field_name in record]
            return values[0] if values else 0.0
        except Exception as error:
            print(f"[ERROR] | 读取 {dbf_file_path} 失败: {error}")
            return 0.0
    
    @staticmethod
    def save_to_excel(data: List[List[Any]], output_file: str) -> None:
        """
        将二维列表保存为Excel文件
        
        Args:
            data: 二维数据列表
            output_file: 输出文件路径
        """
        try:
            data_frame = pd.DataFrame(data[1:], columns=data[0])
            data_frame.to_excel(output_file, index=False)
            print(f"[INFO] | 数据已导出到: {output_file}")
        except Exception as error:
            print(f"[ERROR] | 保存Excel失败: {error}")


if __name__ == "__main__":
    # 工具函数测试
    test_coords = (-73.997826, 40.744754)
    position = CoordinateUtils.determine_map_position(test_coords[0], test_coords[1])
    print(f"[TEST] | 坐标转换测试: {position}")
    
    start_time = TimeTracker.start_timing()
    time.sleep(1)
    TimeTracker.end_timing(start_time, "测试任务")