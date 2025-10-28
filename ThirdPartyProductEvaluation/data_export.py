#!/usr/bin/env python3
"""
海岸线变化分析系统 - 数据导出功能
提供DBF读取、Excel导出、格式转换等数据导出功能
"""

import os
import pandas as pd
from dbfread import DBF
from typing import List, Dict, Any
from config import ProjectConfig
from utils import TimeTracker, log_execution


class DataExporter:
    """数据导出器"""
    
    def __init__(self) -> None:
        self.config = ProjectConfig()
    
    @log_execution
    def read_dbf_field_value(
        self, 
        dbf_file_path: str, 
        field_name: str
    ) -> float:
        """
        读取DBF文件指定字段的值
        
        Args:
            dbf_file_path: DBF文件路径
            field_name: 字段名称
            
        Returns:
            字段值，如果读取失败返回0
        """
        try:
            if not os.path.exists(dbf_file_path):
                print(f"[WARN]  | DBF文件不存在: {dbf_file_path}")
                return 0.0
            
            table = DBF(dbf_file_path)
            values = [
                record[field_name] for record in table 
                if field_name in record
            ]
            
            return values[0] if values else 0.0
            
        except Exception as error:
            print(f"[ERROR] | 读取DBF文件失败 {dbf_file_path}: {error}")
            return 0.0
    
    @log_execution
    def process_data_for_export(
        self,
        data_directory: str,
        data_categories: List[str],
        countries: List[str]
    ) -> List[List[Any]]:
        """
        处理数据用于导出
        
        Args:
            data_directory: 数据目录
            data_categories: 数据类别列表
            countries: 国家代码列表
            
        Returns:
            二维数据列表
        """
        # 初始化表头
        headers = ["ID", "GID"] + data_categories
        result_data = [headers]
        
        # 处理每个国家
        for index, country in enumerate(countries, 1):
            row_data = [index, country]  # ID和国家代码
            
            # 处理每个数据类别
            for category in data_categories:
                dbf_file_path = os.path.join(
                    data_directory, 
                    category, 
                    f"{country}\_{country}_merge.dbf"
                )
                
                # 读取Leng_Geo字段值
                length_value = self.read_dbf_field_value(dbf_file_path, "Leng_Geo")
                row_data.append(length_value)
            
            result_data.append(row_data)
        
        return result_data
    
    @log_execution
    def export_to_excel(
        self, 
        data: List[List[Any]], 
        output_file_path: str
    ) -> bool:
        """
        导出数据到Excel
        
        Args:
            data: 二维数据列表
            output_file_path: 输出文件路径
            
        Returns:
            导出是否成功
        """
        try:
            # 创建DataFrame
            dataframe = pd.DataFrame(data[1:], columns=data[0])
            
            # 导出到Excel
            dataframe.to_excel(output_file_path, index=False)
            
            print(f"[INFO]  | 数据导出成功: {output_file_path}")
            return True
            
        except Exception as error:
            print(f"[ERROR] | 数据导出失败: {error}")
            return False
    
    @log_execution
    def create_comprehensive_export(
        self,
        output_file_name: str = "coastline_analysis_report.xlsx"
    ) -> bool:
        """
        创建综合导出报告
        
        Args:
            output_file_name: 输出文件名
            
        Returns:
            导出是否成功
        """
        data_categories = [
            "SIDS_CL_10", "SIDS_CL_15", "SIDS_CL_20",
            "GSV", "GMSSD_2015", "OSM",
            "GCL_FCS30_10", "GCL_FCS30_15", "GCL_FCS30_20"
        ]
        
        data_directory = self.config.project_root
        countries = self.config.sids_countries
        
        # 处理数据
        export_data = self.process_data_for_export(
            data_directory=data_directory,
            data_categories=data_categories,
            countries=countries
        )
        
        # 输出数据预览
        print("[INFO]  | 生成的二维数据:")
        for row in export_data[:3]:  # 只显示前3行
            print(f"        | {row}")
        
        # 导出到Excel
        output_path = os.path.join(data_directory, output_file_name)
        return self.export_to_excel(export_data, output_path)


class FormatConverter:
    """格式转换器"""
    
    @staticmethod
    @log_execution
    def convert_dbf_to_dataframe(dbf_file_path: str) -> pd.DataFrame:
        """
        将DBF文件转换为DataFrame
        
        Args:
            dbf_file_path: DBF文件路径
            
        Returns:
            pandas DataFrame
        """
        try:
            records = []
            for record in DBF(dbf_file_path):
                records.append(record)
            
            return pd.DataFrame(records)
            
        except Exception as error:
            print(f"[ERROR] | DBF转换失败: {error}")
            return pd.DataFrame()
    
    @staticmethod
    @log_execution
    def merge_multiple_dbf_files(
        dbf_file_paths: List[str],
        output_excel_path: str
    ) -> bool:
        """
        合并多个DBF文件到单个Excel文件
        
        Args:
            dbf_file_paths: DBF文件路径列表
            output_excel_path: 输出Excel路径
            
        Returns:
            合并是否成功
        """
        try:
            with pd.ExcelWriter(output_excel_path, engine="openpyxl") as writer:
                for i, dbf_path in enumerate(dbf_file_paths):
                    if os.path.exists(dbf_path):
                        sheet_name = f"Sheet_{i+1}"
                        dataframe = FormatConverter.convert_dbf_to_dataframe(dbf_path)
                        
                        if not dataframe.empty:
                            dataframe.to_excel(
                                writer, 
                                sheet_name=sheet_name, 
                                index=False
                            )
            
            print(f"[INFO]  | 多文件合并成功: {output_excel_path}")
            return True
            
        except Exception as error:
            print(f"[ERROR] | 多文件合并失败: {error}")
            return False


if __name__ == "__main__":
    # 数据导出测试
    exporter = DataExporter()
    converter = FormatConverter()
    
    with TimeTracker("数据导出测试"):
        # 测试综合导出
        exporter.create_comprehensive_export("test_export.xlsx")
        
        # 测试DBF读取
        test_dbf_path = r"E:\test_data\test.dbf"
        if os.path.exists(test_dbf_path):
            test_dataframe = converter.convert_dbf_to_dataframe(test_dbf_path)
            print(f"[INFO]  | 测试DataFrame形状: {test_dataframe.shape}")