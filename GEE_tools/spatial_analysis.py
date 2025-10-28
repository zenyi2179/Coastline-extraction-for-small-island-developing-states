# spatial_analysis.py
#!/usr/bin/env python3
"""
空间分析模块
提供几何计算、统计分析、数据合并等空间分析功能
"""

import arcpy
import pandas as pd
from typing import List, Dict, Any, Optional

from config import ProjectConfig
from file_utils import FileOperations


class GeometryCalculator:
    """几何计算器"""
    
    def __init__(self):
        """初始化计算器"""
        arcpy.env.overwriteOutput = True
    
    def calculate_geometry_attributes(
        self, 
        input_features: str, 
        area_field: str = "Geo_Area", 
        length_field: str = "Geo_Length"
    ) -> bool:
        """
        计算几何属性（面积和周长）
        
        Args:
            input_features: 输入要素路径
            area_field: 面积字段名
            length_field: 长度字段名
            
        Returns:
            计算是否成功
        """
        try:
            print(f"[INFO]  | 开始计算几何属性: {input_features}")
            
            # 计算几何属性
            result_features = arcpy.management.CalculateGeometryAttributes(
                in_features=input_features,
                geometry_property=[
                    [area_field, "AREA_GEODESIC"], 
                    [length_field, "PERIMETER_LENGTH_GEODESIC"]
                ],
                length_unit="KILOMETERS",
                area_unit="SQUARE_KILOMETERS",
                coordinate_format="SAME_AS_INPUT"
            )[0]
            
            print(f"[INFO]  | 几何属性计算完成: {input_features}")
            return True
            
        except Exception as e:
            print(f"[ERROR] | 几何属性计算失败 {input_features}: {e}")
            return False
    
    def add_unique_identifier_field(
        self, 
        input_features: str, 
        field_name: str = "UID_ISID", 
        identifier: str = ""
    ) -> bool:
        """
        添加唯一标识符字段
        
        Args:
            input_features: 输入要素路径
            field_name: 字段名称
            identifier: 标识符值
            
        Returns:
            添加是否成功
        """
        try:
            print(f"[INFO]  | 开始添加唯一标识符字段: {input_features}")
            
            # 如果未提供标识符，从文件名中提取
            if not identifier:
                file_name = os.path.basename(input_features)
                # 从文件名中提取 UID（假设格式为 UID_XXXXX.shp）
                if "UID_" in file_name:
                    identifier = file_name.split("UID_")[1].split("_")[0]
                else:
                    identifier = "UNKNOWN"
            
            # 计算字段
            result_features = arcpy.management.CalculateField(
                in_table=input_features,
                field=field_name,
                expression=f"'{identifier}'",
                expression_type="PYTHON3",
                field_type="TEXT"
            )[0]
            
            print(f"[INFO]  | 唯一标识符字段添加完成: {field_name} = {identifier}")
            return True
            
        except Exception as e:
            print(f"[ERROR] | 添加唯一标识符字段失败 {input_features}: {e}")
            return False


