#!/usr/bin/env python3
"""
海岸线变化分析系统 - 主程序入口
提供完整的海岸线变化分析工作流和命令行接口
"""

import os
import time
import argparse
from typing import List, Optional

from config import ProjectConfig, PathConfig
from utils import TimeTracker
from data_processing import DataFormatConverter, SubpixelExtractor, PolygonSmoother, Rasterizer
from file_operations import FileManager, BatchProcessor, DataMigrator, SpatialFileOperator
from spatial_analysis import MergeCalculator
from coastline_extraction import CoastlineExtractor, ThresholdExtractor
from accuracy_evaluation import AccuracyEvaluator, BatchAccuracyEvaluator


class CoastlineAnalysisWorkflow:
    """海岸线分析工作流"""
    
    def __init__(self):
        self.config = ProjectConfig()
        self.path_config = PathConfig()
        self.format_converter = DataFormatConverter()
        self.subpixel_extractor = SubpixelExtractor()
        self.polygon_smoother = PolygonSmoother()
        self.rasterizer = Rasterizer()
        self.file_manager = FileManager()
        self.batch_processor = BatchProcessor()
        self.data_migrator = DataMigrator()
        self.spatial_operator = SpatialFileOperator()
        self.merge_calculator = MergeCalculator()
        self.coastline_extractor = CoastlineExtractor()
        self.threshold_extractor = ThresholdExtractor()
        self.accuracy_evaluator = AccuracyEvaluator()
        self.batch_evaluator = BatchAccuracyEvaluator()
    
    def run_full_workflow(self, years: Optional[List[int]] = None,
                         countries: Optional[List[str]] = None) -> None:
        """
        运行完整工作流
        
        Args:
            years: 处理年份列表
            countries: 处理国家列表
        """
        try:
            total_start_time = TimeTracker.start_timing()
            print(f"[INFO] | 开始海岸线变化分析完整工作流")
            
            if years is None:
                years = self.config.PROCESS_YEARS
            if countries is None:
                countries = self.config.SIDS_COUNTRIES
            
            # 1. 数据准备阶段
            print(f"[INFO] | === 阶段1: 数据准备 ===")
            self._prepare_data(years, countries)
            
            # 2. 海岸线提取阶段
            print(f"[INFO] | === 阶段2: 海岸线提取 ===")
            self._extract_coastlines(years, countries)
            
            # 3. 数据处理阶段
            print(f"[INFO] | === 阶段3: 数据处理 ===")
            self._process_data(years, countries)
            
            # 4. 精度评估阶段
            print(f"[INFO] | === 阶段4: 精度评估 ===")
            self._evaluate_accuracy(years, countries)
            
            TimeTracker.end_timing(total_start_time, "完整工作流")
            print(f"[INFO] | 海岸线变化分析完整工作流完成")
            
        except Exception as error:
            print(f"[ERROR] | 完整工作流执行失败: {error}")
            raise
    
    def _prepare_data(self, years: List[int], countries: List[str]) -> None:
        """数据准备阶段"""
        print(f"[INFO] | 创建目录结构...")
        self.batch_processor.create_country_directories(countries)
        
        print(f"[INFO] | 迁移历史文件...")
        self.data_migrator.migrate_historical_files(countries, years)
    
    def _extract_coastlines(self, years: List[int], countries: List[str]) -> None:
        """海岸线提取阶段"""
        # 子像素提取
        def extract_subpixel(country: str, year: int) -> None:
            input_tif = self.path_config.get_country_year_path("tif", country, year)
            output_geojson = self.path_config.get_country_year_path("geojson", country, year)
            
            if os.path.exists(input_tif):
                self.subpixel_extractor.extract_subpixel_contours(
                    input_tif, 0, output_geojson
                )
        
        print(f"[INFO] | 执行子像素提取...")
        self.batch_processor.process_all_countries(extract_subpixel, years, countries)
        
        # GeoJSON转Shapefile
        def convert_geojson(country: str, year: int) -> None:
            input_geojson = self.path_config.get_country_year_path("geojson", country, year)
            output_shp = self.path_config.get_country_year_path("shp_line", country, year)
            
            if os.path.exists(input_geojson):
                self.format_converter.geojson_to_shapefile(input_geojson, output_shp)
        
        print(f"[INFO] | 执行格式转换...")
        self.batch_processor.process_all_countries(convert_geojson, years, countries)
    
    def _process_data(self, years: List[int], countries: List[str]) -> None:
        """数据处理阶段"""
        # 线转面
        def line_to_polygon(country: str, year: int) -> None:
            input_shp = self.path_config.get_country_year_path("shp_line", country, year)
            output_shp = self.path_config.get_country_year_path("shp_polygon", country, year)
            
            if os.path.exists(input_shp):
                self.format_converter.line_to_polygon(input_shp, output_shp)
        
        print(f"[INFO] | 执行线转面...")
        self.batch_processor.process_all_countries(line_to_polygon, years, countries)
        
        # 面平滑
        def smooth_polygon(country: str, year: int) -> None:
            input_shp = self.path_config.get_country_year_path("shp_polygon", country, year)
            output_shp = self.path_config.get_country_year_path("smooth", country, year)
            
            if os.path.exists(input_shp):
                self.polygon_smoother.smooth_polygon(input_shp, output_shp)
        
        print(f"[INFO] | 执行面平滑...")
        self.batch_processor.process_all_countries(smooth_polygon, years, countries)
        
        # 面转线（用于海岸线）
        def polygon_to_line(country: str, year: int) -> None:
            input_shp = self.path_config.get_country_year_path("smooth", country, year)
            output_dir = os.path.join(
                self.path_config.arc_data, "_ThirdProductEvaluation", 
                f"SIDS_CL_{str(year)[-2:]}", country
            )
            output_shp = os.path.join(output_dir, f"{country}_CL_{str(year)[-2:]}.shp")
            
            os.makedirs(output_dir, exist_ok=True)
            
            if os.path.exists(input_shp):
                self.format_converter.polygon_to_line(input_shp, output_shp)
        
        print(f"[INFO] | 执行面转线...")
        self.batch_processor.process_all_countries(polygon_to_line, years, countries)
    
    def _evaluate_accuracy(self, years: List[int], countries: List[str]) -> None:
        """精度评估阶段"""
        print(f"[INFO] | 生成样本点...")
        
        for year in years:
            for country in countries:
                # 生成SIDS样本点
                self.accuracy_evaluator.generate_sample_points(country, year, "SIDS")
                
                # 生成第三方数据样本点
                if year in [2010, 2015, 2020]:
                    self.accuracy_evaluator.generate_sample_points(country, year, "GCL")
                
                if year == 2020:
                    self.accuracy_evaluator.generate_sample_points(country, year, "OSM")
                
                if year == 2015:
                    self.accuracy_evaluator.generate_sample_points(country, year, "GSV")
                    self.accuracy_evaluator.generate_sample_points(country, year, "GMSSD")
        
        print(f"[INFO] | 导出精度统计...")
        self.batch_evaluator.export_accuracy_statistics(years, countries)
    
    def run_specific_year(self, year: int, countries: Optional[List[str]] = None) -> None:
        """
        运行特定年份分析
        
        Args:
            year: 年份
            countries: 国家列表
        """
        if countries is None:
            countries = self.config.SIDS_COUNTRIES
        
        print(f"[INFO] | 开始 {year} 年海岸线分析")
        self.run_full_workflow([year], countries)
    
    def run_specific_country(self, country: str, years: Optional[List[int]] = None) -> None:
        """
        运行特定国家分析
        
        Args:
            country: 国家代码
            years: 年份列表
        """
        if years is None:
            years = self.config.PROCESS_YEARS
        
        print(f"[INFO] | 开始 {country} 海岸线分析")
        self.run_full_workflow(years, [country])


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="海岸线变化分析系统")
    parser.add_argument("--year", type=int, help="处理特定年份")
    parser.add_argument("--country", type=str, help="处理特定国家")
    parser.add_argument("--years", type=str, help="处理年份列表，用逗号分隔")
    parser.add_argument("--countries", type=str, help="处理国家列表，用逗号分隔")
    parser.add_argument("--workflow", action="store_true", help="运行完整工作流")
    
    args = parser.parse_args()
    
    workflow = CoastlineAnalysisWorkflow()
    
    try:
        if args.workflow:
            # 解析年份和国家参数
            years = None
            countries = None
            
            if args.years:
                years = [int(y) for y in args.years.split(",")]
            if args.countries:
                countries = args.countries.split(",")
            
            workflow.run_full_workflow(years, countries)
            
        elif args.year and args.country:
            workflow.run_specific_country(args.country, [args.year])
            
        elif args.year:
            workflow.run_specific_year(args.year)
            
        elif args.country:
            workflow.run_specific_country(args.country)
            
        else:
            print("[INFO] | 海岸线变化分析系统")
            print("[INFO] | 使用 --help 查看使用说明")
            print("[INFO] | 示例: python main.py --workflow --years 2015,2020 --countries ATG,BHS")
            
    except Exception as error:
        print(f"[ERROR] | 程序执行失败: {error}")
        raise


if __name__ == "__main__":
    main()