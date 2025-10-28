# coastline_processing.py
#!/usr/bin/env python3
"""
海岸线处理模块
提供海岸线提取、验证、转换等专用处理功能
"""

import arcpy
import xarray as xr
import rioxarray
import geopandas as gpd
from dea_tools.spatial import subpixel_contours
from shapely.geometry import LineString, MultiLineString
from typing import Optional, List, Generator

from config import ProjectConfig, ProcessingConfig
from file_utils import FileOperations, GeoJSONProcessor


class CoastlineExtractor:
    """海岸线提取器"""
    
    def __init__(self):
        """初始化提取器"""
        arcpy.env.overwriteOutput = True
    
    def extract_by_mask(
        self, 
        origin_tif: str, 
        mask: str, 
        identifier: str, 
        output_tif: str
    ) -> bool:
        """
        按掩膜提取有效范围
        
        Args:
            origin_tif: 原始栅格路径
            mask: 掩膜要素路径
            identifier: 标识符
            output_tif: 输出栅格路径
            
        Returns:
            提取是否成功
        """
        try:
            print(f"[INFO]  | 开始按掩膜提取: {origin_tif}")
            
            # 创建内存中的掩膜图层
            shapefile_layer = "in_memory\\mask_layer"
            arcpy.MakeFeatureLayer_management(mask, shapefile_layer)
            
            # 根据标识符选择要素
            where_clause = f"ALL_Uniq = {identifier}"
            arcpy.SelectLayerByAttribute_management(
                shapefile_layer, "NEW_SELECTION", where_clause
            )
            
            # 加载栅格数据
            input_raster = arcpy.Raster(origin_tif)
            mask_layer = shapefile_layer
            
            # 执行按掩膜提取
            with arcpy.EnvManager(extent=mask_layer):
                extracted_raster = arcpy.sa.ExtractByMask(
                    in_raster=input_raster,
                    in_mask_data=mask_layer,
                    extraction_area="INSIDE",
                    analysis_extent=input_raster
                )
                extracted_raster.save(output_tif)
            
            # 清除选择状态
            arcpy.SelectLayerByAttribute_management(shapefile_layer, "CLEAR_SELECTION")
            
            print(f"[INFO]  | 掩膜提取完成: {output_tif}")
            return True
            
        except Exception as e:
            print(f"[ERROR] | 掩膜提取失败 {origin_tif}: {e}")
            return False


class SubpixelWaterlineExtractor:
    """亚像元水线提取器"""
    
    def __init__(self):
        """初始化提取器"""
        self.geojson_processor = GeoJSONProcessor()
    
    def _process_multilinestring(self, geometry: MultiLineString) -> Generator[LineString, None, None]:
        """
        处理 MultiLineString 几何，封闭线段
        
        Args:
            geometry: MultiLineString 几何
            
        Yields:
            封闭后的 LineString
        """
        if isinstance(geometry, MultiLineString):
            for component in geometry.geoms:
                coords = list(component.coords)
                start_point = coords[0]
                end_point = coords[-1]
                
                # 检查首尾点是否一致，不一致则封闭
                if start_point != end_point:
                    coords.append(start_point)  # 封闭
                
                yield LineString(coords)
        else:
            print("[WARN]  | 几何不是 MultiLineString 类型")
    
    def fix_subpixel_extraction(self, input_geojson: str, output_geojson: str) -> bool:
        """
        修复亚像元提取结果，封闭线段
        
        Args:
            input_geojson: 输入 GeoJSON 路径
            output_geojson: 输出 GeoJSON 路径
            
        Returns:
            修复是否成功
        """
        try:
            print(f"[INFO]  | 开始修复亚像元提取: {input_geojson}")
            
            # 读取 GeoJSON 文件
            gdf = gpd.read_file(input_geojson)
            
            # 处理所有要素的几何
            for idx, row in gdf.iterrows():
                geometry = row["geometry"]
                
                if isinstance(geometry, MultiLineString):
                    closed_components = list(self._process_multilinestring(geometry))
                    # 创建封闭后的 MultiLineString 几何
                    closed_multilinestring = MultiLineString(closed_components)
                    gdf.at[idx, "geometry"] = closed_multilinestring
                else:
                    print(f"[WARN]  | 要素 {idx + 1} 不是 MultiLineString")
            
            # 输出结果
            gdf.to_file(output_geojson, driver="GeoJSON")
            print(f"[INFO]  | 亚像元提取修复完成: {output_geojson}")
            return True
            
        except Exception as e:
            print(f"[ERROR] | 亚像元提取修复失败 {input_geojson}: {e}")
            return False
    
    def subpixel_extraction(
        self, 
        input_tif: str, 
        z_values: float = ProcessingConfig.SUBPIXEL_Z_VALUE, 
        subpixel_tif: str = ""
    ) -> bool:
        """
        执行亚像元边界提取
        
        Args:
            input_tif: 输入栅格路径
            z_values: Z 值阈值
            subpixel_tif: 输出 GeoJSON 路径
            
        Returns:
            提取是否成功
        """
        try:
            print(f"[INFO]  | 开始亚像元边界提取: {input_tif}")
            
            # 使用 rasterio 读取 TIFF 文件
            with rasterio.open(input_tif) as src:
                # 读取栅格数据
                raster_data = src.read(1)
                
                # 获取 TIFF 文件的元数据
                transform = src.transform
                crs = src.crs
                
                # 创建坐标数组
                height, width = raster_data.shape
                x_coords = [transform * (col, 0) for col in range(width)]
                y_coords = [transform * (0, row) for row in range(height)]
                
                # 提取X和Y坐标
                x_coords = [x[0] for x in x_coords]
                y_coords = [y[1] for y in y_coords]
                
                # 将数据转换为 xarray DataArray
                data_array = xr.DataArray(
                    raster_data,
                    coords=[y_coords, x_coords],
                    dims=["y", "x"],
                    attrs={
                        "crs": str(crs),
                        "transform": transform
                    }
                )
            
            # 使用 rioxarray 设置 CRS
            data_array = data_array.rio.write_crs("EPSG:4326", inplace=True)
            
            # 生成临时输出路径
            temp_output = subpixel_tif.replace(".geojson", "_temp.geojson")
            
            # 执行亚像元轮廓提取
            subpixel_contours(
                da=data_array, 
                z_values=z_values, 
                attribute_df=None, 
                output_path=temp_output
            )
            
            # 修复闭合线段
            success = self.fix_subpixel_extraction(temp_output, subpixel_tif)
            
            # 清理临时文件
            if os.path.exists(temp_output):
                os.remove(temp_output)
            
            if success:
                print(f"[INFO]  | 亚像元边界提取完成: {subpixel_tif}")
            else:
                print(f"[ERROR] | 亚像元边界提取修复失败")
                
            return success
            
        except Exception as e:
            print(f"[ERROR] | 亚像元边界提取失败 {input_tif}: {e}")
            return False


