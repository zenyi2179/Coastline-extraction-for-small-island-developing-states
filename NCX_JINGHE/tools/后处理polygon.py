import arcpy
import os
import time
from worktools import read_txt_to_list

# 允许覆盖已有输出
arcpy.env.overwriteOutput = True


def process_shapefiles(input_shapefile_1, input_shapefile_2, clip_shapefile, output_shapefile):
    """
    合并、融合并裁剪 shapefile 文件，计算面积和周长。

    :param input_shapefile_1: 第一个输入 shapefile 文件路径
    :param input_shapefile_2: 第二个输入 shapefile 文件路径
    :param clip_shapefile: 用于裁剪的 shapefile 文件路径
    :param output_shapefile: 最终输出的 shapefile 文件路径
    """
    start_time = time.time()
    print(f"[INFO]  | 任务启动，PID={os.getpid()}")

    # 检查输入文件是否存在
    for file_path in [input_shapefile_1, input_shapefile_2, clip_shapefile]:
        if not arcpy.Exists(file_path):
            print(f"[ERROR] | 文件不存在：{file_path}")
            return

    # 合并输入文件
    merged_shapefile = r"in_memory\merged"
    arcpy.Merge_management([input_shapefile_1, input_shapefile_2], merged_shapefile)
    print(f"[INFO]  | 合并完成：{input_shapefile_1} 和 {input_shapefile_2} -> {merged_shapefile}")

    # 融合合并结果
    dissolved_shapefile = r"in_memory\dissolved"
    arcpy.Dissolve_management(merged_shapefile, dissolved_shapefile)
    print(f"[INFO]  | 融合完成：{merged_shapefile} -> {dissolved_shapefile}")

    # 裁剪融合结果
    arcpy.Clip_analysis(dissolved_shapefile, clip_shapefile, output_shapefile)
    print(f"[INFO]  | 裁剪完成：{dissolved_shapefile} 被 {clip_shapefile} 裁剪为 {output_shapefile}")

    # 计算几何属性
    arcpy.management.CalculateGeometryAttributes(
        in_features=output_shapefile,
        geometry_property=[
            ["area_geo", "AREA_GEODESIC"],
            ["leng_geo", "PERIMETER_LENGTH_GEODESIC"]
        ],
        length_unit="KILOMETERS",
        area_unit="SQUARE_KILOMETERS"
    )
    print(f"[INFO]  | 几何属性计算完成")

    # 统计运行时间
    elapsed_time = time.time() - start_time
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"[TIME]  | 总耗时: {int(hours):02d}h{int(minutes):02d}m{int(seconds):02d}s")


def main():
    """
    主函数：批量处理多个岛屿的多边形数据，执行合并、融合、裁剪和属性计算。
    """
    base_workspace = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1"
    base_mask = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\boundary\boun_mask"

    list_sids = read_txt_to_list("SIDS_Clip_9.txt")
    list_years = [2010, 2015, 2020]

    # 测试用
    list_sids = ['DOM']
    list_years = [2010]

    for island_code in list_sids:
        for year in list_years:
            input_shapefile_1 = os.path.join(base_workspace, f"{island_code}\\{island_code}_polygon_{year}.shp")
            input_shapefile_2 = os.path.join(base_mask, f"v4\\{island_code}_v4.shp")
            clip_shapefile = os.path.join(base_mask, f"v2\\{island_code}.shp")
            output_shapefile = os.path.join(base_workspace, f"{island_code}\\{island_code}_polygon_{year}_processed_.shp")

            process_shapefiles(input_shapefile_1, input_shapefile_2, clip_shapefile, output_shapefile)


if __name__ == '__main__':
    main()
