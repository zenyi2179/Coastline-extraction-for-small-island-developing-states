# raster_processing.py
#!/usr/bin/env python3
"""
栅格数据处理模块
提供图像插值、指数计算、主成分分析等栅格处理功能
"""

import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform
from rasterio.enums import Resampling
from pyproj import CRS
from scipy.ndimage import zoom
from sklearn.decomposition import PCA
import cv2
from typing import Tuple, Optional, List

from config import ProcessingConfig
from file_utils import FileOperations


class RasterProcessor:
    """栅格处理器基类"""
    
    def __init__(self):
        """初始化处理器"""
        self.target_crs = CRS.from_epsg(4326)  # WGS 84
    
    def read_raster_band(self, raster_path: str, band: int = 1) -> Optional[Tuple[np.ndarray, dict]]:
        """
        读取栅格波段数据
        
        Args:
            raster_path: 栅格文件路径
            band: 波段索引（从1开始）
            
        Returns:
            (波段数据, 元数据) 元组，失败返回 None
        """
        try:
            with rasterio.open(raster_path) as src:
                band_data = src.read(band)
                metadata = {
                    "crs": src.crs,
                    "transform": src.transform,
                    "width": src.width,
                    "height": src.height,
                    "count": src.count
                }
                return band_data, metadata
                
        except Exception as e:
            print(f"[ERROR] | 读取栅格波段失败 {raster_path}: {e}")
            return None
    
    def write_raster(
        self, 
        data: np.ndarray, 
        output_path: str, 
        metadata: dict,
        dtype: str = "float32"
    ) -> bool:
        """
        写入栅格数据
        
        Args:
            data: 栅格数据
            output_path: 输出路径
            metadata: 元数据
            dtype: 数据类型
            
        Returns:
            写入是否成功
        """
        try:
            # 确保输出目录存在
            FileOperations.ensure_directory_exists(os.path.dirname(output_path))
            
            with rasterio.open(
                output_path,
                "w",
                driver="GTiff",
                height=data.shape[0],
                width=data.shape[1],
                count=1,
                dtype=dtype,
                crs=metadata.get("crs", self.target_crs),
                transform=metadata["transform"]
            ) as dst:
                dst.write(data, 1)
            
            print(f"[INFO]  | 栅格数据写入成功: {output_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] | 写入栅格数据失败 {output_path}: {e}")
            return False


class BandInterpolator(RasterProcessor):
    """波段插值器"""
    
    def downscale_by_interpolation(
        self, 
        origin_tif: str, 
        zoom_tif: str, 
        zoom_ratio: int = ProcessingConfig.ZOOM_RATIO
    ) -> bool:
        """
        使用双线性插值方法对栅格图像进行缩放
        
        Args:
            origin_tif: 原始栅格路径
            zoom_tif: 缩放后栅格路径
            zoom_ratio: 缩放比例
            
        Returns:
            处理是否成功
        """
        try:
            print(f"[INFO]  | 开始插值降尺度: {origin_tif}")
            
            # 打开输入图像
            with rasterio.open(origin_tif) as src:
                # 读取原始图像的元数据
                src_crs = src.crs
                transform = src.transform
                band_count = src.count
                
                # 创建用于存储重采样后数据的空列表
                resampled_bands = []
                
                # 对每个波段进行处理
                for band in range(1, band_count + 1):
                    data = src.read(band)  # 读取每个波段的数据
                    resampled_data = zoom(data, zoom_ratio, order=1)  # 双线性插值
                    resampled_bands.append(resampled_data)
                
                # 计算新的地理变换矩阵
                new_transform, new_width, new_height = calculate_default_transform(
                    src_crs, self.target_crs, 
                    src.width * zoom_ratio, src.height * zoom_ratio, 
                    *src.bounds
                )
                
                # 写入新的图像文件
                with rasterio.open(
                    zoom_tif,
                    "w",
                    driver="GTiff",
                    height=new_height,
                    width=new_width,
                    count=band_count,
                    dtype=resampled_bands[0].dtype,
                    crs=self.target_crs,
                    transform=new_transform,
                ) as dst:
                    # 将每个波段写入新的文件
                    for band in range(1, band_count + 1):
                        dst.write(resampled_bands[band - 1], band)
            
            print(f"[INFO]  | 插值降尺度完成: {zoom_tif}")
            return True
            
        except Exception as e:
            print(f"[ERROR] | 插值降尺度失败 {origin_tif}: {e}")
            return False


