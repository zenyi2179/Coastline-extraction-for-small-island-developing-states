# gee_operations.py
#!/usr/bin/env python3
"""
Google Earth Engine 操作模块
处理 GEE 数据上传、下载、资产管理和图像处理
"""

import os
import time
import ee
from datetime import datetime
from typing import List, Optional, Dict, Any, Callable

from auth import initialize_earth_engine
from config import GEEConfig, ProcessingConfig
from file_utils import FileOperations


class GEETaskManager:
    """GEE 任务管理器"""
    
    def __init__(self):
        """初始化任务管理器"""
        if not initialize_earth_engine():
            raise RuntimeError("Earth Engine 初始化失败")
    
    @staticmethod
    def cancel_active_tasks() -> int:
        """
        取消所有正在运行的任务
        
        Returns:
            取消的任务数量
        """
        tasks = ee.batch.Task.list()
        cancelled_count = 0
        
        for task in tasks:
            status = task.status()
            if status["state"] in ["READY", "RUNNING"]:
                task.cancel()
                print(f"[INFO]  | 取消任务: {status['description']} ({status['state']})")
                cancelled_count += 1
        
        print(f"[INFO]  | 共取消 {cancelled_count} 个活动任务")
        return cancelled_count
    
    @staticmethod
    def delete_completed_tasks() -> int:
        """
        删除所有已完成的任务
        
        Returns:
            删除的任务数量
        """
        tasks = ee.batch.Task.list()
        deleted_count = 0
        
        for task in tasks:
            status = task.status()
            if status["state"] in ["COMPLETED", "FAILED", "CANCELLED"]:
                task_id = status["id"]
                ee.data.deleteTask(task_id)
                print(f"[INFO]  | 删除任务: {status['description']} ({status['state']})")
                deleted_count += 1
        
        print(f"[INFO]  | 共删除 {deleted_count} 个已完成任务")
        return deleted_count
    
    def clear_all_tasks(self) -> None:
        """清除所有任务"""
        print("[INFO]  | 开始清理 GEE 任务...")
        self.cancel_active_tasks()
        self.delete_completed_tasks()
        print("[INFO]  | 任务清理完成")


class GEEAssetManager:
    """GEE 资产管理器"""
    
    def __init__(self):
        """初始化资产管理器"""
        if not initialize_earth_engine():
            raise RuntimeError("Earth Engine 初始化失败")
    
    def list_assets_in_folder(self, folder_path: str) -> List[str]:
        """
        列出指定文件夹下的所有资产名称
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            包含资产名称的列表
        """
        assets = []
        
        def _list_assets(prefix: str) -> None:
            try:
                response = ee.data.listAssets({"parent": prefix})
                
                for asset in response["assets"]:
                    asset_name = asset["name"]
                    assets.append(asset_name)
                    
                    # 递归处理子文件夹
                    if "assets" in asset and len(asset["assets"]) > 0:
                        _list_assets(asset_name + "/")
                        
            except ee.EEException as e:
                print(f"[ERROR] | 列出资产失败 {prefix}: {e}")
        
        _list_assets(folder_path)
        print(f"[INFO]  | 在 {folder_path} 中找到 {len(assets)} 个资产")
        return assets
    
    def delete_asset_if_exists(self, asset_path: str) -> bool:
        """
        检查并删除指定的资产路径，如果存在的话
        
        Args:
            asset_path: 资产路径
            
        Returns:
            是否执行了删除操作
        """
        try:
            asset = ee.data.getAsset(asset_path)
            ee.data.deleteAsset(asset_path)
            print(f"[INFO]  | 删除资产: {asset_path}")
            return True
            
        except ee.EEException as e:
            if "not found" in str(e):
                # 资产不存在，无需处理
                return False
            else:
                print(f"[ERROR] | 检查资产失败 {asset_path}: {e}")
                raise
    
    def delete_asset_folder(self, delete_path: str) -> bool:
        """
        递归删除指定的资产文件夹及其所有内容
        
        Args:
            delete_path: 要删除的文件夹路径
            
        Returns:
            删除是否成功
        """
        try:
            print(f"[INFO]  | 正在删除资产文件夹: {delete_path}")
            
            # 获取该文件夹下的所有资产
            assets = ee.data.getList({"id": delete_path})
            for asset in assets:
                asset_id = asset["id"]
                asset_type = asset["type"]
                
                if asset_type == "FOLDER":
                    # 递归删除子文件夹
                    self.delete_asset_folder(asset_id)
                else:
                    # 删除文件资产
                    ee.data.deleteAsset(asset_id)
                    print(f"[INFO]  | 删除资产: {asset_id}")
                
                # 为避免触发速率限制，添加短暂延时
                time.sleep(1)
            
            # 删除空文件夹
            ee.data.deleteAsset(delete_path)
            print(f"[INFO]  | 删除文件夹: {delete_path}")
            return True
            
        except ee.EEException as e:
            if "not found" in str(e):
                print(f"[WARN]  | 资产不存在，无需删除: {delete_path}")
                return True
            else:
                print(f"[ERROR] | 删除资产失败 {delete_path}: {e}")
                return False


