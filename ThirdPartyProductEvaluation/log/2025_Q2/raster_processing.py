#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海岸线变化分析项目 - 栅格处理模块

作用：栅格数据预处理、滤波、空洞填充、团块过滤等操作
主要类：RasterPreprocessor, RasterFilter
使用示例：from raster_processing import RasterPreprocessor
"""

import numpy as np
import rasterio
from rasterio.profiles import Profile
from scipy.ndimage import maximum_filter, label, binary_fill_holes
from typing import Optional, Tuple

from config import PROJECT_CONFIG
from utils import TimeTracker, FileUtils


class RasterFilter:
    """栅格滤波器"""
    
    @staticmethod
    def extract_pixels_above_threshold(data: np.ndarray, 
                                     threshold: float = 5.0, 
                                     nodata_value: float = 0.0) -> np.ndarray:
        """
        提取像元值大于阈值的区域
        
        Args:
            data: 输入栅格数据
            threshold: 像元阈值
            nodata_value: 不满足条件的像元填充值
            
        Returns:
            过滤后的栅格数据
        """
        return np.where(data > threshold, data, nodata_value)
    
    @staticmethod
    def filter_by_local_maximum(data: np.ndarray, 
                              window_size: int = 31, 
                              max_threshold: float = 10.0, 
                              nodata_value: float = 0.0) -> np.ndarray:
        """
        使用局部最大值滤波过滤背景噪点
        
        Args:
            data: 输入栅格数据
            window_size: 滤波窗口大小（必须为奇数）
            max_threshold: 最大值阈值
            nodata_value: 滤除后的像元值
            
        Returns:
            滤波后的栅格数据
        """
        if window_size % 2 == 0:
            raise ValueError("window_size 必须为奇数")
            
        local_max = maximum_filter(data, size=window_size, mode='nearest')
        return np.where(local_max < max_threshold, nodata_value, data)
    
    @staticmethod
    def remove_small_clusters(data: np.ndarray, 
                            min_cluster_size: int = 4, 
                            nodata_value: float = 0.0) -> np.ndarray:
        """
        移除小于指定大小的连通区域
        
        Args:
            data: 输入栅格数据
            min_cluster_size: 最小保留的连通区域大小
            nodata_value: 被移除区域赋值
            
        Returns:
            过滤后的栅格数据
        """
        mask = data != 0
        structure = np.array([[0, 1, 0], 
                             [1, 1, 1], 
                             [0, 1, 0]])
        labeled_array, _ = label(mask, structure=structure)
        counts = np.bincount(labeled_array.ravel())
        keep_mask = np.isin(labeled_array, np.where(counts >= min_cluster_size)[0])
        return np.where(keep_mask, data, nodata_value)
    
    @staticmethod
    def fill_internal_holes(data: np.ndarray, 
                          fill_value: float = 20.0, 
                          max_hole_size: int = 500) -> np.ndarray:
        """
        填补栅格内部的空洞
        
        Args:
            data: 输入栅格数据
            fill_value: 填充空洞的像元值
            max_hole_size: 最大填充空洞大小
            
        Returns:
            填充后的栅格数据
        """
        foreground = data != 0
        filled = binary_fill_holes(foreground)
        holes = filled & (~foreground)
        
        structure = np.ones((3, 3))
        labeled, _ = label(holes, structure=structure)
        counts = np.bincount(labeled.ravel())
        valid_labels = np.where((counts > 0) & (counts <= max_hole_size))[0]
        mask_fill = np.isin(labeled, valid_labels)
        
        data_filled = data.copy()
        data_filled[mask_fill] = fill_value
        return data_filled
    
    @staticmethod
    def filter_clusters_by_median(data: np.ndarray, 
                                threshold: float = 10.0, 
                                connectivity: int = 8) -> np.ndarray:
        """
        根据团块中像元值的中位数过滤小团块
        
        Args:
            data: 输入栅格数据
            threshold: 中位数阈值
            connectivity: 连通性（4 或 8）
            
        Returns:
            过滤后的栅格数据
        """
        mask = data != 0
        if connectivity == 8:
            structure = np.ones((3, 3))
        else:
            structure = np.array([[0, 1, 0], 
                                 [1, 1, 1], 
                                 [0, 1, 0]])
            
        labeled_array, num_features = label(mask, structure=structure)
        filtered_data = data.copy()
        
        for region_label in range(1, num_features + 1):
            region_mask = labeled_array == region_label
            region_values = data[region_mask]
            median_val = np.median(region_values)
            
            if median_val < threshold:
                filtered_data[region_mask] = 0
                
        return filtered_data


class RasterPreprocessor:
    """栅格数据预处理器"""
    
    def __init__(self):
        self.filter = RasterFilter()
        self.config = PROJECT_CONFIG.processing
        
    def preprocess_tif(self, 
                     input_tif_path: str, 
                     output_tif_path: str, 
                     extract_threshold: float,
                     filter_threshold: float) -> None:
        """
        预处理 TIF 文件
        
        Args:
            input_tif_path: 输入 TIF 文件路径
            output_tif_path: 输出 TIF 文件路径
            extract_threshold: 提取阈值
            filter_threshold: 滤波阈值
        """
        with TimeTracker("栅格数据预处理"):
            FileUtils.ensure_directory_exists(output_tif_path)
            
            with rasterio.open(input_tif_path) as src:
                data = src.read(1)
                profile = src.profile
            
            # 1. 提取像元值大于阈值的区域
            data = self.filter.extract_pixels_above_threshold(data, extract_threshold)
            
            # 2. 局部最大值滤波
            data = self.filter.filter_by_local_maximum(
                data, 
                self.config.LOCAL_MAX_WINDOW_SIZE, 
                filter_threshold
            )
            
            # 3. 移除小团块
            data = self.filter.remove_small_clusters(data, self.config.MIN_CLUSTER_SIZE)
            
            # 4. 填充内部空洞
            data = self.filter.fill_internal_holes(data, self.config.HOLE_FILL_VALUE)
            
            # 5. 中位数滤波
            data = self.filter.filter_clusters_by_median(data, filter_threshold)
            
            # 更新 profile 并保存
            profile.update(dtype=rasterio.float32, count=1, nodata=0.0)
            
            with rasterio.open(output_tif_path, 'w', **profile) as dst:
                dst.write(data.astype(np.float32), 1)
                
            print(f"[INFO]  | 预处理完成: {output_tif_path}")
    
    def apply_otsu_threshold(self, input_tif_path: str, output_tif_path: str) -> None:
        """
        应用 Otsu 阈值进行二值化
        
        Args:
            input_tif_path: 输入 TIF 文件路径
            output_tif_path: 输出 TIF 文件路径
        """
        try:
            import cv2
            from osgeo import gdal, gdal_array
            
            dataset = gdal.Open(input_tif_path, gdal.GA_ReadOnly)
            if dataset is None:
                raise IOError(f"无法打开文件: {input_tif_path}")
                
            geo_transform = dataset.GetGeoTransform()
            projection = dataset.GetProjection()
            band = dataset.GetRasterBand(1)
            data = band.ReadAsArray()
            
            # 转为 uint8 并取绝对值
            data = np.abs(data).astype(np.uint8)
            
            # Otsu 二值化
            _, binary_image = cv2.threshold(data, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 保存结果
            driver = gdal.GetDriverByName('GTiff')
            out_dataset = driver.Create(
                output_tif_path,
                binary_image.shape[1],
                binary_image.shape[0],
                1,
                gdal.GDT_Byte
            )
            out_dataset.SetGeoTransform(geo_transform)
            out_dataset.SetProjection(projection)
            out_band = out_dataset.GetRasterBand(1)
            out_band.WriteArray(binary_image)
            out_band.FlushCache()
            
            out_dataset = None
            dataset = None
            
            print(f"[INFO]  | Otsu 二值化完成: {output_tif_path}")
            
        except ImportError:
            print("[ERROR] | 需要安装 opencv-python 和 gdal 包")
            raise