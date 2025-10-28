# main.py
#!/usr/bin/env python3
"""
海岸线变化分析系统 - 主程序入口
协调完整工作流，提供命令行接口和模块化使用方式
"""

import os
import time
import argparse
from typing import List, Optional
from datetime import datetime

from config import ProjectConfig, ProcessingConfig, SUPPORTED_YEARS, SIDS_COUNTRIES
from auth import initialize_earth_engine
from file_utils import FileOperations
from raster_processing import BandInterpolator, IndexCalculator
from coastline_processing import CoastlineExtractor, SubpixelWaterlineExtractor, CoastlineValidator
from spatial_analysis import SpatialAnalyzer


class CoastlineAnalysisWorkflow:
    """海岸线分析工作流"""
    
    def __init__(self):
        """初始化工作流"""
        self.initialize_components()
        self.setup_directories()
    
    def initialize_components(self) -> None:
        """初始化各个组件"""
        print("[INFO]  | 初始化海岸线分析组件...")
        
        # 初始化 Earth Engine
        if not initialize_earth_engine():
            raise RuntimeError("Earth Engine 初始化失败")
        
        # 初始化处理器
        self.band_interpolator = BandInterpolator()
        self.index_calculator = IndexCalculator()
        self.coastline_extractor = CoastlineExtractor()
        self.subpixel_extractor = SubpixelWaterlineExtractor()
        self.coastline_validator = CoastlineValidator()
        self.spatial_analyzer = SpatialAnalyzer()
        
        print("[INFO]  | 组件初始化完成")
    
    def setup_directories(self) -> None:
        """设置工作目录"""
        print("[INFO]  | 设置工作目录...")
        
        directories = [
            ProjectConfig.TEMP_PATH,
            ProjectConfig.INTERPOLATION_PATH,
            ProjectConfig.MNDWI_PATH,
            ProjectConfig.EXTRACT_PATH,
            ProjectConfig.SUBPIXEL_PATH,
            ProjectConfig.SHAPE_FEATURE_PATH,
            ProjectConfig.OUTPUT_PATH
        ]
        
        for directory in directories:
            FileOperations.ensure_directory_exists(directory)
        
        print("[INFO]  | 工作目录设置完成")
    
    def process_single_island(
        self, 
        input_tif_path: str, 
        year: int, 
        region: str = "Africa"
    ) -> bool:
        """
        处理单个岛屿的海岸线
        
        Args:
            input_tif_path: 输入 TIFF 路径
            year: 年份
            region: 区域名称
            
        Returns:
            处理是否成功
        """
        try:
            start_time = time.time()
            print(f"[INFO]  | 开始处理岛屿: {input_tif_path}")
            
            # 提取 UID
            file_name = os.path.basename(input_tif_path)
            if "UID_" in file_name:
                uid = file_name.split("UID_")[1].split(".")[0]
            else:
                uid = file_name.split(".")[0]
            
            print(f"[INFO]  | 处理岛屿 UID: {uid}")
            
            # 1. 利用插值法降尺度全色波段
            zoom_tif = os.path.join(
                ProjectConfig.INTERPOLATION_PATH, 
                f"UID_{uid}_zoom.tif"
            )
            if not self.band_interpolator.downscale_by_interpolation(
                input_tif_path, zoom_tif, ProcessingConfig.ZOOM_RATIO
            ):
                return False
            
            # 2. 计算 MNDWI 水体指数
            mndwi_tif = os.path.join(
                ProjectConfig.MNDWI_PATH, 
                f"UID_{uid}_ND.tif"
            )
            if not self.index_calculator.calculate_mndwi(
                zoom_tif, mndwi_tif, 
                ProcessingConfig.MNDWI_BAND1, ProcessingConfig.MNDWI_BAND2
            ):
                return False
            
            # 3. 裁剪有效范围
            valid_tif = os.path.join(
                ProjectConfig.EXTRACT_PATH, 
                f"UID_{uid}_extract.tif"
            )
            if not self.coastline_extractor.extract_by_mask(
                mndwi_tif, ProjectConfig.MASK_SHP_PATH, uid, valid_tif
            ):
                return False
            
            # 4. 亚像元边界提取
            subpixel_geojson = os.path.join(
                ProjectConfig.SUBPIXEL_PATH, 
                f"UID_{uid}_subpixel.geojson"
            )
            if not self.subpixel_extractor.subpixel_extraction(
                valid_tif, ProcessingConfig.SUBPIXEL_Z_VALUE, subpixel_geojson
            ):
                return False
            
            # 5. 构建有效面要素并计算几何属性
            output_dir = os.path.join(ProjectConfig.OUTPUT_PATH, f"YY_{year}", region)
            FileOperations.ensure_directory_exists(output_dir)
            
            coast_line_shp = os.path.join(output_dir, f"UID_{uid}_coastline.shp")
            
            if not self.coastline_validator.geojson_to_polygon(
                subpixel_geojson, ProjectConfig.CONTINENT_SHP_PATH, uid,
                ProcessingConfig.SMOOTH_TOLERANCE, coast_line_shp
            ):
                return False
            
            # 6. 计算几何属性
            if not self.spatial_analyzer.process_coastline_features(coast_line_shp, uid):
                return False
            
            elapsed_time = time.strftime(
                "%Hh%Mm%Ss", time.gmtime(time.time() - start_time)
            )
            print(f"[INFO]  | 岛屿 {uid} 处理完成 | 耗时: {elapsed_time}")
            return True
            
        except Exception as e:
            print(f"[ERROR] | 处理岛屿失败 {input_tif_path}: {e}")
            return False
    
    def process_year_data(self, year: int, region: str = "Africa") -> int:
        """
        处理指定年份的所有数据
        
        Args:
            year: 年份
            region: 区域名称
            
        Returns:
            成功处理的岛屿数量
        """
        try:
            print(f"[INFO]  | 开始处理 {year} 年 {region} 区域数据...")
            
            # 构建数据目录路径
            data_dir = os.path.join(
                ProjectConfig.GEE_DATA_PATH, f"c_YY_{year}", region, "temp"
            )
            
            if not os.path.exists(data_dir):
                print(f"[ERROR] | 数据目录不存在: {data_dir}")
                return 0
            
            # 获取所有 TIFF 文件
            tif_files = FileOperations.get_files_with_extension(data_dir, ".tif")
            success_count = 0
            
            for tif_file in tif_files:
                tif_path = os.path.join(data_dir, tif_file)
                
                if self.process_single_island(tif_path, year, region):
                    success_count += 1
            
            print(f"[INFO]  | {year} 年数据处理完成: {success_count}/{len(tif_files)} 个岛屿成功")
            return success_count
            
        except Exception as e:
            print(f"[ERROR] | 处理 {year} 年数据失败: {e}")
            return 0
    
    def run_full_workflow(
        self, 
        years: List[int], 
        countries: List[str], 
        regions: List[str] = None
    ) -> Dict[str, Any]:
        """
        运行完整工作流
        
        Args:
            years: 年份列表
            countries: 国家代码列表
            regions: 区域列表
            
        Returns:
            处理结果统计
        """
        if regions is None:
            regions = ["Africa"]  # 默认区域
        
        start_time = time.time()
        print("[INFO]  | 开始完整海岸线分析工作流")
        print(f"[INFO]  | 年份: {years}")
        print(f"[INFO]  | 国家: {countries}")
        print(f"[INFO]  | 区域: {regions}")
        
        results = {
            "total_processed": 0,
            "successful_years": {},
            "failed_years": {},
            "start_time": datetime.now().isoformat(),
            "end_time": None
        }
        
        for year in years:
            if year not in SUPPORTED_YEARS:
                print(f"[WARN]  | 不支持的年份: {year}，跳过")
                continue
            
            year_success_count = 0
            for region in regions:
                count = self.process_year_data(year, region)
                year_success_count += count
            
            if year_success_count > 0:
                results["successful_years"][year] = year_success_count
                results["total_processed"] += year_success_count
            else:
                results["failed_years"][year] = "处理失败"
        
        results["end_time"] = datetime.now().isoformat()
        
        elapsed_time = time.strftime(
            "%Hh%Mm%Ss", time.gmtime(time.time() - start_time)
        )
        
        print(f"[INFO]  | 完整工作流完成 | 总耗时: {elapsed_time}")
        print(f"[INFO]  | 处理统计: {results['total_processed']} 个岛屿成功")
        
        return results
    
    def run_specific_year(self, year: int) -> bool:
        """
        运行特定年份的分析
        
        Args:
            year: 年份
            
        Returns:
            运行是否成功
        """
        if year not in SUPPORTED_YEARS:
            print(f"[ERROR] | 不支持的年份: {year}")
            return False
        
        results = self.run_full_workflow([year], SIDS_COUNTRIES)
        return results["total_processed"] > 0
    
    def run_specific_country(self, country_code: str) -> bool:
        """
        运行特定国家的分析
        
        Args:
            country_code: 国家代码
            
        Returns:
            运行是否成功
        """
        if country_code not in SIDS_COUNTRIES:
            print(f"[ERROR] | 不支持的国家代码: {country_code}")
            return False
        
        results = self.run_full_workflow(SUPPORTED_YEARS, [country_code])
        return results["total_processed"] > 0