class IndexCalculator(RasterProcessor):
    """指数计算器"""
    
    def calculate_mndwi(
        self, 
        input_path: str, 
        output_path: str, 
        green_band: int = ProcessingConfig.MNDWI_BAND1,
        swir_band: int = ProcessingConfig.MNDWI_BAND2
    ) -> bool:
        """
        计算 MNDWI（改进的归一化差异水体指数）
        
        Args:
            input_path: 输入图像路径
            output_path: 输出图像路径
            green_band: 绿色波段索引
            swir_band: 短波红外波段索引
            
        Returns:
            计算是否成功
        """
        try:
            print(f"[INFO]  | 开始计算 MNDWI: {input_path}")
            
            # 打开遥感图像文件
            with rasterio.open(input_path) as src:
                # 读取指定的两个波段
                green_data = src.read(green_band).astype(float)
                swir_data = src.read(swir_band).astype(float)
                
                # 计算 MNDWI: (Green - SWIR) / (Green + SWIR)
                denominator = green_data + swir_data + 1e-10  # 避免除零
                mndwi = (green_data - swir_data) / denominator
                
                # 处理无效值
                mndwi = np.nan_to_num(mndwi, nan=0.0, posinf=0.0, neginf=0.0)
                
                # 将比值数据转换为与原图像相同的数据类型
                mndwi = np.clip(mndwi, -1, 1)  # MNDWI 范围通常在 -1 到 1 之间
                mndwi_data = ((mndwi + 1) * 127.5).astype(np.uint8)  # 转换为 0-255 范围
                
                # 创建输出文件的元数据
                out_meta = src.meta.copy()
                out_meta.update({
                    "dtype": "uint8",
                    "count": 1
                })
                
                # 写入输出文件
                with rasterio.open(output_path, "w", **out_meta) as dst:
                    dst.write(mndwi_data, 1)
            
            print(f"[INFO]  | MNDWI 计算完成: {output_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] | MNDWI 计算失败 {input_path}: {e}")
            return False
    
    def calculate_band_ratio(
        self, 
        input_path: str, 
        output_path: str, 
        band1: int, 
        band2: int
    ) -> bool:
        """
        计算通用波段比值
        
        Args:
            input_path: 输入图像路径
            output_path: 输出图像路径
            band1: 第一个波段索引
            band2: 第二个波段索引
            
        Returns:
            计算是否成功
        """
        try:
            with rasterio.open(input_path) as src:
                # 读取指定的两个波段
                band1_data = src.read(band1).astype(float)
                band2_data = src.read(band2).astype(float)
                
                # 计算比值 (band2 - band1) / (band1 + band2)
                denominator = band1_data + band2_data + 1e-10
                ratio = (band2_data - band1_data) / denominator
                
                # 处理无效值
                ratio = np.nan_to_num(ratio, nan=0.0)
                
                # 将比值数据转换
                ratio = np.clip(ratio, 0, 1)
                ratio_data = (ratio * 255).astype(np.uint8)
                
                # 创建输出文件的元数据
                out_meta = src.meta.copy()
                out_meta.update({
                    "dtype": "uint8",
                    "count": 1
                })
                
                # 写入输出文件
                with rasterio.open(output_path, "w", **out_meta) as dst:
                    dst.write(ratio_data, 1)
            
            print(f"[INFO]  | 波段比值计算完成: {output_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] | 波段比值计算失败 {input_path}: {e}")
            return False