class CoastlineValidator:
    """海岸线验证器"""
    
    def __init__(self):
        """初始化验证器"""
        arcpy.env.overwriteOutput = True
    
    def _export_largest_area_feature(
        self, 
        input_feature: str, 
        output_feature: str, 
        area_field: str = "Shape_Area"
    ) -> bool:
        """
        导出面积最大的要素
        
        Args:
            input_feature: 输入要素路径
            output_feature: 输出要素路径
            area_field: 面积字段名
            
        Returns:
            导出是否成功
        """
        try:
            max_area = None
            max_feature_oid = None
            
            # 使用 SearchCursor 遍历所有要素，寻找面积最大的要素
            with arcpy.da.SearchCursor(input_feature, ["OID@", area_field]) as cursor:
                for row in cursor:
                    oid, area_value = row
                    if max_area is None or area_value > max_area:
                        max_area = area_value
                        max_feature_oid = oid
            
            # 如果找到了最大面积的要素，执行导出
            if max_feature_oid is not None:
                where_clause = f"OID = {max_feature_oid}"
                arcpy.conversion.ExportFeatures(
                    in_features=input_feature,
                    out_features=output_feature,
                    where_clause=where_clause
                )
                print(f"[INFO]  | 最大面积要素导出完成: {output_feature}")
                return True
            else:
                print("[WARN]  | 未找到有效的面积要素")
                return False
                
        except Exception as e:
            print(f"[ERROR] | 导出最大面积要素失败: {e}")
            return False
    
    def geojson_to_polygon(
        self, 
        extract_geojson: str, 
        shp_mask: str, 
        identifier: str, 
        tolerance: int = ProcessingConfig.SMOOTH_TOLERANCE,
        coast_line_shp: str = ""
    ) -> bool:
        """
        将 GeoJSON 转换为有效的海岸线面要素
        
        Args:
            extract_geojson: 输入 GeoJSON 路径
            shp_mask: 掩膜要素路径
            identifier: 标识符
            tolerance: 平滑容差
            coast_line_shp: 输出海岸线要素路径
            
        Returns:
            转换是否成功
        """
        try:
            print(f"[INFO]  | 开始 GeoJSON 到面要素转换: {extract_geojson}")
            
            # 1. JSON 转要素
            json_to_feature = "in_memory\\JSONToFeature"
            arcpy.conversion.JSONToFeatures(
                in_json_file=extract_geojson,
                out_features=json_to_feature,
                geometry_type="POLYLINE"
            )
            
            # 2. 平滑线
            smooth_line = "in_memory\\SmoothLine"
            with arcpy.EnvManager(transferGDBAttributeProperties="false"):
                arcpy.cartography.SmoothLine(
                    in_features=json_to_feature,
                    out_feature_class=smooth_line,
                    algorithm="PAEK",
                    tolerance=f"{tolerance} Meters",
                    endpoint_option="FIXED_CLOSED_ENDPOINT"
                )
            
            # 3. 要素转面
            feature_to_polygon = "in_memory\\FeatureToPolygon"
            arcpy.management.FeatureToPolygon(
                in_features=[smooth_line],
                out_feature_class=feature_to_polygon,
                attributes="ATTRIBUTES"
            )
            
            # 4. 缓冲区修复空洞
            polygon_fixed = "in_memory\\PolygonFixed"
            
            # 正向缓冲区
            buffer_temp = "in_memory\\BufferTemp"
            arcpy.analysis.Buffer(
                in_features=feature_to_polygon,
                out_feature_class=buffer_temp,
                buffer_distance_or_field=f"{ProcessingConfig.BUFFER_DISTANCE} Meters",
                line_side="FULL",
                line_end_type="ROUND",
                dissolve_option="NONE",
                method="PLANAR"
            )
            
            # 负向缓冲区
            arcpy.analysis.Buffer(
                in_features=buffer_temp,
                out_feature_class=polygon_fixed,
                buffer_distance_or_field=f"-{ProcessingConfig.BUFFER_DISTANCE} Meters",
                line_side="FULL",
                line_end_type="ROUND",
                dissolve_option="NONE",
                method="PLANAR"
            )
            
            # 5. 要素转点找到中心点
            polygon_points = "in_memory\\PolygonPoints"
            arcpy.management.FeatureToPoint(
                in_features=polygon_fixed,
                out_feature_class=polygon_points,
                point_location="INSIDE"
            )
            
            # 6. 创建掩膜图层并选择
            mask_layer = "in_memory\\MaskLayer"
            arcpy.MakeFeatureLayer_management(shp_mask, mask_layer)
            
            where_clause = f"ALL_Uniq = {identifier}"
            arcpy.SelectLayerByAttribute_management(mask_layer, "NEW_SELECTION", where_clause)
            
            # 7. 选择有效中心点
            valid_points_layer = arcpy.management.SelectLayerByLocation(
                in_layer=[polygon_points],
                overlap_type="INTERSECT",
                select_features=mask_layer,
                search_distance="30 Meters",
                selection_type="NEW_SELECTION",
                invert_spatial_relationship="NOT_INVERT"
            )[0]
            
            valid_points = "in_memory\\ValidPoints"
            arcpy.conversion.ExportFeatures(
                in_features=valid_points_layer,
                out_features=valid_points
            )
            
            # 清除选择状态
            arcpy.SelectLayerByAttribute_management(mask_layer, "CLEAR_SELECTION")
            arcpy.SelectLayerByAttribute_management(polygon_points, "CLEAR_SELECTION")
            
            # 8. 连接字段并选择有效图形
            polygon_linked = arcpy.management.JoinField(
                in_data=polygon_fixed,
                in_field="OBJECTID",
                join_table=valid_points,
                join_field="ORIG_FID"
            )[0]
            
            # 9. 导出与中心点相交的图形
            selected_polygons = "in_memory\\SelectedPolygons"
            arcpy.conversion.ExportFeatures(
                in_features=polygon_linked,
                out_features=selected_polygons,
                where_clause="BUFF_DIST_1 <> 0"
            )
            
            # 10. 计算几何属性
            polygons_with_geometry = arcpy.management.CalculateGeometryAttributes(
                in_features=selected_polygons,
                geometry_property=[["Shape_Area", "AREA_GEODESIC"]],
                coordinate_format="SAME_AS_INPUT"
            )[0]
            
            # 11. 导出面积最大的要素
            success = self._export_largest_area_feature(
                polygons_with_geometry, coast_line_shp, "Shape_Area"
            )
            
            if success:
                print(f"[INFO]  | GeoJSON 到面要素转换完成: {coast_line_shp}")
            else:
                print(f"[ERROR] | GeoJSON 到面要素转换失败")
                
            return success
            
        except Exception as e:
            print(f"[ERROR] | GeoJSON 到面要素转换失败 {extract_geojson}: {e}")
            return False


if __name__ == "__main__":
    # 测试海岸线处理功能
    extractor = CoastlineExtractor()
    subpixel_extractor = SubpixelWaterlineExtractor()
    validator = CoastlineValidator()
    
    print("[INFO]  | 海岸线处理模块测试完成")