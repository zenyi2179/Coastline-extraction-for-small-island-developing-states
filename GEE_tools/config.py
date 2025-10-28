# config.py
#!/usr/bin/env python3
"""
海岸线变化分析系统 - 配置模块
定义项目路径、处理参数、常量等全局配置
"""

import os
from typing import Dict, List, Any

# 项目基础路径配置
class ProjectConfig:
    """项目基础路径配置"""
    
    # 基础路径
    BASE_PROJECT_PATH = r"E:\_OrderingProject\F_IslandsBoundaryChange"
    ARC_DATA_PATH = os.path.join(BASE_PROJECT_PATH, "b_ArcData")
    GEE_DATA_PATH = os.path.join(BASE_PROJECT_PATH, "c_GeeData")
    
    # 临时文件路径
    TEMP_PATH = os.path.join(ARC_DATA_PATH, "temp")
    INTERPOLATION_PATH = os.path.join(TEMP_PATH, "h_bandInterpolation")
    MNDWI_PATH = os.path.join(TEMP_PATH, "i_cadulateMNDWI")
    EXTRACT_PATH = os.path.join(TEMP_PATH, "j_distinguishRange")
    SUBPIXEL_PATH = os.path.join(TEMP_PATH, "k_subPixelWaterlineExtraction")
    SHAPE_FEATURE_PATH = os.path.join(TEMP_PATH, "l_buildShapeFeature")
    
    # 输出路径
    OUTPUT_PATH = os.path.join(ARC_DATA_PATH, "GEE_Landsat_output")
    
    # 数据源路径
    MASK_SHP_PATH = os.path.join(ARC_DATA_PATH, "SmallIslands_con_buffer.gdb", "Africa_buffer")
    CONTINENT_SHP_PATH = os.path.join(ARC_DATA_PATH, "SmallIslands_continent.gdb", "Africa")


class ProcessingConfig:
    """处理参数配置"""
    
    # 插值参数
    ZOOM_RATIO = 3
    
    # MNDWI 计算参数
    MNDWI_BAND1 = 2  # 绿色波段
    MNDWI_BAND2 = 4  # 短波红外波段
    
    # 亚像元提取参数
    SUBPIXEL_Z_VALUE = 10.5
    
    # 平滑参数
    SMOOTH_TOLERANCE = 60  # 米
    
    # 缓冲区参数
    BUFFER_DISTANCE = 50  # 米


class GEEConfig:
    """Google Earth Engine 配置"""
    
    # GEE 项目配置
    PROJECT_NAME = "ee-nicexian0011"
    
    # 代理配置
    HTTP_PROXY = "http://127.0.0.1:4780"
    HTTPS_PROXY = "http://127.0.0.1:4780"
    
    # 资产路径
    ASSET_BASE_PATH = "users/nicexian0011"
    ISLANDS_ASSET_PATH = f"{ASSET_BASE_PATH}/islands"
    AFRICA_BUFFER_ASSET_PATH = f"{ASSET_BASE_PATH}/Africa_si_buffer"
    
    # 图像集合配置
    LANDSAT_COLLECTION = "LANDSAT/LC08/C02/T1_L2"
    SENTINEL_COLLECTION = "COPERNICUS/S2_HARMONIZED"
    
    # 过滤参数
    MAX_CLOUD_COVER = 20
    MAX_CLOUDY_PIXEL_PERCENTAGE = 20


# 支持的年份列表
SUPPORTED_YEARS = [2000, 2010, 2015, 2020]

# 小岛屿发展中国家代码列表
SIDS_COUNTRIES = [
    "ATG", "BHS", "BLZ", "BRB", "CPV", "COM", "CUB", "DMA", "DOM", "FJI",
    "GRD", "GNB", "GUY", "HTI", "JAM", "KIR", "MDV", "MHL", "FSM", "MUS",
    "NRU", "PLW", "PNG", "KNA", "LCA", "VCT", "WSM", "STP", "SYC", "SLB",
    "SUR", "TLS", "TON", "TUV", "VUT"
]


def get_year_folder(year: int) -> str:
    """根据年份获取对应的文件夹名称"""
    return f"YY_{year}"


def get_output_folder(year: int, region: str = "Africa") -> str:
    """获取输出文件夹路径"""
    return os.path.join(ProjectConfig.OUTPUT_PATH, get_year_folder(year), region)