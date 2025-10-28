#!/usr/bin/env python3
"""
海岸线变化分析系统 - 主程序入口
提供完整的工作流协调和命令行接口
"""

import argparse
import sys
from typing import List, Optional
from config import ProjectConfig
from utils import TimeTracker, log_execution
from data_extraction import DataExtractor
from file_operations import FileManager, BatchProcessor
from spatial_analysis import SpatialAnalyzer
from coastline_processing import CoastlineProcessor
from data_export import DataExporter
from statistics_analysis import StatisticsAnalyzer


class CoastlineAnalysisWorkflow:
    """海岸线分析工作流"""
    
    def __init__(self) -> None:
        self.config = ProjectConfig()
        self.data_extractor = DataExtractor()
        self.file_manager = FileManager()
        self.batch_processor = BatchProcessor()
        self.spatial_analyzer = SpatialAnalyzer()
        self.coastline_processor = CoastlineProcessor()
        self.data_exporter = DataExporter()
        self.statistics_analyzer = StatisticsAnalyzer()
    
    @log_execution
    def run_full_workflow(
        self, 
        years: Optional[List[int]] = None,
        countries: Optional[List[str]] = None
    ) -> None:
        """
        运行完整工作流
        
        Args:
            years: 处理年份列表，为None时使用配置中的所有年份
            countries: 国家代码列表，为None时使用配置中的所有国家
        """
        if years is None:
            years = self.config.processing_years
        
        if countries is None:
            countries = self.config.sids_countries
        
        print(f"[INFO]  | 开始完整工作流")
        print(f"[INFO]  | 处理年份: {years}")
        print(f"[INFO]  | 处理国家: {countries}")
        
        with TimeTracker("完整海岸线分析工作流"):
            # 1. 数据提取阶段
            self._run_data_extraction_phase(years, countries)
            
            # 2. 海岸线处理阶段
            self._run_coastline_processing_phase(years, countries)
            
            # 3. 空间分析阶段
            self._run_spatial_analysis_phase(years, countries)
            
            # 4. 数据导出阶段
            self._run_data_export_phase()
            
            # 5. 统计分析阶段
            self._run_statistics_analysis_phase()
            
            # 6. 清理阶段
            self._run_cleanup_phase()
    
    def _run_data_extraction_phase(self, years: List[int], countries: List[str]) -> None:
        """运行数据提取阶段"""
        print("[INFO]  | 阶段1: 数据提取")
        
        # 提取GCL_FCS30数据
        for year in years:
            output_dir = self.config.get_output_path("gcl_fcs30", year)
            self.data_extractor.extract_gcl_fcs30_data(
                countries=countries,
                year=year,
                output_base_dir=output_dir,
                operation_type="both"
            )
        
        # 提取GMSSD数据
        gmssd_output_dir = self.config.get_output_path("gmssd_2015")
        self.data_extractor.extract_gmssd_data(
            countries=countries,
            output_base_dir=gmssd_output_dir,
            operation_type="both"
        )
    
    def _run_coastline_processing_phase(self, years: List[int], countries: List[str]) -> None:
        """运行海岸线处理阶段"""
        print("[INFO]  | 阶段2: 海岸线处理")
        
        # 处理SIDS海岸线
        self.coastline_processor.batch_process_coastlines_by_year(
            insert_countries=countries,
            extract_countries=countries,  # 可根据需要调整
            years=years,
            operation_type="both"
        )
    
    def _run_spatial_analysis_phase(self, years: List[int], countries: List[str]) -> None:
        """运行空间分析阶段"""
        print("[INFO]  | 阶段3: 空间分析")
        
        # 处理GSV数据
        gsv_output_dir = self.config.get_output_path("gsv")
        self.spatial_analyzer.process_gsv_data(countries, gsv_output_dir)
        
        # 处理GMSSD数据
        gmssd_output_dir = self.config.get_output_path("gmssd_2015")
        self.spatial_analyzer.process_gmssd_data(countries, gmssd_output_dir)
        
        # 处理GCL数据
        for year in years:
            gcl_output_dir = self.config.get_output_path("gcl_fcs30", year)
            self.spatial_analyzer.process_gcl_data(countries, year, gcl_output_dir)
        
        # 处理SIDS海岸线数据
        for year in years:
            sids_cl_output_dir = self.config.get_output_path("sids_cl", year)
            self.spatial_analyzer.process_sids_coastline(
                countries, year, sids_cl_output_dir
            )
    
    def _run_data_export_phase(self) -> None:
        """运行数据导出阶段"""
        print("[INFO]  | 阶段4: 数据导出")
        
        # 创建综合导出报告
        self.data_exporter.create_comprehensive_export()
    
    def _run_statistics_analysis_phase(self) -> None:
        """运行统计分析阶段"""
        print("[INFO]  | 阶段5: 统计分析")
        
        # 生成比较分析报告
        input_excel = os.path.join(
            self.config.project_root, 
            "coastline_analysis_report.xlsx"
        )
        output_excel = os.path.join(
            self.config.project_root, 
            "comparison_analysis.xlsx"
        )
        
        if os.path.exists(input_excel):
            self.statistics_analyzer.generate_comparison_report(
                input_excel, 
                output_excel
            )
    
    def _run_cleanup_phase(self) -> None:
        """运行清理阶段"""
        print("[INFO]  | 阶段6: 清理")
        
        # 清理空文件
        self.file_manager.clean_all_output_directories()
    
    @log_execution
    def run_specific_year(self, year: int) -> None:
        """
        运行特定年份的处理
        
        Args:
            year: 处理年份
        """
        if year not in self.config.processing_years:
            print(f"[ERROR] | 不支持的年份: {year}")
            return
        
        print(f"[INFO]  | 开始处理年份: {year}")
        self.run_full_workflow(years=[year])
    
    @log_execution
    def run_specific_country(self, country: str) -> None:
        """
        运行特定国家的处理
        
        Args:
            country: 国家代码
        """
        if country not in self.config.sids_countries:
            print(f"[ERROR] | 不支持的国家: {country}")
            return
        
        print(f"[INFO]  | 开始处理国家: {country}")
        self.run_full_workflow(countries=[country])