class PCAAnalyzer(RasterProcessor):
    """主成分分析器"""
    
    def perform_pca(
        self, 
        input_path: str, 
        output_path: str, 
        n_components: int = 2
    ) -> bool:
        """
        执行主成分分析
        
        Args:
            input_path: 输入图像路径
            output_path: 输出图像路径
            n_components: 主成分数量
            
        Returns:
            分析是否成功
        """
        try:
            print(f"[INFO]  | 开始主成分分析: {input_path}")
            
            # 打开输入的图像文件
            with rasterio.open(input_path) as src:
                # 读取所有波段的数据
                bands_data = []
                for band in range(1, src.count + 1):
                    bands_data.append(src.read(band))
                
                # 将波段数据堆叠并展平
                image_stack = np.dstack(bands_data)
                rows, cols, bands = image_stack.shape
                image_reshaped = image_stack.reshape(rows * cols, bands)
                
                # 处理 NaN 值
                image_reshaped = np.nan_to_num(image_reshaped, nan=np.nanmean(image_reshaped))
                
                # 执行主成分分析
                pca = PCA(n_components=n_components)
                pca_result = pca.fit_transform(image_reshaped)
                
                # 将结果重新变回图像的形状
                pca_bands = []
                for i in range(n_components):
                    pca_band = pca_result[:, i].reshape(rows, cols)
                    pca_bands.append(pca_band)
                
                # 保存PCA结果
                with rasterio.open(
                    output_path,
                    "w",
                    driver="GTiff",
                    height=rows,
                    width=cols,
                    count=n_components,
                    dtype=rasterio.float32,
                    crs=src.crs,
                    transform=src.transform
                ) as dst:
                    for i, pca_band in enumerate(pca_bands, 1):
                        dst.write(pca_band, i)
            
            print(f"[INFO]  | 主成分分析完成: {output_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] | 主成分分析失败 {input_path}: {e}")
            return False


class OtsuThresholder(RasterProcessor):
    """Otsu 阈值处理器"""
    
    def otsu_threshold(self, input_tif_path: str, output_tif_path: str) -> bool:
        """
        使用 Otsu 方法进行阈值分割
        
        Args:
            input_tif_path: 输入 TIFF 路径
            output_tif_path: 输出 TIFF 路径
            
        Returns:
            处理是否成功
        """
        try:
            print(f"[INFO]  | 开始 Otsu 阈值分割: {input_tif_path}")
            
            # 打开TIFF文件
            dataset = rasterio.open(input_tif_path)
            if dataset is None:
                raise IOError(f"无法打开文件: {input_tif_path}")
            
            # 获取图像的地理信息
            geo_transform = dataset.transform
            projection = dataset.crs
            
            # 读取单波段图像数据
            band = dataset.read(1)
            data = np.abs(band).astype(np.uint8)
            
            # 使用Otsu方法计算最佳阈值
            _, binary_image = cv2.threshold(data, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # 创建输出文件
            with rasterio.open(
                output_tif_path,
                "w",
                driver="GTiff",
                height=binary_image.shape[0],
                width=binary_image.shape[1],
                count=1,
                dtype=rasterio.uint8,
                crs=projection,
                transform=geo_transform
            ) as dst:
                dst.write(binary_image, 1)
                dst.nodata = 0
            
            print(f"[INFO]  | Otsu 阈值分割完成: {output_tif_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] | Otsu 阈值分割失败 {input_tif_path}: {e}")
            return False


if __name__ == "__main__":
    # 测试栅格处理功能
    interpolator = BandInterpolator()
    index_calc = IndexCalculator()
    pca_analyzer = PCAAnalyzer()
    otsu_thresholder = OtsuThresholder()
    
    # 测试数据路径
    test_input = "test_input.tif"
    test_output = "test_output.tif"
    
    print("[INFO]  | 栅格处理模块测试完成")