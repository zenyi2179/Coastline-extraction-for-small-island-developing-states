#!/usr/bin/env python3
"""
ArcGIS 空间分析操作模块
提供裁剪、融合、要素转换等 ArcGIS 空间分析功能
"""

import arcpy
from typing import List, Optional


class ArcGISOperations:
    """ArcGIS 空间分析操作类"""

    def __init__(self, overwrite_output: bool = True) -> None:
        """
        初始化 ArcGIS 操作类

        Args:
            overwrite_output: 是否覆盖输出，默认为 True
        """
        arcpy.env.overwriteOutput = overwrite_output
        print(f"[INFO]  | ArcGIS 操作初始化完成，覆盖输出: {overwrite_output}")

    def delete_feature(self, feature_path: str) -> None:
        """
        删除要素文件

        Args:
            feature_path: 要素文件路径

        Raises:
            arcpy.ExecuteError: ArcGIS 执行错误
        """
        print(f"[INFO]  | 开始删除要素: {feature_path}")
        try:
            arcpy.Delete_management(feature_path)
            print(f"[INFO]  | 成功删除要素: {feature_path}")
        except Exception as error:
            print(f"[ERROR] | 删除要素失败 {feature_path}: {error}")
            raise

    def merge_features(
        self, input_features: List[str], output_feature: str
    ) -> None:
        """
        合并多个要素类

        Args:
            input_features: 输入要素路径列表
            output_feature: 输出要素路径

        Raises:
            arcpy.ExecuteError: ArcGIS 执行错误
        """
        print(f"[INFO]  | 开始合并要素，输出: {output_feature}")
        try:
            arcpy.management.Merge(inputs=input_features, output=output_feature)
            print(f"[INFO]  | 成功合并要素: {output_feature}")
        except Exception as error:
            print(f"[ERROR] | 合并要素失败: {error}")
            raise

    def export_features(self, in_features: str, out_features: str) -> None:
        """
        导出要素类

        Args:
            in_features: 输入要素路径
            out_features: 输出要素路径

        Raises:
            arcpy.ExecuteError: ArcGIS 执行错误
        """
        print(f"[INFO]  | 开始导出要素: {in_features} -> {out_features}")
        try:
            arcpy.conversion.ExportFeatures(in_features, out_features)
            print(f"[INFO]  | 成功导出要素: {out_features}")
        except Exception as error:
            print(f"[ERROR] | 导出要素失败: {error}")
            raise

    def clip_features(
        self, in_features: str, clip_features: str, out_feature_class: str
    ) -> None:
        """
        裁剪要素类

        Args:
            in_features: 输入要素路径
            clip_features: 裁剪要素路径
            out_feature_class: 输出要素路径

        Raises:
            arcpy.ExecuteError: ArcGIS 执行错误
        """
        print(f"[INFO]  | 开始裁剪要素: {in_features}")
        try:
            arcpy.analysis.PairwiseClip(
                in_features=in_features,
                clip_features=clip_features,
                out_feature_class=out_feature_class,
            )
            print(f"[INFO]  | 成功裁剪要素: {out_feature_class}")
        except Exception as error:
            print(f"[ERROR] | 裁剪要素失败: {error}")
            raise

    def dissolve_features(
        self,
        in_features: str,
        out_feature_class: str,
        multi_part: str = "SINGLE_PART",
    ) -> None:
        """
        融合要素类

        Args:
            in_features: 输入要素路径
            out_feature_class: 输出要素路径
            multi_part: 多部分要素处理方式
                       "SINGLE_PART" - 输出中不包含多部件要素
                       "MULTI_PART" - 输出中将包含多部件要素（默认）

        Raises:
            arcpy.ExecuteError: ArcGIS 执行错误
        """
        print(f"[INFO]  | 开始融合要素: {in_features}")
        try:
            arcpy.analysis.PairwiseDissolve(
                in_features, out_feature_class, multi_part
            )
            print(f"[INFO]  | 成功融合要素: {out_feature_class}")
        except Exception as error:
            print(f"[ERROR] | 融合要素失败: {error}")
            raise

    def feature_to_line(
        self, in_features: str, out_feature_class: str
    ) -> None:
        """
        要素转线

        Args:
            in_features: 输入要素路径
            out_feature_class: 输出线要素路径

        Raises:
            arcpy.ExecuteError: ArcGIS 执行错误
        """
        print(f"[INFO]  | 开始要素转线: {in_features}")
        try:
            arcpy.management.FeatureToLine(in_features, out_feature_class)
            print(f"[INFO]  | 成功要素转线: {out_feature_class}")
        except Exception as error:
            print(f"[ERROR] | 要素转线失败: {error}")
            raise

    def feature_to_polygon(
        self, in_features: List[str], out_feature_class: str
    ) -> None:
        """
        要素转面

        Args:
            in_features: 输入要素路径列表
            out_feature_class: 输出面要素路径

        Raises:
            arcpy.ExecuteError: ArcGIS 执行错误
        """
        print(f"[INFO]  | 开始要素转面，输出: {out_feature_class}")
        try:
            arcpy.FeatureToPolygon_management(in_features, out_feature_class)
            print(f"[INFO]  | 成功要素转面: {out_feature_class}")
        except Exception as error:
            print(f"[ERROR] | 要素转面失败: {error}")
            raise

    def clear_selection(self, layer: str) -> None:
        """
        清除图层选择

        Args:
            layer: 图层名称或路径

        Raises:
            arcpy.ExecuteError: ArcGIS 执行错误
        """
        print(f"[INFO]  | 开始清除选择: {layer}")
        try:
            arcpy.management.SelectLayerByAttribute(
                layer, "CLEAR_SELECTION"
            )
            print(f"[INFO]  | 成功清除选择: {layer}")
        except Exception as error:
            print(f"[ERROR] | 清除选择失败: {error}")
            raise


def main() -> None:
    """主函数示例"""
    arc_ops = ArcGISOperations()

    # 删除要素示例
    arc_ops.delete_feature("majorrds.shp")

    # 合并要素示例
    arc_ops.merge_features(
        input_features=["majorrds.shp", "Habitat_Analysis.gdb/futrds"],
        output_feature="C:/output/Output.gdb/allroads",
    )

    # 裁剪要素示例
    arc_ops.clip_features(
        in_features="majorrds.shp",
        clip_features="study_quads.shp",
        out_feature_class="C:/output/studyarea.shp",
    )

    # 融合要素示例
    arc_ops.dissolve_features(
        in_features="taxlots",
        out_feature_class="C:/output/output.gdb/taxlots_dissolved",
        multi_part="SINGLE_PART",
    )


if __name__ == "__main__":
    main()