class SpatialAnalyzer:
    """空间分析器"""
    
    def __init__(self):
        """初始化分析器"""
        arcpy.env.overwriteOutput = True
        self.geometry_calculator = GeometryCalculator()
    
    def process_coastline_features(
        self, 
        input_features: str, 
        unique_id: Optional[str] = None
    ) -> bool:
        """
        处理海岸线要素，计算几何属性
        
        Args:
            input_features: 输入要素路径
            unique_id: 唯一标识符
            
        Returns:
            处理是否成功
        """
        try:
            print(f"[INFO]  | 开始处理海岸线要素: {input_features}")
            
            # 添加唯一标识符字段
            if unique_id:
                success = self.geometry_calculator.add_unique_identifier_field(
                    input_features, "UID_ISID", unique_id
                )
            else:
                success = self.geometry_calculator.add_unique_identifier_field(
                    input_features, "UID_ISID"
                )
            
            if not success:
                return False
            
            # 计算几何属性
            success = self.geometry_calculator.calculate_geometry_attributes(
                input_features, "Geo_Area", "Geo_Length"
            )
            
            if success:
                print(f"[INFO]  | 海岸线要素处理完成: {input_features}")
            else:
                print(f"[ERROR] | 海岸线要素处理失败")
                
            return success
            
        except Exception as e:
            print(f"[ERROR] | 海岸线要素处理失败 {input_features}: {e}")
            return False
    
    def batch_process_coastline_features(
        self, 
        input_directory: str, 
        file_extension: str = ".shp"
    ) -> int:
        """
        批量处理海岸线要素
        
        Args:
            input_directory: 输入目录
            file_extension: 文件扩展名
            
        Returns:
            成功处理的文件数量
        """
        try:
            print(f"[INFO]  | 开始批量处理海岸线要素: {input_directory}")
            
            # 获取所有要素文件
            feature_files = FileOperations.get_files_with_extension(
                input_directory, file_extension
            )
            
            success_count = 0
            
            for feature_file in feature_files:
                feature_path = os.path.join(input_directory, feature_file)
                
                # 从文件名中提取唯一标识符
                if "UID_" in feature_file:
                    uid = feature_file.split("UID_")[1].split("_")[0]
                else:
                    uid = None
                
                if self.process_coastline_features(feature_path, uid):
                    success_count += 1
            
            print(f"[INFO]  | 批量处理完成: {success_count}/{len(feature_files)} 个文件成功")
            return success_count
            
        except Exception as e:
            print(f"[ERROR] | 批量处理海岸线要素失败 {input_directory}: {e}")
            return 0


class DataExporter:
    """数据导出器"""
    
    def __init__(self):
        """初始化导出器"""
        arcpy.env.overwriteOutput = True
    
    def export_to_shapefile(
        self, 
        input_features: str, 
        output_shapefile: str, 
        where_clause: str = ""
    ) -> bool:
        """
        导出要素到 Shapefile
        
        Args:
            input_features: 输入要素
            output_shapefile: 输出 Shapefile 路径
            where_clause: 查询条件
            
        Returns:
            导出是否成功
        """
        try:
            print(f"[INFO]  | 开始导出到 Shapefile: {input_features}")
            
            # 确保输出目录存在
            FileOperations.ensure_directory_exists(os.path.dirname(output_shapefile))
            
            arcpy.conversion.ExportFeatures(
                in_features=input_features,
                out_features=output_shapefile,
                where_clause=where_clause,
                use_field_alias_as_name="NOT_USE_ALIAS"
            )
            
            print(f"[INFO]  | Shapefile 导出完成: {output_shapefile}")
            return True
            
        except Exception as e:
            print(f"[ERROR] | Shapefile 导出失败 {input_features}: {e}")
            return False
    
    def export_feature_statistics(
        self, 
        input_features: str, 
        output_csv: str, 
        statistics_fields: List[str] = None
    ) -> bool:
        """
        导出要素统计信息到 CSV
        
        Args:
            input_features: 输入要素
            output_csv: 输出 CSV 路径
            statistics_fields: 统计字段列表
            
        Returns:
            导出是否成功
        """
        try:
            print(f"[INFO]  | 开始导出要素统计信息: {input_features}")
            
            if statistics_fields is None:
                statistics_fields = ["Geo_Area", "Geo_Length", "UID_ISID"]
            
            # 读取要素属性表
            data = []
            fields = statistics_fields
            
            with arcpy.da.SearchCursor(input_features, fields) as cursor:
                for row in cursor:
                    row_dict = dict(zip(fields, row))
                    data.append(row_dict)
            
            # 创建 DataFrame 并保存
            df = pd.DataFrame(data)
            df.to_csv(output_csv, index=False, encoding="utf-8")
            
            print(f"[INFO]  | 要素统计信息导出完成: {output_csv}")
            return True
            
        except Exception as e:
            print(f"[ERROR] | 要素统计信息导出失败 {input_features}: {e}")
            return False