def parse_arguments() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="海岸线变化分析系统")
    
    parser.add_argument(
        "--workflow", 
        action="store_true",
        help="运行完整工作流"
    )
    
    parser.add_argument(
        "--years", 
        type=str,
        help="处理的年份，用逗号分隔（例如：2015,2020）"
    )
    
    parser.add_argument(
        "--countries", 
        type=str,
        help="处理的国家代码，用逗号分隔（例如：ATG,BHS,BLZ）"
    )
    
    parser.add_argument(
        "--year", 
        type=int,
        help="处理特定年份"
    )
    
    parser.add_argument(
        "--country", 
        type=str,
        help="处理特定国家"
    )
    
    return parser.parse_args()


def main() -> None:
    """主函数"""
    try:
        args = parse_arguments()
        workflow = CoastlineAnalysisWorkflow()
        
        if args.workflow:
            # 解析年份和国家参数
            years = []
            if args.years:
                years = [int(y.strip()) for y in args.years.split(",")]
            else:
                years = SUPPORTED_YEARS
            
            countries = []
            if args.countries:
                countries = [c.strip() for c in args.countries.split(",")]
            else:
                countries = SIDS_COUNTRIES
            
            results = workflow.run_full_workflow(years, countries)
            print(f"[INFO]  | 工作流执行结果: {results}")
            
        elif args.year:
            success = workflow.run_specific_year(args.year)
            print(f"[INFO]  | 特定年份处理: {'成功' if success else '失败'}")
            
        elif args.country:
            success = workflow.run_specific_country(args.country)
            print(f"[INFO]  | 特定国家处理: {'成功' if success else '失败'}")
            
        else:
            print("[INFO]  | 使用 --help 查看可用选项")
            
    except Exception as e:
        print(f"[ERROR] | 主程序执行失败: {e}")
        raise


if __name__ == "__main__":
    main()