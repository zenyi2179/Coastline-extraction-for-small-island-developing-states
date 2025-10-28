#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海岸线变化分析项目 - 精度评估模块

作用：精度统计、误差计算、样本点生成、第三方数据评估
主要类：AccuracyEvaluator, SamplePointGenerator
使用示例：from accuracy_evaluation import AccuracyEvaluator
"""

import os
from typing import List, Optional, Dict, Any
import arcpy
import geopandas as gpd
from osgeo import ogr

from config import PROJECT_CONFIG
from utils import TimeTracker, FileUtils, calculate_statistics_from_dbf


class SamplePointGenerator:
    """样本点生成器"""
    
    @staticmethod
    def create_sample_points(standard_points_path: str, 
                           sample_lines_path: str, 
                           output_points_path: str) -> None:
        """
        创建样本点
        
        Args:
            standard_points_path: 标准点路径
            sample_lines_path: 样本线路径
            output_points_path: 输出点路径
        """
        try:
            arcpy.env.overwriteOutput = True
            FileUtils.ensure_directory_exists(output_points_path)
            
            # 复制要素
            points_copy = r"in_memory\StP_Copy"
            arcpy.management.CopyFeatures(
                in_features=standard_points_path, 
                out_feature_class=points_copy
            )
            
            # 邻近分析
            points_near = arcpy.analysis.Near(
                in_features=points_copy, 
                near_features=[sample_lines_path],
                location="LOCATION", 
                method="GEODESIC", 
                search_radius="50000 Meters",
                field_names=[
                    ["NEAR_FID", "NEAR_FID"], 
                    ["NEAR_DIST", "NEAR_DIST"],
                    ["NEAR_X", "NEAR_X"], 
                    ["NEAR_Y", "NEAR_Y"]
                ]
            )[0]
            
            # XY 表转点
            arcpy.management.XYTableToPoint(
                in_table=points_near, 
                out_feature_class=output_points_path,
                x_field="NEAR_X", 
                y_field="NEAR_Y"
            )
            print(f"[INFO]  | 样本点生成完成: {output_points_path}")
            
        except Exception as e:
            print(f"[ERROR] | 样本点生成失败: {e}")
            raise
    
    @staticmethod
    def filter_sample_points_by_distance(input_points_path: str, 
                                       max_distance: float = 120.0) -> None:
        """
        按距离过滤样本点
        
        Args:
            input_points_path: 输入点要素路径
            max_distance: 最大距离阈值
        """
        try:
            arcpy.env.overwriteOutput = True
            
            layer_selected = arcpy.management.SelectLayerByAttribute(
                in_layer_or_view=input_points_path, 
                selection_type="NEW_SELECTION",
                where_clause=f"NEAR_DIST > {max_distance} Or NEAR_DIST = -1", 
                invert_where_clause=""
            )
            arcpy.management.DeleteRows(layer_selected)
            arcpy.management.SelectLayerByAttribute(layer_selected, "CLEAR_SELECTION")
            print(f"[INFO]  | 样本点过滤完成: {input_points_path}")
            
        except Exception as e:
            print(f"[ERROR] | 样本点过滤失败: {e}")
            raise
    
    @staticmethod
    def convert_kml_to_shapefile(kml_file_path: str, shp_file_path: str) -> None:
        """
        将 KML 文件转换为 Shapefile
        
        Args:
            kml_file_path: 输入 KML 文件路径
            shp_file_path: 输出 Shapefile 文件路径
        """
        try:
            import warnings
            warnings.filterwarnings("ignore", category=UserWarning)
            warnings.filterwarnings("ignore", category=RuntimeWarning)
            
            gdf = gpd.read_file(kml_file_path, driver='KML')
            gdf.columns = [col[:10] for col in gdf.columns]  # 确保列名不超过10字符
            gdf.to_file(shp_file_path, driver='ESRI Shapefile')
            print(f"[INFO]  | KML 转换完成: {shp_file_path}")
            
        except Exception as e:
            print(f"[ERROR] | KML 转换失败: {e}")
            raise
    
    @staticmethod
    def export_selected_points_to_kml(input_points_path: str, 
                                    reference_points_path: str, 
                                    output_kml_path: str) -> None:
        """
        导出选择的点到 KML 文件
        
        Args:
            input_points_path: 输入点要素路径
            reference_points_path: 参考点要素路径
            output_kml_path: 输出 KML 文件路径
        """
        try:
            FileUtils.ensure_directory_exists(output_kml_path)
            
            # 按位置选择
            layer_selected = arcpy.management.SelectLayerByLocation(
                in_layer=[input_points_path], 
                overlap_type="INTERSECT",
                select_features=reference_points_path, 
                search_distance="100 Meters",
                selection_type="NEW_SELECTION"
            )
            
            # 导出到临时 Shapefile
            temp_shp_path = output_kml_path.replace(".kml", ".shp")
            arcpy.conversion.ExportFeatures(
                in_features=layer_selected,
                out_features=temp_shp_path
            )
            arcpy.management.SelectLayerByAttribute(layer_selected, "CLEAR_SELECTION")
            
            # 转换为 KML
            input_datasource = ogr.Open(temp_shp_path, 0)
            if input_datasource is None:
                raise IOError("无法打开临时 Shapefile")
                
            input_layer = input_datasource.GetLayer()
            driver = ogr.GetDriverByName('KML')
            output_datasource = driver.CreateDataSource(output_kml_path)
            
            if output_datasource is None:
                raise IOError("无法创建 KML 文件")
                
            output_layer = output_datasource.CopyLayer(input_layer, input_layer.GetName())
            
            input_datasource.Destroy()
            output_datasource.Destroy()
            
            # 清理临时文件
            if os.path.exists(temp_shp_path):
                os.remove(temp_shp_path)
                for ext in ['.dbf', '.shx', '.prj']:
                    sidecar_file = temp_shp_path.replace('.shp', ext)
                    if os.path.exists(sidecar_file):
                        os.remove(sidecar_file)
            
            print(f"[INFO]  | KML 导出完成: {output_kml_path}")
            
        except Exception as e:
            print(f"[ERROR] | KML 导出失败: {e}")
            raise


class AccuracyEvaluator:
    """精度评估器"""
    
    def __init__(self):
        self.config = PROJECT_CONFIG.processing
    
    def evaluate_accuracy_for_country(self, 
                                    country: str, 
                                    year: str, 
                                    data_source: str = "SIDS") -> Optional[Dict[str, float]]:
        """
        评估单个国家的精度
        
        Args:
            country: 国家代码
            year: 年份
            data_source: 数据源类型
            
        Returns:
            精度统计字典
        """
        dbf_file_path = self._get_dbf_file_path(country, year, data_source)
        if not os.path.exists(dbf_file_path):
            print(f"[WARN]  | DBF 文件不存在: {dbf_file_path}")
            return None
            
        return calculate_statistics_from_dbf(dbf_file_path)
    
    def batch_evaluate_accuracy(self, 
                              years: Optional[List[str]] = None,
                              countries: Optional[List[str]] = None,
                              data_sources: Optional[List[str]] = None) -> None:
        """
        批量评估精度
        
        Args:
            years: 年份列表
            countries: 国家列表
            data_sources: 数据源列表
        """
        if years is None:
            years = self.config.YEARS
        if countries is None:
            countries = PROJECT_CONFIG.SIDS_LIST
        if data_sources is None:
            data_sources = ["SIDS", "OSM", "GCL", "GSV", "GMSSD"]
            
        with TimeTracker("批量精度评估"):
            print("year country mean_value std_dev rmse percent_30 percent_60 percent_90 count_30 count_60 count_90 count_all")
            
            for year in years:
                for country in countries:
                    for data_source in data_sources:
                        statistics = self.evaluate_accuracy_for_country(country, year, data_source)
                        if statistics:
                            self._print_statistics_row(year, country, statistics)
                        else:
                            print(f"{year} {country}")
    
    def _get_dbf_file_path(self, country: str, year: str, data_source: str) -> str:
        """获取 DBF 文件路径"""
        year_suffix = year[-2:]
        
        if data_source == "SIDS":
            return os.path.join(
                PROJECT_CONFIG.paths.ACCURACY_EVALUATION,
                country, year, f'SP_{country}_{year_suffix}.dbf'
            )
        else:
            data_source_map = {
                "OSM": "OSM",
                "GCL": "GCL_FCS30",
                "GSV": "GSV", 
                "GMSSD": "GMSSD"
            }
            source_name = data_source_map.get(data_source, data_source)
            return os.path.join(
                PROJECT_CONFIG.paths.ACCURACY_EVALUATION,
                country, year, "ThirdPartyDataSource", 
                f'{source_name}_SP_{country}_{year_suffix}.dbf'
            )
    
    def _print_statistics_row(self, year: str, country: str, statistics: Dict[str, float]) -> None:
        """打印统计行"""
        print(
            f"{year} {country} "
            f"{statistics['mean_value']} "
            f"{statistics['std_dev']} "
            f"{statistics['rmse']} "
            f"{statistics['percent_30']} "
            f"{statistics['percent_60']} "
            f"{statistics['percent_90']} "
            f"{statistics['count_30']} "
            f"{statistics['count_60']} "
            f"{statistics['count_90']} "
            f"{statistics['count_all']}"
        )


def merge_third_party_datasets() -> None:
    """合并第三方数据集"""
    from file_operations import BatchProcessor
    
    processor = BatchProcessor()
    third_party_datasets = [
        'GSV', 'GMSSD_2015', 'OSM',
        'GCL_FCS30_10', 'GCL_FCS30_15', 'GCL_FCS30_20',
    ]
    
    for dataset in third_party_datasets:
        print(f"[INFO]  | 处理第三方数据集: {dataset}")
        # 这里可以调用具体的合并逻辑