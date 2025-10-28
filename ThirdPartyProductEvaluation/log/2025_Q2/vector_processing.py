#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海岸线变化分析项目 - 矢量处理模块

作用：矢量数据转换、修复、合并、平滑等操作
主要类：VectorConverter, GeometryFixer
使用示例：from vector_processing import VectorConverter, fix_holes_in_shapefile
"""

import os
from typing import List, Optional
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.features import shapes, rasterize
from scipy.ndimage import label
from shapely.geometry import shape, mapping, Polygon, MultiPolygon, LineString, MultiLineString
from shapely.ops import unary_union, polygonize
import arcpy

from config import PROJECT_CONFIG
from utils import TimeTracker, FileUtils


class VectorConverter:
    """矢量数据转换器"""
    
    @staticmethod
    def raster_to_vector_polygons(input_tif_path: str, 
                                output_shp_path: str, 
                                threshold: float = 0.0) -> None:
        """
        将栅格数据转换为矢量面
        
        Args:
            input_tif_path: 输入 TIF 文件路径
            output_shp_path: 输出 SHP 文件路径
            threshold: 像元阈值
        """
        with TimeTracker("栅格转矢量"):
            FileUtils.ensure_directory_exists(output_shp_path)
            
            with rasterio.open(input_tif_path) as src:
                data = src.read(1)
                transform = src.transform
                crs = src.crs
                
                binary_mask = (data > threshold).astype(np.uint8)
                labeled_array, num_features = label(binary_mask)
                
                if num_features == 0:
                    print(f"[WARN]  | 无连通区域: {input_tif_path}")
                    return
                    
                shapes_generator = shapes(labeled_array, mask=binary_mask, transform=transform)
                geometries = [
                    {"geometry": shape(geom), "properties": {"id": int(value)}}
                    for geom, value in shapes_generator if value != 0
                ]
                
                gdf = gpd.GeoDataFrame.from_features(geometries, crs=crs)
                gdf.to_file(output_shp_path, driver='ESRI Shapefile')
                print(f"[INFO]  | 矢量输出完成: {output_shp_path}")
    
    @staticmethod
    def vector_to_raster(vector_path: str, 
                       raster_path: str, 
                       reference_raster: str, 
                       value: int = 30) -> None:
        """
        将矢量文件转换为栅格
        
        Args:
            vector_path: 输入矢量文件路径
            raster_path: 输出栅格文件路径
            reference_raster: 参考栅格文件路径
            value: 转换后的栅格像元值
        """
        with TimeTracker("矢量转栅格"):
            FileUtils.ensure_directory_exists(raster_path)
            
            vector_data = gpd.read_file(vector_path)
            
            with rasterio.open(reference_raster) as ref:
                pixel_size = ref.res[0]
                
            bounds = vector_data.total_bounds
            width = int((bounds[2] - bounds[0]) / pixel_size)
            height = int((bounds[3] - bounds[1]) / pixel_size)
            transform = rasterio.Affine(pixel_size, 0, bounds[0], 0, -pixel_size, bounds[3])
            
            rasterized_data = rasterize(
                [(mapping(geom), value) for geom in vector_data.geometry],
                out_shape=(height, width),
                transform=transform,
                fill=0,
                dtype='uint8'
            )
            
            with rasterio.open(raster_path, 'w', 
                             driver='GTiff', 
                             height=height, 
                             width=width,
                             count=1, 
                             dtype='uint8', 
                             crs=vector_data.crs,
                             transform=transform, 
                             nodata=0) as dst:
                dst.write(rasterized_data, 1)
                
            print(f"[INFO]  | 栅格保存完成: {raster_path}")
    
    @staticmethod
    def geojson_to_shapefile(input_geojson: str, output_shp: str) -> None:
        """
        将 GeoJSON 文件转换为 Shapefile
        
        Args:
            input_geojson: 输入 GeoJSON 文件路径
            output_shp: 输出 Shapefile 文件路径
        """
        try:
            temp_line = r"in_memory\geojson_to_shp"
            arcpy.conversion.JSONToFeatures(
                in_json_file=input_geojson, 
                out_features=temp_line, 
                geometry_type='POLYLINE'
            )
            arcpy.management.FeatureToLine(
                in_features=temp_line, 
                out_feature_class=output_shp
            )
            print(f"[INFO]  | GeoJSON 转换完成: {output_shp}")
        except Exception as e:
            print(f"[ERROR] | GeoJSON 转换失败: {e}")
            raise
    
    @staticmethod
    def line_to_polygon(input_shp: str, output_shp: str) -> None:
        """
        将线要素转换为面要素
        
        Args:
            input_shp: 输入线要素 Shapefile
            output_shp: 输出面要素 Shapefile
        """
        try:
            temp_shp = "in_memory/temp_line"
            arcpy.env.overwriteOutput = True
            FileUtils.ensure_directory_exists(output_shp)
            
            arcpy.management.FeatureToPolygon([input_shp], temp_shp)
            arcpy.management.Dissolve(
                in_features=temp_shp,
                out_feature_class=output_shp,
                dissolve_field=[],
                multi_part="SINGLE_PART",
                unsplit_lines="DISSOLVE_LINES"
            )
            print(f"[INFO]  | 线转面完成: {output_shp}")
        except Exception as e:
            print(f"[ERROR] | 线转面失败: {e}")
            raise


class GeometryFixer:
    """几何修复器"""
    
    @staticmethod
    def fix_holes_in_shapefile(input_shp: str, 
                             output_shp: str, 
                             min_area: float = 0.0) -> None:
        """
        修复面要素中的空洞
        
        Args:
            input_shp: 输入 Shapefile 路径
            output_shp: 输出 Shapefile 路径
            min_area: 保留的最小空洞面积
        """
        with TimeTracker("修复面要素空洞"):
            FileUtils.ensure_directory_exists(output_shp)
            
            gdf = gpd.read_file(input_shp)
            fixed_geometries = []
            
            for geom in gdf.geometry:
                if geom.geom_type == 'Polygon':
                    exterior = geom.exterior
                    interiors = [interior for interior in geom.interiors 
                               if Polygon(interior).area > min_area]
                    fixed_geometries.append(Polygon(exterior, interiors))
                elif geom.geom_type == 'MultiPolygon':
                    fixed_polygons = []
                    for poly in geom.geoms:
                        exterior = poly.exterior
                        interiors = [interior for interior in poly.interiors 
                                   if Polygon(interior).area > min_area]
                        fixed_polygons.append(Polygon(exterior, interiors))
                    fixed_geometries.append(MultiPolygon(fixed_polygons))
                else:
                    fixed_geometries.append(geom)
            
            gdf.geometry = fixed_geometries
            gdf.to_file(output_shp)
            print(f"[INFO]  | 空洞修复完成: {output_shp}")
    
    @staticmethod
    def merge_shapefiles_geopandas(input_folder: str, 
                                 output_shp: str, 
                                 extra_shp: Optional[str] = None) -> None:
        """
        使用 GeoPandas 合并多个 Shapefile
        
        Args:
            input_folder: 输入文件夹路径
            output_shp: 输出 Shapefile 路径
            extra_shp: 额外的 Shapefile 路径
        """
        with TimeTracker("合并Shapefile"):
            FileUtils.ensure_directory_exists(output_shp)
            
            gdfs = []
            for filename in os.listdir(input_folder):
                if filename.endswith('.shp'):
                    gdf = gpd.read_file(os.path.join(input_folder, filename))
                    gdfs.append(gdf)
            
            if extra_shp and os.path.exists(extra_shp):
                gdf_extra = gpd.read_file(extra_shp)
                gdfs.append(gdf_extra)
            
            if not gdfs:
                print(f"[WARN]  | 没有找到要合并的 Shapefile")
                return
                
            merged = gpd.GeoDataFrame(gpd.pd.concat(gdfs, ignore_index=True), crs=gdfs[0].crs)
            dissolved = unary_union(merged.geometry)
            gdf_out = gpd.GeoDataFrame(geometry=[dissolved], crs=merged.crs)
            gdf_out.to_file(output_shp)
            print(f"[INFO]  | Shapefile 合并完成: {output_shp}")
    
    @staticmethod
    def fix_shapefile_geometry(input_shp: str, output_shp: str) -> None:
        """
        修复 Shapefile 几何问题
        
        Args:
            input_shp: 输入 Shapefile 路径
            output_shp: 输出 Shapefile 路径
        """
        try:
            arcpy.env.overwriteOutput = True
            FileUtils.ensure_directory_exists(output_shp)
            
            temp_line = "in_memory/shp_temp_line"
            temp_poly = "in_memory/shp_temp_polygon"
            
            arcpy.management.FeatureToLine([input_shp], temp_line)
            arcpy.management.FeatureToPolygon(temp_line, temp_poly)
            arcpy.analysis.PairwiseDissolve(
                temp_poly, 
                output_shp, 
                multi_part="SINGLE_PART"
            )
            print(f"[INFO]  | 几何修复完成: {output_shp}")
        except Exception as e:
            print(f"[ERROR] | 几何修复失败: {e}")
            raise


def select_polygons_by_location(valid_pixel_shp: str, 
                              country_shp: str, 
                              output_shp: str) -> None:
    """
    按位置选择有效的多边形
    
    Args:
        valid_pixel_shp: 有效像素矢量文件
        country_shp: 国家边界矢量文件
        output_shp: 输出矢量文件
    """
    try:
        arcpy.env.overwriteOutput = True
        FileUtils.ensure_directory_exists(output_shp)
        
        selected = arcpy.management.SelectLayerByLocation(
            in_layer=[valid_pixel_shp],
            overlap_type="INTERSECT",
            select_features=country_shp,
            search_distance="300 Meters",
            selection_type="NEW_SELECTION"
        )
        arcpy.conversion.ExportFeatures(
            in_features=selected, 
            out_features=output_shp
        )
        arcpy.management.SelectLayerByAttribute(selected, "CLEAR_SELECTION")
        print(f"[INFO]  | 有效矢量选择完成: {output_shp}")
    except Exception as e:
        print(f"[ERROR] | 选择有效多边形失败: {e}")
        raise