class QualityChecker:
    """质量检查器"""
    
    def __init__(self):
        """初始化检查器"""
        self.geometry_calculator = GeometryCalculator()
    
    def validate_coastline_geometry(self, input_features: str) -> Dict[str, Any]:
        """
        验证海岸线几何质量
        
        Args:
            input_features: 输入要素路径
            
        Returns:
            质量检查结果字典
        """
        try:
            print(f"[INFO]  | 开始验证海岸线几何质量: {input_features}")
            
            results = {
                "is_valid": True,
                "feature_count": 0,
                "area_range": (0, 0),
                "length_range": (0, 0),
                "issues": []
            }
            
            # 获取要素数量
            feature_count = arcpy.management.GetCount(input_features)
            results["feature_count"] = int(feature_count[0])
            
            if results["feature_count"] == 0:
                results["is_valid"] = False
                results["issues"].append("要素数量为0")
                return results
            
            # 检查几何有效性
            invalid_count = 0
            with arcpy.da.SearchCursor(input_features, ["SHAPE@"]) as cursor:
                for row in cursor:
                    geometry = row[0]
                    if not geometry or geometry.isNull:
                        invalid_count += 1
            
            if invalid_count > 0:
                results["is_valid"] = False
                results["issues"].append(f"发现 {invalid_count} 个无效几何")
            
            # 检查面积和长度范围
            areas = []
            lengths = []
            
            with arcpy.da.SearchCursor(input_features, ["Geo_Area", "Geo_Length"]) as cursor:
                for row in cursor:
                    area, length = row
                    if area is not None:
                        areas.append(area)
                    if length is not None:
                        lengths.append(length)
            
            if areas:
                results["area_range"] = (min(areas), max(areas))
            if lengths:
                results["length_range"] = (min(lengths), max(lengths))
            
            print(f"[INFO]  | 海岸线几何质量验证完成: {input_features}")
            return results
            
        except Exception as e:
            print(f"[ERROR] | 海岸线几何质量验证失败 {input_features}: {e}")
            return {
                "is_valid": False,
                "feature_count": 0,
                "area_range": (0, 0),
                "length_range": (0, 0),
                "issues": [f"验证过程出错: {str(e)}"]
            }
    
    def generate_quality_report(
        self, 
        input_features: str, 
        output_report: str
    ) -> bool:
        """
        生成质量检查报告
        
        Args:
            input_features: 输入要素路径
            output_report: 输出报告路径
            
        Returns:
            报告生成是否成功
        """
        try:
            print(f"[INFO]  | 开始生成质量检查报告: {input_features}")
            
            # 执行质量检查
            quality_results = self.validate_coastline_geometry(input_features)
            
            # 生成报告内容
            report_lines = [
                "海岸线数据质量检查报告",
                "=" * 50,
                f"数据文件: {os.path.basename(input_features)}",
                f"检查时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "检查结果:",
                f"- 数据有效性: {'通过' if quality_results['is_valid'] else '失败'}",
                f"- 要素数量: {quality_results['feature_count']}",
                f"- 面积范围: {quality_results['area_range'][0]:.4f} - {quality_results['area_range'][1]:.4f} 平方公里",
                f"- 长度范围: {quality_results['length_range'][0]:.4f} - {quality_results['length_range'][1]:.4f} 公里",
                ""
            ]
            
            if quality_results["issues"]:
                report_lines.append("发现问题:")
                for issue in quality_results["issues"]:
                    report_lines.append(f"- {issue}")
            else:
                report_lines.append("未发现问题")
            
            # 写入报告文件
            with open(output_report, "w", encoding="utf-8") as f:
                f.write("\n".join(report_lines))
            
            print(f"[INFO]  | 质量检查报告生成完成: {output_report}")
            return True
            
        except Exception as e:
            print(f"[ERROR] | 质量检查报告生成失败 {input_features}: {e}")
            return False


if __name__ == "__main__":
    # 测试空间分析功能
    analyzer = SpatialAnalyzer()
    exporter = DataExporter()
    quality_checker = QualityChecker()
    
    print("[INFO]  | 空间分析模块测试完成")