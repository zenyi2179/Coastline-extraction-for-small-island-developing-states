#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海岸线变化分析项目 - 工作流调度模块

作用：完整海岸线变化分析工作流调度和主程序入口
主要类：WorkflowOrchestrator
使用示例：python workflow_orchestrator.py --years 2015,2020 --countries ATG,BHS
"""

import os
import argparse
from typing import List, Optional
from dbfread import DBF

from config import PROJECT_CONFIG
from utils import TimeTracker, FileUtils
from raster_processing import RasterPreprocessor
from vector_processing import VectorConverter, GeometryFixer, select_polygons_by_location
from coastline_extraction import CoastlineExtractor, smooth_polygon_features
from accuracy_evaluation import AccuracyEvaluator, SamplePointGenerator


class WorkflowOrchestrator:
    """工作流调度器"""
    
    def __init__(self):
        self.config = PROJECT_CONFIG
        self.raster_processor = RasterPreprocessor()
        self.vector_converter = VectorConverter()
        self.geometry_fixer = GeometryFixer()
        self.coastline_extractor = CoastlineExtractor()
        self.accuracy_evaluator = AccuracyEvaluator()
        self.sample_generator = SamplePointGenerator()
    
    def run_complete_workflow(self, 
                            years: Optional[List[str]] = None,
                            countries: Optional[List[str]] = None) -> None:
        """
        运行完整工作流
        
        Args:
            years: 处理的年份列表
            countries: 处理的国家列表
        """
        if years is None:
            years = self.config.processing.YEARS
        if countries is None:
            countries = self.config.SIDS_LIST
            
        with TimeTracker("完整海岸线分析工作流"):
            for year in years:
                for country in countries:
                    print(f"[INFO]  | 处理国家: {country}, 年份: {year}")
                    try:
                        self._process_single_country_year(country, year)
                    except Exception as e:
                        print(f"[ERROR] | 处理 {country} {year} 失败: {e}")
                        continue
    
    def _process_single_country_year(self, country: str, year: str) -> None:
        """处理单个国家年份的数据"""
        # 1. 获取国家图幅列表
        map_list = self._get_country_maps(country)
        
        for map_name in map_list:
            try:
                # 2. 栅格数据预处理
                self._preprocess_raster_data(country, year, map_name)
                
                # 3. 栅格转矢量并筛选
                self._convert_and_filter_vectors(country, year, map_name)
                
                # 4. 修复几何并重新栅格化
                self._fix_geometry_and_rasterize(country, year, map_name)
                
                # 5. 海岸线提取
                self._extract_coastline(country, year, map_name)
                
            except Exception as e:
                print(f"[ERROR] | 处理图幅 {map_name} 失败: {e}")
                continue
        
        # 6. 合并和后期处理
        self._merge_and_postprocess(country, year)
        
        # 7. 精度评估
        self._evaluate_accuracy(country, year)
    
    def _get_country_maps(self, country: str) -> List[str]:
        """获取国家图幅列表"""
        dbf_path = f"./SIDS_grid_link/{country}_grid.dbf"
        records = FileUtils.read_dbf_to_list(dbf_path)
        return [record[4] for record in records] if records else []
    
    def _preprocess_raster_data(self, country: str, year: str, map_name: str) -> None:
        """预处理栅格数据"""
        extract_threshold = self.config.processing.EXTRACT_THRESHOLDS.get(year, 0.0)
        filter_threshold = self.config.processing.MEDIAN_FILTER_THRESHOLD
        
        input_tif = os.path.join(
            self.config.paths.GEE_DATA,
            f'SIDs_Grid_Y{year[-2:]}',
            f'{map_name}_ls578_Index.tif'
        )
        output_tif = os.path.join(
            self.config.paths.TEMP_DIR,
            'a_tif_GeeData',
            country, year,
            f'{country}_{map_name}.tif'
        )
        
        self.raster_processor.preprocess_tif(
            input_tif, output_tif, extract_threshold, filter_threshold
        )
    
    def _convert_and_filter_vectors(self, country: str, year: str, map_name: str) -> None:
        """转换并筛选矢量数据"""
        input_tif = os.path.join(
            self.config.paths.TEMP_DIR,
            'a_tif_GeeData', country, year,
            f'{country}_{map_name}.tif'
        )
        temp_shp = os.path.join(
            self.config.paths.DRAFT_DIR,
            f'{country}_{map_name}.shp'
        )
        country_shp = os.path.join(
            self.config.paths.SIDS_BOUNDARY,
            country, f'{country}_20.shp'
        )
        output_shp = os.path.join(
            self.config.paths.TEMP_DIR,
            'b_shp_GeeData', country, year,
            f'{country}_{map_name}.shp'
        )
        
        self.vector_converter.raster_to_vector_polygons(input_tif, temp_shp)
        select_polygons_by_location(temp_shp, country_shp, output_shp)
    
    def _fix_geometry_and_rasterize(self, country: str, year: str, map_name: str) -> None:
        """修复几何并重新栅格化"""
        input_shp = os.path.join(
            self.config.paths.TEMP_DIR,
            'b_shp_GeeData', country, year,
            f'{country}_{map_name}.shp'
        )
        fixed_shp = os.path.join(
            self.config.paths.TEMP_DIR,
            'c_shp_fixed', country, year,
            f'{country}_{map_name}.shp'
        )
        output_tif = os.path.join(
            self.config.paths.TEMP_DIR,
            'd_tif_fixed', country, year,
            f'{country}_{map_name}.tif'
        )
        reference_raster = os.path.join(
            self.config.paths.TEMP_DIR,
            '_draft', '_reference_raster.tif'
        )
        
        self.geometry_fixer.fix_holes_in_shapefile(input_shp, fixed_shp)
        self.vector_converter.vector_to_raster(fixed_shp, output_tif, reference_raster)
    
    def _extract_coastline(self, country: str, year: str, map_name: str) -> None:
        """提取海岸线"""
        input_tif = os.path.join(
            self.config.paths.TEMP_DIR,
            'd_tif_fixed', country, year,
            f'{country}_{map_name}.tif'
        )
        output_shp = os.path.join(
            self.config.paths.TEMP_DIR,
            'e_shp_subpixel', country, year,
            f'{country}_{map_name}.shp'
        )
        
        self.coastline_extractor.extract_coastline_polygons(input_tif, output_shp)
    
    def _merge_and_postprocess(self, country: str, year: str) -> None:
        """合并和后期处理"""
        input_folder = os.path.join(
            self.config.paths.TEMP_DIR,
            'g_shp_polygon', country, year
        )
        extra_shp = os.path.join(
            self.config.paths.TEMP_DIR,
            'g_shp_polygon', country, f'{country}_add.shp'
        )
        merged_shp = os.path.join(
            self.config.paths.DRAFT_DIR,
            f'{country}_{year}.shp'
        )
        fixed_shp = os.path.join(
            self.config.paths.TEMP_DIR,
            'h_shp_merge', country, f'{country}_{year}.shp'
        )
        smooth_shp = os.path.join(
            self.config.paths.TEMP_DIR,
            'i_shp_smooth', country, f'{country}_BV_{year}.shp'
        )
        
        self.geometry_fixer.merge_shapefiles_geopandas(input_folder, merged_shp, extra_shp)
        self.geometry_fixer.fix_shapefile_geometry(merged_shp, fixed_shp)
        smooth_polygon_features(fixed_shp, smooth_shp, self.config.processing.SMOOTH_TOLERANCE)
    
    def _evaluate_accuracy(self, country: str, year: str) -> None:
        """精度评估"""
        # 这里可以调用精度评估相关功能
        print(f"[INFO]  | 精度评估: {country} {year}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='海岸线变化分析工作流')
    parser.add_argument('--years', type=str, help='处理的年份，用逗号分隔')
    parser.add_argument('--countries', type=str, help='处理的国家，用逗号分隔')
    parser.add_argument('--workflow', action='store_true', help='运行完整工作流')
    
    args = parser.parse_args()
    
    orchestrator = WorkflowOrchestrator()
    
    if args.workflow:
        years = args.years.split(',') if args.years else None
        countries = args.countries.split(',') if args.countries else None
        orchestrator.run_complete_workflow(years, countries)
    else:
        print("使用 --workflow 参数运行完整工作流")


if __name__ == "__main__":
    main()