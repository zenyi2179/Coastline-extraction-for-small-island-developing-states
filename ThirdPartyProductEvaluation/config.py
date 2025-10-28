#!/usr/bin/env python3
"""
海岸线变化分析系统 - 配置文件
定义项目路径、国家列表、处理参数等全局配置
"""

import os
from typing import List, Dict, Any

# 项目根路径配置
PROJECT_ROOT = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData"

# 小岛屿发展中国家列表
SIDS_COUNTRIES: List[str] = [
    "ATG", "BHS", "BLZ", "BRB", "COM", "CPV", "CUB", "DMA", "DOM", "FJI",
    "FSM", "GNB", "GRD", "GUY", "HTI", "JAM", "KIR", "KNA", "LCA", "MDV",
    "MHL", "MUS", "NRU", "PLW", "PNG", "SGP", "SLB", "STP", "SUR", "SYC",
    "TLS", "TON", "TTO", "TUV", "VCT", "VUT", "WSM"
]

# 处理年份配置
PROCESSING_YEARS: List[int] = [2000, 2010, 2015, 2020]

# 数据源配置
DATA_SOURCES: Dict[str, str] = {
    "sids_boundary": os.path.join(PROJECT_ROOT, r"_ThirdProductEvaluation\boundary\SIDS_boun.shp"),
    "admin_division": os.path.join(PROJECT_ROOT, r"d_SIDS_Boundary\SIDS\AdminDivision"),
    "boundary_mask": os.path.join(PROJECT_ROOT, r"_ThirdProductEvaluation\boundary\boun_mask"),
    "sids_optimize": os.path.join(PROJECT_ROOT, r"f_SIDS_Optimize"),
}

# 输出目录配置
OUTPUT_PATHS: Dict[str, str] = {
    "gcl_fcs30": os.path.join(PROJECT_ROOT, r"_ThirdProductEvaluation\GCL_FCS30_{}"),
    "gmssd_2015": os.path.join(PROJECT_ROOT, r"_ThirdProductEvaluation\GMSSD_2015"),
    "gsv": os.path.join(PROJECT_ROOT, r"_ThirdProductEvaluation\GSV"),
    "osm": os.path.join(PROJECT_ROOT, r"_ThirdProductEvaluation\OSM"),
    "sids_cl": os.path.join(PROJECT_ROOT, r"_ThirdProductEvaluation\SIDS_CL_{}"),
}

# 处理参数配置
PROCESSING_PARAMS: Dict[str, Any] = {
    "search_distance": "2 Kilometers",  # 空间搜索距离
    "clip_distance": "200 Meters",      # 裁剪搜索距离
    "empty_file_threshold": 100,        # 空文件大小阈值（字节）
    "geometry_length_unit": "KILOMETERS",  # 几何长度单位
    "geometry_area_unit": "SQUARE_KILOMETERS",  # 几何面积单位
}

# 大陆列表
CONTINENTS: List[str] = [
    "Africa", "Antarctica", "Asia", "Europe", 
    "North_America", "Oceania", "South_America"
]

class ProjectConfig:
    """项目配置类"""
    
    def __init__(self) -> None:
        self.project_root = PROJECT_ROOT
        self.sids_countries = SIDS_COUNTRIES
        self.processing_years = PROCESSING_YEARS
        self.data_sources = DATA_SOURCES
        self.output_paths = OUTPUT_PATHS
        self.processing_params = PROCESSING_PARAMS
        self.continents = CONTINENTS
    
    def get_output_path(self, data_type: str, year: int = None) -> str:
        """获取输出路径"""
        path_template = self.output_paths.get(data_type, "")
        if year and "{}" in path_template:
            return path_template.format(str(year)[-2:])
        return path_template
    
    def get_admin_boundary_path(self, country: str) -> str:
        """获取国家行政边界路径"""
        return os.path.join(self.data_sources["admin_division"], f"{country}.shp")
    
    def get_mask_boundary_path(self, country: str, version: str = "v3") -> str:
        """获取掩膜边界路径"""
        return os.path.join(self.data_sources["boundary_mask"], f"{country}_{version}.shp")


if __name__ == "__main__":
    # 配置验证
    config = ProjectConfig()
    print("[INFO]  | 配置加载完成")
    print(f"[INFO]  | 项目根路径: {config.project_root}")
    print(f"[INFO]  | 处理国家数量: {len(config.sids_countries)}")
    print(f"[INFO]  | 处理年份: {config.processing_years}")