def setup_argument_parser() -> argparse.ArgumentParser:
    """设置命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="海岸线变化分析系统",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--workflow",
        action="store_true",
        help="运行完整工作流"
    )
    
    parser.add_argument(
        "--year",
        type=int,
        help="处理特定年份"
    )
    
    parser.add_argument(
        "--country",
        type=str,
        help="处理特定国家代码"
    )
    
    parser.add_argument(
        "--years",
        type=str,
        help="处理多个年份，用逗号分隔，如：2010,2015,2020"
    )
    
    parser.add_argument(
        "--countries", 
        type=str,
        help="处理多个国家，用逗号分隔，如：ATG,BHS,BLZ"
    )
    
    return parser


def main() -> None:
    """主函数"""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    workflow = CoastlineAnalysisWorkflow()
    
    try:
        if args.workflow:
            # 处理多年份和多国家
            years = None
            countries = None
            
            if args.years:
                years = [int(year.strip()) for year in args.years.split(",")]
            
            if args.countries:
                countries = [country.strip() for country in args.countries.split(",")]
            
            workflow.run_full_workflow(years=years, countries=countries)
        
        elif args.year:
            workflow.run_specific_year(args.year)
        
        elif args.country:
            workflow.run_specific_country(args.country)
        
        else:
            # 默认运行完整工作流
            print("[INFO]  | 未指定参数，运行完整工作流")
            workflow.run_full_workflow()
    
    except KeyboardInterrupt:
        print("\n[INFO]  | 用户中断执行")
    except Exception as error:
        print(f"[ERROR] | 工作流执行失败: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()