#!/usr/bin/env python3
"""
海岸线变化分析系统 - 统计分析功能
提供数据统计、比较分析、报告生成等统计分析功能
"""

import pandas as pd
from typing import List, Dict, Tuple
from config import ProjectConfig
from utils import TimeTracker, log_execution


class StatisticsAnalyzer:
    """统计分析器"""
    
    def __init__(self) -> None:
        self.config = ProjectConfig()
    
    @log_execution
    def analyze_max_min_columns(
        self, 
        excel_file_path: str, 
        columns_to_analyze: List[str]
    ) -> pd.DataFrame:
        """
        分析每行的最大值和最小值对应列
        
        Args:
            excel_file_path: Excel文件路径
            columns_to_analyze: 要分析的列名列表
            
        Returns:
            包含分析结果的DataFrame
        """
        try:
            # 读取Excel文件
            dataframe = pd.read_excel(excel_file_path)
            
            results = []
            for _, row in dataframe.iterrows():
                # 获取当前行的指定列数据
                row_data = row[columns_to_analyze]
                
                # 找到最大值和最小值对应的列名
                max_column = row_data.idxmax()
                min_column = row_data.idxmin()
                
                results.append({
                    "ID": row["ID"],
                    "GID": row["GID"],
                    "Max_Value_Column": max_column,
                    "Min_Value_Column": min_column
                })
            
            result_dataframe = pd.DataFrame(results)
            print(f"[INFO]  | 统计分析完成，共处理 {len(results)} 行数据")
            return result_dataframe
            
        except Exception as error:
            print(f"[ERROR] | 统计分析失败: {error}")
            return pd.DataFrame()
    
    @log_execution
    def generate_comparison_report(
        self,
        input_excel_path: str,
        output_excel_path: str,
        comparison_columns: List[str] = None
    ) -> bool:
        """
        生成比较分析报告
        
        Args:
            input_excel_path: 输入Excel文件路径
            output_excel_path: 输出Excel文件路径
            comparison_columns: 比较列列表，为None时使用默认列
            
        Returns:
            报告生成是否成功
        """
        if comparison_columns is None:
            comparison_columns = [
                "SIDS_CL_10", "SIDS_CL_15", "SIDS_CL_20", 
                "GSV", "GMSSD_2015"
            ]
        
        try:
            # 执行最大值最小值分析
            analysis_result = self.analyze_max_min_columns(
                input_excel_path, 
                comparison_columns
            )
            
            if analysis_result.empty:
                print(f"[WARN]  | 分析结果为空，无法生成报告")
                return False
            
            # 保存分析结果
            analysis_result.to_excel(output_excel_path, index=False)
            print(f"[INFO]  | 比较分析报告已生成: {output_excel_path}")
            return True
            
        except Exception as error:
            print(f"[ERROR] | 报告生成失败: {error}")
            return False
    
    @log_execution
    def calculate_basic_statistics(
        self, 
        excel_file_path: str, 
        data_columns: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """
        计算基本统计信息
        
        Args:
            excel_file_path: Excel文件路径
            data_columns: 数据列名列表
            
        Returns:
            包含统计信息的字典
        """
        try:
            dataframe = pd.read_excel(excel_file_path)
            statistics = {}
            
            for column in data_columns:
                if column in dataframe.columns:
                    column_data = dataframe[column]
                    statistics[column] = {
                        "mean": column_data.mean(),
                        "median": column_data.median(),
                        "std": column_data.std(),
                        "min": column_data.min(),
                        "max": column_data.max(),
                        "count": column_data.count()
                    }
            
            # 打印统计摘要
            print("[INFO]  | 基本统计信息:")
            for column, stats in statistics.items():
                print(f"        | {column}: 均值={stats['mean']:.2f}, "
                      f"标准差={stats['std']:.2f}, 数量={stats['count']}")
            
            return statistics
            
        except Exception as error:
            print(f"[ERROR] | 统计计算失败: {error}")
            return {}
    
    @log_execution
    def identify_data_quality_issues(
        self, 
        excel_file_path: str, 
        threshold: float = 0.0
    ) -> pd.DataFrame:
        """
        识别数据质量问题
        
        Args:
            excel_file_path: Excel文件路径
            threshold: 阈值，小于此值的数据视为有问题
            
        Returns:
            包含质量问题数据的DataFrame
        """
        try:
            dataframe = pd.read_excel(excel_file_path)
            
            # 识别零值或接近零值的数据
            quality_issues = dataframe[
                (dataframe.select_dtypes(include=["number"]) <= threshold).any(axis=1)
            ]
            
            issue_count = len(quality_issues)
            print(f"[INFO]  | 发现 {issue_count} 条数据质量问题")
            
            return quality_issues
            
        except Exception as error:
            print(f"[ERROR] | 质量检查失败: {error}")
            return pd.DataFrame()


class ReportGenerator:
    """报告生成器"""
    
    @staticmethod
    @log_execution
    def generate_summary_report(
        statistics: Dict[str, Dict[str, float]],
        output_path: str
    ) -> bool:
        """
        生成摘要报告
        
        Args:
            statistics: 统计信息字典
            output_path: 输出路径
            
        Returns:
            报告生成是否成功
        """
        try:
            summary_data = []
            for column, stats in statistics.items():
                summary_data.append({
                    "数据列": column,
                    "平均值": f"{stats['mean']:.4f}",
                    "中位数": f"{stats['median']:.4f}",
                    "标准差": f"{stats['std']:.4f}",
                    "最小值": f"{stats['min']:.4f}",
                    "最大值": f"{stats['max']:.4f}",
                    "数据量": stats["count"]
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(output_path, index=False)
            print(f"[INFO]  | 摘要报告已生成: {output_path}")
            return True
            
        except Exception as error:
            print(f"[ERROR] | 摘要报告生成失败: {error}")
            return False


if __name__ == "__main__":
    # 统计分析测试
    analyzer = StatisticsAnalyzer()
    report_generator = ReportGenerator()
    
    with TimeTracker("统计分析测试"):
        test_excel_path = r"E:\test_data\test_analysis.xlsx"
        test_columns = ["SIDS_CL_10", "SIDS_CL_15", "GSV"]
        
        # 测试统计分析
        if os.path.exists(test_excel_path):
            analysis_result = analyzer.analyze_max_min_columns(
                test_excel_path, 
                test_columns
            )
            print(f"[INFO]  | 分析结果形状: {analysis_result.shape}")
            
            # 测试统计计算
            statistics = analyzer.calculate_basic_statistics(
                test_excel_path, 
                test_columns
            )