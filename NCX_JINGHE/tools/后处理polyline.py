import arcpy
import os
import time
from worktools import read_txt_to_list

# 允许覆盖已有输出
arcpy.env.overwriteOutput = True


def process_shapefiles_to_single_line_37(input_shapefile, output_shapefile):
    """
    将多边形要素转换为单个融合线要素，并计算几何属性。
    会在处理前自动修复几何，以避免拓扑错误。
    """
    start_time = time.time()
    print(f"[INFO]  | 任务启动，PID={os.getpid()}")

    # Step 0: 修复几何
    repaired_shapefile = r"in_memory\repaired_polygon"
    arcpy.management.RepairGeometry(
        in_features=input_shapefile,
        delete_null="DELETE_NULL"
    )
    # 将修复后的结果复制到内存
    arcpy.management.CopyFeatures(input_shapefile, repaired_shapefile)
    print(f"[INFO]  | 几何修复完成：{input_shapefile}")

    # Step 1: 多边形转线
    temp_line_path = r"in_memory\temp_line"
    arcpy.management.FeatureToLine(
        in_features=[repaired_shapefile],
        out_feature_class=temp_line_path
    )
    print(f"[INFO]  | 多边形转换为线完成：{repaired_shapefile} -> {temp_line_path}")

    # Step 2: 删除无用字段
    try:
        arcpy.management.DeleteField(
            in_table=temp_line_path,
            drop_field=["Id", "area_geo"]
        )
    except Exception as e:
        print(f"[WARN]  | 字段删除时出现问题（可能不存在）：{e}")

    # Step 3: 融合所有线为一个整体
    temp_dissolved_path = r"in_memory\dissolved_line"
    arcpy.management.Dissolve(
        in_features=temp_line_path,
        out_feature_class=temp_dissolved_path
    )

    # Step 4: 保存融合结果到输出路径
    arcpy.management.CopyFeatures(
        in_features=temp_dissolved_path,
        out_feature_class=output_shapefile
    )
    print(f"[INFO]  | 融合线保存到：{output_shapefile}")

    # Step 5: 计算几何属性（线长）
    arcpy.management.CalculateGeometryAttributes(
        in_features=output_shapefile,
        geometry_property=[["leng_geo", "LENGTH_GEODESIC"]],
        length_unit="KILOMETERS",
        area_unit="SQUARE_KILOMETERS"
    )

    # Step 6: 统计运行时间
    elapsed_time = time.time() - start_time
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"[TIME]  | 总耗时: {int(hours):02d}h{int(minutes):02d}m{int(seconds):02d}s")


def process_shapefiles_to_single_line_9(input_shapefile, input_mask, output_shapefile):
    """
    将多边形要素转换为单个融合线要素，并计算几何属性。

    :param input_shapefile: 输入多边形 shapefile 文件路径
    :param output_shapefile: 最终输出的单一线 shapefile 文件路径
    """
    start_time = time.time()
    print(f"[INFO]  | 任务启动，PID={os.getpid()}")

    # Step 1: 多边形转线
    temp_line_path = r"in_memory\temp_line"
    arcpy.management.FeatureToLine(
        in_features=[input_shapefile],
        out_feature_class=temp_line_path
    )
    print(f"[INFO]  | 多边形转换为线完成：{input_shapefile} -> {temp_line_path}")

    # Step 2: 删除无用字段
    try:
        arcpy.management.DeleteField(
            in_table=temp_line_path,
            drop_field=["Id", "area_geo"]
        )
        # print(f"[INFO]  | 字段清理完成：Id, area_geo")
    except Exception as e:
        print(f"[WARN]  | 字段删除时出现问题（可能不存在）：{e}")

    # Process: 成对裁剪 (成对裁剪) (analysis)
    temp_pairwise_path = r"in_memory\temp_pairwise_path"
    arcpy.analysis.PairwiseClip(
        in_features=temp_line_path,
        clip_features=input_mask,
        out_feature_class=temp_pairwise_path
    )

    # Step 3: 融合所有线为一个整体
    temp_dissolved_path = r"in_memory\dissolved_line"
    arcpy.management.Dissolve(
        in_features=temp_pairwise_path,
        out_feature_class=temp_dissolved_path
    )
    # print(f"[INFO]  | 融合完成：{temp_line_path} -> {temp_dissolved_path}")

    # Step 4: 保存融合结果到输出路径
    arcpy.management.CopyFeatures(
        in_features=temp_dissolved_path,
        out_feature_class=output_shapefile
    )
    print(f"[INFO]  | 融合线保存到：{output_shapefile}")

    # Step 5: 计算几何属性（线长）
    arcpy.management.CalculateGeometryAttributes(
        in_features=output_shapefile,
        geometry_property=[["leng_geo", "LENGTH_GEODESIC"]],
        length_unit="KILOMETERS",
        area_unit="SQUARE_KILOMETERS"
    )

    # Step 6: 统计运行时间
    elapsed_time = time.time() - start_time
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"[TIME]  | 总耗时: {int(hours):02d}h{int(minutes):02d}m{int(seconds):02d}s")


def main():
    """
    主函数：批量处理多个岛屿的多边形数据，转换为单一线要素。
    """
    base_workspace = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1"
    base_mask = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\boundary\boun_mask"

    # list_sids = read_txt_to_list("SIDS_37.txt")
    # list_sids = read_txt_to_list("SIDS_Clip_9.txt")
    # list_sids = ['TUV', 'MHL']
    # list_sids = ['COM', 'DOM', 'STP', 'FJI']
    list_sids = ['STP']

    # 测试用
    # list_years = [2010, 2015, 2020]
    list_years = [2020]

    for island_code in list_sids:
        for year in list_years:
            input_shapefile = os.path.join(
                base_workspace,
                fr"{island_code}\{island_code}_polygon_{year}.shp"
            )
            output_shapefile = os.path.join(
                base_workspace,
                fr"{island_code}\{island_code}_polyline_{year}.shp"
            )
            input_mask = os.path.join(base_mask, fr'{island_code}_v3.shp')

            process_shapefiles_to_single_line_37(input_shapefile, output_shapefile)
            # process_shapefiles_to_single_line_9(input_shapefile, input_mask, output_shapefile)


if __name__ == '__main__':
    main()
