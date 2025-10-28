#!/usr/bin/env python3
"""
海岸线变化分析系统 - 配置文件
定义项目常量、路径配置和通用设置
"""

import os
from typing import List, Dict, Any

# ====== 项目配置 ======
class ProjectConfig:
    """项目全局配置"""
    
    # 基础路径
    BASE_PATH = r"E:\_OrderingProject\F_IslandsBoundaryChange"
    ARC_DATA_PATH = os.path.join(BASE_PATH, "b_ArcData")
    GEE_DATA_PATH = os.path.join(BASE_PATH, "c_GeeData")
    QGIS_PATH = os.path.join(BASE_PATH, "g_QGIS")
    
    # 小岛屿发展中国家列表
    SIDS_COUNTRIES: List[str] = [
        "ATG", "BHS", "BLZ", "BRB", "COM", "CPV", "CUB", "DMA", "DOM", 
        "FJI", "FSM", "GNB", "GRD", "GUY", "HTI", "JAM", "KIR", "KNA", 
        "LCA", "MDV", "MHL", "MUS", "NRU", "PLW", "PNG", "SGP", "SLB", 
        "STP", "SUR", "SYC", "TLS", "TON", "TTO", "TUV", "VCT", "VUT", "WSM"
    ]
    
    # 处理年份
    PROCESS_YEARS: List[int] = [2000, 2010, 2015, 2020]
    
    # 文件后缀
    FILE_EXTENSIONS: Dict[str, str] = {
        "shapefile": ".shp",
        "geojson": ".geojson", 
        "tiff": ".tif",
        "dbf": ".dbf"
    }


class PathConfig:
    """路径配置类"""
    
    def __init__(self, base_path: str = ProjectConfig.BASE_PATH):
        self.base_path = base_path
        self.arc_data = os.path.join(base_path, "b_ArcData")
        self.gee_data = os.path.join(base_path, "c_GeeData")
        self.qgis = os.path.join(base_path, "g_QGIS")
    
    def get_country_year_path(self, data_type: str, country_code: str, year: int) -> str:
        """
        获取国家年份特定路径
        
        Args:
            data_type: 数据类型 ('tif', 'geojson', 'shp_line', 'shp_polygon', 'smooth')
            country_code: 国家代码
            year: 年份
            
        Returns:
            完整路径字符串
        """
        year_suffix = str(year)[-2:]
        
        path_map = {
            "tif": os.path.join(self.arc_data, "h_SIDS_Tif", country_code, f"{country_code}_{year_suffix}.tif"),
            "geojson": os.path.join(self.arc_data, "GEE_Geojson", country_code, f"{country_code}_{year_suffix}.geojson"),
            "shp_line": os.path.join(self.arc_data, "i_SIDS_Line", country_code, f"{country_code}_{year_suffix}.shp"),
            "shp_polygon": os.path.join(self.arc_data, "j_SIDS_Polygon", country_code, f"{country_code}_{year_suffix}.shp"),
            "smooth": os.path.join(self.arc_data, "k_SIDS_Smooth", country_code, f"{country_code}_{year_suffix}.shp")
        }
        
        return path_map.get(data_type, "")
    
    def create_directory(self, directory_path: str) -> None:
        """创建目录如果不存在"""
        os.makedirs(directory_path, exist_ok=True)


# ====== 处理参数 ======
class ProcessingParameters:
    """处理参数配置"""
    
    # 子像素提取参数
    SUBPIXEL_Z_VALUES: int = 0
    SUBPIXEL_BUFFER_SIZE: int = 1
    
    # 平滑参数
    SMOOTH_ALGORITHM: str = "PAEK"
    SMOOTH_TOLERANCE: str = "90 Meters"
    SMOOTH_ENDPOINT_OPTION: str = "FIXED_ENDPOINT"
    
    # 栅格化参数
    RASTERIZE_VALUE: int = 10
    PIXEL_THRESHOLD: int = 5
    
    # 精度评估参数
    NEAR_SEARCH_RADIUS: str = "500 Meters"
    ACCURACY_THRESHOLDS: List[int] = [30, 60, 90]


if __name__ == "__main__":
    # 配置测试
    config = ProjectConfig()
    print(f"[INFO] | 项目基础路径: {config.BASE_PATH}")
    print(f"[INFO] | 处理国家数量: {len(config.SIDS_COUNTRIES)}")
    print(f"[INFO] | 处理年份: {config.PROCESS_YEARS}")