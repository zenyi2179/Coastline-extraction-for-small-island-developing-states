import arcpy
import os
import random

arcpy.env.overwriteOutput = True

# 定义数据集和目标点数的字典
dict_datasets = {
    "GCL_FCS30_2010": 760,
    "GSV_2015": 3736,
    "GMSSD_2015": 3580,
    "GCL_FCS30_2015": 741,
    "OSM_2020": 1887,
    "GCL_FCS30_2020": 732,
}

# 定义目标坐标系为 GCS_WGS_1984
target_spatial_reference = arcpy.SpatialReference(4326)  # GCS_WGS_1984

def calculate_near_distance(point_shp: str, line_shp: str, output_folder: str) -> None:
    """
    计算点要素与线要素的近邻距离，并添加字段 NEAR_DIST。
    删除 NEAR_DIST 大于 500 的点，并打印剩余点的数量。
    如果剩余点数量大于目标点数，则随机删除多余的点。

    Args:
        point_shp: 点要素的shp文件路径
        line_shp: 线要素的shp文件路径
        output_folder: 输出文件夹路径
    """
    # 检查输入文件是否存在
    if not os.path.exists(point_shp):
        raise FileNotFoundError(f"[ERROR] | 输入的点shp文件路径不存在：{point_shp}")
    if not os.path.exists(line_shp):
        raise FileNotFoundError(f"[ERROR] | 输入的线shp文件路径不存在：{line_shp}")
    if not os.path.exists(output_folder):
        raise FileNotFoundError(f"[ERROR] | 输出文件夹路径不存在：{output_folder}")

    # 获取文件名（不包含扩展名）
    point_shp_name = os.path.splitext(os.path.basename(point_shp))[0]

    # 检查文件名是否在字典中
    if point_shp_name not in dict_datasets:
        raise ValueError(f"[ERROR] | 文件名 {point_shp_name} 不在字典中")

    target_count = dict_datasets[point_shp_name]

    # 将点要素投影到GCS_WGS_1984
    output_point_shp = os.path.join(output_folder, os.path.basename(point_shp))
    arcpy.Project_management(point_shp, output_point_shp, target_spatial_reference)
    print(f"[INFO]  | 点要素已投影到GCS_WGS_1984：{output_point_shp}")

    # 添加字段 NEAR_DIST
    arcpy.AddField_management(output_point_shp, "NEAR_DIST", "DOUBLE")

    # 计算近邻距离
    arcpy.Near_analysis(output_point_shp, line_shp, method="GEODESIC")
    print(f"[INFO]  | 近邻距离计算完成，结果已保存到：{output_point_shp}")

    # 删除 NEAR_DIST 大于 500 的点
    arcpy.MakeFeatureLayer_management(output_point_shp, "point_layer")
    arcpy.SelectLayerByAttribute_management("point_layer", "NEW_SELECTION", "NEAR_DIST > 500")
    arcpy.DeleteFeatures_management("point_layer")
    arcpy.Delete_management("point_layer")

    # 打印剩余点的数量
    remaining_count = int(arcpy.GetCount_management(output_point_shp).getOutput(0))
    print(f"[INFO]  | 还剩 {remaining_count} 个点保留")

    # 如果剩余点数量大于目标点数，则随机删除多余的点
    if remaining_count > target_count:
        print(f"[INFO]  | 需要随机删除 {remaining_count - target_count} 个点，以达到目标点数 {target_count}")
        arcpy.MakeFeatureLayer_management(output_point_shp, "point_layer")
        arcpy.SelectLayerByAttribute_management("point_layer", "NEW_SELECTION", "NEAR_DIST <= 500")
        point_features = arcpy.da.SearchCursor("point_layer", ["SHAPE@"])
        point_list = [row[0] for row in point_features]
        point_features.reset()
        arcpy.Delete_management("point_layer")

        # 随机选择要删除的点
        points_to_delete = random.sample(point_list, remaining_count - target_count)

        # 使用 UpdateCursor 删除随机选择的点
        with arcpy.da.UpdateCursor(output_point_shp, ["SHAPE@"]) as cursor:
            for row in cursor:
                if row[0] in points_to_delete:
                    cursor.deleteRow()

        # 打印最终剩余点的数量
        final_count = int(arcpy.GetCount_management(output_point_shp).getOutput(0))
        print(f"[INFO]  | 最终剩余 {final_count} 个点保留")

def main():
    path_datasets = fr'E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\Analyze\consistency_check\third_dataset_poi'
    path_sids = fr"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\_dataet_SIDS_SV"

    output_folder = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\Analyze\consistency_check\neighborhood"

    list_datasets = [
        'GCL_FCS30_2010', 'GCL_FCS30_2015', 'GCL_FCS30_2020',
        'GMSSD_2015', 'GSV_2015', 'OSM_2020'
    ]
    dict_datasets = {
        "GCL_FCS30_2010": 'SIDS_SV_polyline_2010',
        "GSV_2015": 'SIDS_SV_polyline_2015',
        "GMSSD_2015": 'SIDS_SV_polyline_2015',
        "GCL_FCS30_2015": 'SIDS_SV_polyline_2015',
        "OSM_2020": 'SIDS_SV_polyline_2020',
        "GCL_FCS30_2020": 'SIDS_SV_polyline_2020',
    }
    for dataset in list_datasets:
        point_shp = os.path.join(path_datasets, fr'{dataset}.shp')
        line_shp = os.path.join(path_sids, fr'{dict_datasets.get(dataset)}.shp')
        print(f"[INFO]  | 任务启动，PID={os.getpid()}")
        try:
            calculate_near_distance(point_shp, line_shp, output_folder)
            print(f"[INFO]  | 任务完成")
        except Exception as err:
            print(f"[ERROR] | 发生错误：{err}")

if __name__ == "__main__":
    main()