# file_utils.py
#!/usr/bin/env python3
"""
文件操作工具模块
提供文件路径处理、格式转换、批量操作等通用功能
"""

import os
import json
import arcpy
from typing import List, Optional, Dict, Any
from pathlib import Path

from config import ProjectConfig


class FileOperations:
    """文件操作工具类"""
    
    @staticmethod
    def get_files_with_extension(directory: str, extension: str) -> List[str]:
        """
        获取指定文件夹中具有特定扩展名的所有文件名
        
        Args:
            directory: 文件夹路径
            extension: 文件扩展名（包括点，例如 '.shp'）
            
        Returns:
            包含指定扩展名文件名的列表
        """
        directory = os.path.normpath(directory)
        
        if not os.path.exists(directory):
            print(f"[WARN]  | 目录不存在: {directory}")
            return []
        
        all_files = os.listdir(directory)
        files_with_extension = [
            file for file in all_files 
            if file.endswith(extension)
        ]
        
        print(f"[INFO]  | 在 {directory} 中找到 {len(files_with_extension)} 个 {extension} 文件")
        return files_with_extension
    
    @staticmethod
    def ensure_directory_exists(directory_path: str) -> bool:
        """
        确保目录存在，如果不存在则创建
        
        Args:
            directory_path: 目录路径
            
        Returns:
            是否成功确保目录存在
        """
        try:
            os.makedirs(directory_path, exist_ok=True)
            return True
        except Exception as e:
            print(f"[ERROR] | 创建目录失败 {directory_path}: {e}")
            return False
    
    @staticmethod
    def construct_output_path(base_dir: str, sub_dir: str, filename: str) -> str:
        """
        构建输出文件路径
        
        Args:
            base_dir: 基础目录
            sub_dir: 子目录
            filename: 文件名
            
        Returns:
            完整的输出文件路径
        """
        output_dir = os.path.join(base_dir, sub_dir)
        FileOperations.ensure_directory_exists(output_dir)
        return os.path.join(output_dir, filename)


class ShapefileToGeoJSONConverter:
    """Shapefile 到 GeoJSON 转换器"""
    
    def __init__(self):
        """初始化转换器"""
        arcpy.env.overwriteOutput = True
    
    def convert_shp_to_geojson(self, shp_path: str, json_path: str) -> bool:
        """
        将 Shapefile 转换为 GeoJSON 文件
        
        Args:
            shp_path: 输入的 Shapefile 文件路径
            json_path: 输出的 GeoJSON 文件路径
            
        Returns:
            转换是否成功
        """
        try:
            print(f"[INFO]  | 开始转换 Shapefile 到 GeoJSON: {shp_path}")
            
            arcpy.conversion.FeaturesToJSON(
                in_features=shp_path,
                out_json_file=json_path,
                format_json="NOT_FORMATTED",
                geoJSON="GEOJSON",
                outputToWGS84="WGS84",
                use_field_alias="USE_FIELD_NAME"
            )
            
            print(f"[INFO]  | 转换完成: {json_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] | Shapefile 转换失败 {shp_path}: {e}")
            return False
    
    def batch_convert_shp_to_geojson(self, shp_directory: str, json_directory: str) -> int:
        """
        批量转换 Shapefile 到 GeoJSON
        
        Args:
            shp_directory: Shapefile 目录
            json_directory: GeoJSON 输出目录
            
        Returns:
            成功转换的文件数量
        """
        FileOperations.ensure_directory_exists(json_directory)
        
        shp_files = FileOperations.get_files_with_extension(shp_directory, ".shp")
        success_count = 0
        
        for shp_file in shp_files:
            # 生成对应的 GeoJSON 文件名
            geo_name = shp_file.replace(".shp", ".geojson")
            
            # 构建完整的文件路径
            feature_shp = os.path.join(shp_directory, shp_file)
            feature_geojson = os.path.join(json_directory, geo_name)
            
            if self.convert_shp_to_geojson(feature_shp, feature_geojson):
                success_count += 1
        
        print(f"[INFO]  | 批量转换完成: {success_count}/{len(shp_files)} 个文件成功")
        return success_count


class GeoJSONProcessor:
    """GeoJSON 处理器"""
    
    @staticmethod
    def load_geojson(geojson_path: str) -> Optional[Dict[str, Any]]:
        """
        加载 GeoJSON 文件
        
        Args:
            geojson_path: GeoJSON 文件路径
            
        Returns:
            GeoJSON 数据字典，失败返回 None
        """
        try:
            with open(geojson_path, "r", encoding="utf-8") as file:
                geojson_data = json.load(file)
            return geojson_data
        except Exception as e:
            print(f"[ERROR] | 加载 GeoJSON 失败 {geojson_path}: {e}")
            return None
    
    @staticmethod
    def save_geojson(geojson_data: Dict[str, Any], geojson_path: str) -> bool:
        """
        保存 GeoJSON 文件
        
        Args:
            geojson_data: GeoJSON 数据
            geojson_path: 保存路径
            
        Returns:
            保存是否成功
        """
        try:
            # 确保目录存在
            FileOperations.ensure_directory_exists(os.path.dirname(geojson_path))
            
            with open(geojson_path, "w", encoding="utf-8") as file:
                json.dump(geojson_data, file, indent=2, ensure_ascii=False)
            
            print(f"[INFO]  | GeoJSON 保存成功: {geojson_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] | 保存 GeoJSON 失败 {geojson_path}: {e}")
            return False


if __name__ == "__main__":
    # 测试文件操作
    converter = ShapefileToGeoJSONConverter()
    
    # 测试批量转换
    shp_dir = os.path.join(ProjectConfig.ARC_DATA_PATH, "b_Global_Island_Grid", "_DGS_GSV_Grids")
    json_dir = os.path.join(ProjectConfig.ARC_DATA_PATH, "b_Global_Island_Grid", "_DGS_GSV_Geojson")
    
    if os.path.exists(shp_dir):
        success_count = converter.batch_convert_shp_to_geojson(shp_dir, json_dir)
        print(f"[INFO]  | 测试完成: {success_count} 个文件转换成功")
    else:
        print(f"[WARN]  | 测试目录不存在: {shp_dir}")