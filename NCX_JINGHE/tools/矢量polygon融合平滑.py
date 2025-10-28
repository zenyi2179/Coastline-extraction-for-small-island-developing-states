import os
import arcpy
arcpy.env.overwriteOutput = True
from worktools import read_txt_to_list


def merge_and_smooth_polygons(shapefile1, shapefile2, output_shapefile, smooth_tolerance = 60):
    """
    合并两个 Shapefile，融合多边形，并使用 PAEK 算法平滑多边形边界。

    处理流程：
    1. 合并两个 Shapefile
    2. 融合（Dissolve）合并后的多边形
    3. 使用 PAEK 算法平滑边界
    4. 保存为新的 Shapefile

    参数：
    :param shapefile1: 第一个输入 Shapefile 路径
    :param shapefile2: 第二个输入 Shapefile 路径
    :param output_shapefile: 输出的 Shapefile 路径
    :param smooth_tolerance: 平滑容差值（单位与数据坐标系一致，例如 "60 Meters"）
    """
    # 设置工作环境（可按需调整）
    os.makedirs(os.path.dirname(output_shapefile), exist_ok=True)

    # 1. 合并 Shapefile
    merged_memory = "in_memory\\merged"
    arcpy.management.Merge([shapefile1, shapefile2], merged_memory)
    print(f"[INFO] 合并完成 -> {merged_memory}")

    # 2. 融合多边形（避免多余边界线）
    dissolved_memory = "in_memory\\dissolved"
    arcpy.analysis.PairwiseDissolve(
        in_features=merged_memory,
        out_feature_class=dissolved_memory,
        multi_part='MULTI_PART'
    )
    print(f"[INFO] 融合完成 -> {dissolved_memory}")

    # 3. 平滑多边形边界
    arcpy.cartography.SmoothPolygon(
        in_features=dissolved_memory,
        out_feature_class=output_shapefile,
        algorithm="PAEK",
        tolerance=f"{smooth_tolerance} Meters"
    )
    print(f"[INFO] 平滑完成 -> {output_shapefile}")

    # Process: 计算几何属性 (计算几何属性) (management)
    arcpy.management.CalculateGeometryAttributes(
        in_features=output_shapefile,
        geometry_property=[["area_geo", "AREA_GEODESIC"], ["leng_geo", "PERIMETER_LENGTH_GEODESIC"]],
        length_unit="KILOMETERS",
        area_unit="SQUARE_KILOMETERS")


if __name__ == '__main__':

    """
    主函数，用于处理多个岛屿的多边形数据。
    """
    base_workspace = r'E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\temp'

    list_sids = read_txt_to_list('SIDS_37.txt')[19:20]  # 读取岛屿列表
    # 异常[19:20] PLW 2020
    list_years = [2010, 2015, 2020]  # 年份列表

    # 测试用
    # list_sids = ['COM', 'DOM', 'STP', 'FJI']
    list_sids = ['STP']
    list_years = [2020]

    for gid in list_sids:
        for year in list_years:
            # 输入 Shapefile 路径
            shp1_path = os.path.join(base_workspace, f'polygon_merge', gid, f"{gid}_{year}.shp")
            shp2_path = os.path.join(base_workspace, f'polygon_merge_add', gid, f"{gid}_add_{year}.shp")

            # 输出 Shapefile 路径
            output_path = os.path.join(base_workspace, f'polygon_merge_smooth', gid, f"{gid}_smooth_{year}.shp")

            # 平滑容差（单位：米）
            tolerance_meters = 60

            # 执行处理
            merge_and_smooth_polygons(
                shapefile1=shp1_path,
                shapefile2=shp2_path,
                output_shapefile=output_path,
                smooth_tolerance=tolerance_meters
            )
