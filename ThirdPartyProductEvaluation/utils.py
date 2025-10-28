#!/usr/bin/env python3
"""
海岸线变化分析系统 - 通用工具函数
提供时间跟踪、文件操作、类型定义等通用功能
"""

import os
import time
import arcpy
from typing import List, Tuple, Optional, Callable, Any
from dataclasses import dataclass
from config import ProjectConfig


@dataclass
class ProcessingResult:
    """处理结果数据类"""
    success: bool
    message: str
    output_path: Optional[str] = None
    file_size: int = 0
    processing_time: float = 0.0


class TimeTracker:
    """时间跟踪器"""
    
    def __init__(self, task_name: str) -> None:
        self.task_name = task_name
        self.start_time = time.time()
    
    def __enter__(self) -> "TimeTracker":
        print(f"[INFO]  | 开始执行: {self.task_name}")
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        elapsed_time = time.time() - self.start_time
        elapsed_str = time.strftime("%Hh%Mm%Ss", time.gmtime(elapsed_time))
        status = "完成" if exc_type is None else "失败"
        print(f"[INFO]  | {self.task_name} {status} | 耗时: {elapsed_str}")


class FileUtils:
    """文件操作工具类"""
    
    @staticmethod
    def ensure_directory_exists(directory_path: str) -> None:
        """确保目录存在"""
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            print(f"[INFO]  | 创建目录: {directory_path}")
    
    @staticmethod
    def get_shapefiles_in_directory(directory_path: str) -> List[str]:
        """获取目录中的所有Shapefile文件"""
        if not os.path.exists(directory_path):
            return []
        
        shapefiles = []
        for file_name in os.listdir(directory_path):
            if file_name.endswith('.shp'):
                shapefiles.append(os.path.join(directory_path, file_name))
        
        return shapefiles
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """获取文件大小（字节）"""
        try:
            return os.path.getsize(file_path)
        except OSError as error:
            print(f"[ERROR] | 无法获取文件大小: {file_path}, 错误: {error}")
            return 0
    
    @staticmethod
    def delete_file_and_associated_files(file_path: str) -> bool:
        """删除文件及其关联文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"[INFO]  | 已删除: {file_path}")
            
            # 删除关联文件
            base_name = os.path.splitext(file_path)[0]
            for extension in ['.dbf', '.shx', '.prj', '.cpg', '.xml']:
                associated_file = base_name + extension
                if os.path.exists(associated_file):
                    os.remove(associated_file)
                    print(f"[INFO]  | 已删除关联文件: {associated_file}")
            
            return True
        except Exception as error:
            print(f"[ERROR] | 删除文件时出错: {file_path}, 错误: {error}")
            return False


class ArcPyUtils:
    """ArcPy工具类"""
    
    def __init__(self) -> None:
        arcpy.env.overwriteOutput = True
    
    @staticmethod
    def clear_selection(layer: Any) -> None:
        """清除图层选择"""
        try:
            arcpy.SelectLayerByAttribute_management(layer, "CLEAR_SELECTION")
        except Exception as error:
            print(f"[WARN]  | 清除选择失败: {error}")
    
    @staticmethod
    def calculate_geometry_stats(feature_class: str, output_class: str) -> str:
        """计算几何统计信息"""
        return arcpy.management.CalculateGeometryAttributes(
            in_features=feature_class,
            geometry_property=[
                ["Leng_Geo", "LENGTH_GEODESIC"], 
                ["Area_Geo", "AREA_GEODESIC"]
            ],
            length_unit="KILOMETERS", 
            area_unit="SQUARE_KILOMETERS", 
            coordinate_format="SAME_AS_INPUT"
        )[0]


def log_execution(func: Callable) -> Callable:
    """执行日志装饰器"""
    
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        function_name = func.__name__
        print(f"[INFO]  | 开始执行函数: {function_name}")
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            elapsed_str = time.strftime("%Hh%Mm%Ss", time.gmtime(elapsed_time))
            print(f"[INFO]  | 函数 {function_name} 执行成功 | 耗时: {elapsed_str}")
            return result
        except Exception as error:
            elapsed_time = time.time() - start_time
            elapsed_str = time.strftime("%Hh%Mm%Ss", time.gmtime(elapsed_time))
            print(f"[ERROR] | 函数 {function_name} 执行失败 | 耗时: {elapsed_str} | 错误: {error}")
            raise
    
    return wrapper


if __name__ == "__main__":
    # 工具函数测试
    with TimeTracker("工具函数测试"):
        test_dir = r"E:\test_directory"
        FileUtils.ensure_directory_exists(test_dir)
        file_size = FileUtils.get_file_size(__file__)
        print(f"[INFO]  | 当前文件大小: {file_size} 字节")