#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海岸线变化分析项目 - 配置模块

作用：定义项目路径、国家列表、处理参数等全局配置
主要类：ProjectConfig, PathConfig
使用示例：from config import PROJECT_CONFIG, SIDS_LIST
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass(frozen=True)
class PathConfig:
    """项目路径配置"""
    
    # 基础路径
    PROJECT_ROOT: str = r"E:\_OrderingProject\F_IslandsBoundaryChange"
    ARC_DATA: str = os.path.join(PROJECT_ROOT, "b_ArcData")
    GEE_DATA: str = os.path.join(PROJECT_ROOT, "c_GeeData")
    
    # 工作目录
    TEMP_DIR: str = os.path.join(ARC_DATA, "temp")
    DRAFT_DIR: str = os.path.join(TEMP_DIR, "_draft")
    
    # 数据目录
    SIDS_BOUNDARY: str = os.path.join(ARC_DATA, "j_SIDS_Polygon")
    ACCURACY_EVALUATION: str = os.path.join(ARC_DATA, "_AccuracyEvaluation")
    THIRD_PARTY_DATA: str = os.path.join(ARC_DATA, "_ThirdProductEvaluation")


@dataclass(frozen=True)
class ProcessingConfig:
    """处理参数配置"""
    
    # 年份配置
    YEARS: List[str] = ("2010", "2015", "2020")
    
    # 提取阈值配置
    EXTRACT_THRESHOLDS: Dict[str, float] = {
        "2010": 1.0,
        "2015": 5.0, 
        "2020": 9.0
    }
    
    # 滤波参数
    LOCAL_MAX_WINDOW_SIZE: int = 31
    LOCAL_MAX_THRESHOLD: float = 30.0
    MIN_CLUSTER_SIZE: int = 4
    MEDIAN_FILTER_THRESHOLD: float = 10.0
    
    # 矢量处理参数
    HOLE_FILL_VALUE: float = 20.0
    MAX_HOLE_SIZE: int = 500
    SMOOTH_TOLERANCE: str = "90 Meters"
    
    # 精度评估参数
    DISTANCE_THRESHOLDS: List[int] = (30, 60, 90, 120, 150)


class ProjectConfig:
    """项目总配置"""
    
    paths = PathConfig()
    processing = ProcessingConfig()
    
    # SIDS 国家列表
    SIDS_LIST: List[str] = [
        "ATG", "BHS", "BLZ", "BRB", "COM", "CPV", "CUB", "DMA", "DOM", "FJI",
        "FSM", "GNB", "GRD", "GUY", "HTI", "JAM", "KIR", "KNA", "LCA", "MDV",
        "MHL", "MUS", "NRU", "PLW", "PNG", "SGP", "SLB", "STP", "SUR", "SYC",
        "TLS", "TON", "TTO", "TUV", "VCT", "VUT", "WSM"
    ]


# 全局配置实例
PROJECT_CONFIG = ProjectConfig()