class GEEImageProcessor:
    """GEE 图像处理器"""
    
    def __init__(self):
        """初始化图像处理器"""
        if not initialize_earth_engine():
            raise RuntimeError("Earth Engine 初始化失败")
    
    def _mask_landsat_clouds(self, image: ee.Image) -> ee.Image:
        """
        遮蔽 Landsat 8 图像中的云
        
        Args:
            image: 输入图像
            
        Returns:
            云遮蔽后的图像
        """
        # 使用内置的 QA 波段来进行云掩膜
        qa_band = image.select("QA_PIXEL")
        cloud_mask = (
            qa_band.bitwiseAnd(1 << 5).eq(0)
            .And(qa_band.bitwiseAnd(1 << 3).eq(0))
            .And(qa_band.bitwiseAnd(1 << 4).eq(0))
        )
        return image.updateMask(cloud_mask).divide(10000)
    
    def _mask_sentinel_clouds(self, image: ee.Image) -> ee.Image:
        """
        遮蔽 Sentinel-2 图像中的云
        
        Args:
            image: 输入图像
            
        Returns:
            云遮蔽后的图像
        """
        qa_band = image.select("QA60")
        cloud_mask = (
            qa_band.bitwiseAnd(1 << 10).eq(0)
            .And(qa_band.bitwiseAnd(1 << 11).eq(0))
        )
        return image.updateMask(cloud_mask).divide(10000)
    
    def get_landsat_collection(
        self, 
        geometry: ee.Geometry, 
        year: int,
        max_cloud_cover: int = GEEConfig.MAX_CLOUD_COVER
    ) -> ee.ImageCollection:
        """
        获取 Landsat 图像集合
        
        Args:
            geometry: 几何范围
            year: 年份
            max_cloud_cover: 最大云覆盖百分比
            
        Returns:
            Landsat 图像集合
        """
        start_date = ee.Date.fromYMD(year, 1, 1)
        end_date = ee.Date.fromYMD(year + 1, 1, 1)
        
        collection = (
            ee.ImageCollection(GEEConfig.LANDSAT_COLLECTION)
            .filterBounds(geometry)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lte("CLOUD_COVER", max_cloud_cover))
        )
        
        # 应用云遮蔽
        collection = collection.map(self._mask_landsat_clouds)
        
        return collection
    
    def get_sentinel_collection(
        self, 
        geometry: ee.Geometry, 
        year: int,
        max_cloudy_pixel_percentage: int = GEEConfig.MAX_CLOUDY_PIXEL_PERCENTAGE
    ) -> ee.ImageCollection:
        """
        获取 Sentinel-2 图像集合
        
        Args:
            geometry: 几何范围
            year: 年份
            max_cloudy_pixel_percentage: 最大云像素百分比
            
        Returns:
            Sentinel-2 图像集合
        """
        start_date = datetime(year, 1, 1)
        end_date = datetime(year + 1, 1, 1)
        
        collection = (
            ee.ImageCollection(GEEConfig.SENTINEL_COLLECTION)
            .filterBounds(geometry)
            .filterDate(start_date, end_date)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", max_cloudy_pixel_percentage))
        )
        
        # 应用云遮蔽
        collection = collection.map(self._mask_sentinel_clouds)
        
        return collection
    
    def export_landsat_mndwi_bands(
        self, 
        boundary_asset: str, 
        year: int, 
        output_folder: str
    ) -> bool:
        """
        导出 Landsat MNDWI 波段
        
        Args:
            boundary_asset: 边界资产路径
            year: 年份
            output_folder: 输出文件夹
            
        Returns:
            任务是否成功启动
        """
        try:
            # 加载边界数据集
            admin_boundary = ee.FeatureCollection(boundary_asset)
            boundary_geometry = admin_boundary.geometry()
            
            # 获取 Landsat 图像集合
            landsat_collection = self.get_landsat_collection(boundary_geometry, year)
            
            # 检查图像集合的大小
            num_images = landsat_collection.size().getInfo()
            if num_images == 0:
                print(f"[WARN]  | 在指定日期范围和云覆盖条件下未找到图像: {boundary_asset}")
                return False
            
            # 计算中值图像并按边界裁剪
            clipped_median = landsat_collection.median().clip(boundary_geometry)
            
            # 选择 MNDWI 计算所需的波段
            clipped_median = clipped_median.select(["SR_B4", "SR_B3", "SR_B2", "SR_B6"])
            
            # 提取资产名称
            asset_name = boundary_asset.split("/")[-1]
            
            # 创建导出任务
            task = ee.batch.Export.image.toDrive(
                image=clipped_median,
                folder=output_folder,
                fileNamePrefix=asset_name,
                region=boundary_geometry,
                scale=30,
                maxPixels=1e13,
                description=f"Download Landsat MNDWI bands {asset_name}"
            )
            
            task.start()
            print(f"[INFO]  | 任务启动: {asset_name}")
            return True
            
        except Exception as e:
            print(f"[ERROR] | 导出 Landsat MNDWI 波段失败 {boundary_asset}: {e}")
            return False
    
    def wait_for_task_completion(self, task: ee.batch.Task, check_interval: int = 10) -> bool:
        """
        等待任务完成
        
        Args:
            task: GEE 任务
            check_interval: 检查间隔（秒）
            
        Returns:
            任务是否成功完成
        """
        print(f"[INFO]  | 等待任务完成: {task.status()['description']}")
        
        while True:
            if not task.active():
                status = task.status()
                if status["state"] == "COMPLETED":
                    print(f"[INFO]  | 任务完成: {status['description']}")
                    return True
                else:
                    print(f"[ERROR] | 任务失败: {status['description']} - {status['state']}")
                    return False
            
            time.sleep(check_interval)


if __name__ == "__main__":
    # 测试 GEE 操作
    try:
        # 清理任务
        task_manager = GEETaskManager()
        task_manager.clear_all_tasks()
        
        # 测试资产管理
        asset_manager = GEEAssetManager()
        assets = asset_manager.list_assets_in_folder(GEEConfig.ISLANDS_ASSET_PATH)
        print(f"[INFO]  | 找到 {len(assets)} 个岛屿资产")
        
    except Exception as e:
        print(f"[ERROR] | GEE 操作测试失败: {e}")