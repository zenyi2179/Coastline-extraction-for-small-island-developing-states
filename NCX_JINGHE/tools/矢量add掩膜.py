import arcpy
import os
import time
import math
from datetime import timedelta
from worktools import read_txt_to_list


# ----------------------------------------------------
# 按 5° 经度带宽切分（避免内存多边形直接 Clip）
# ----------------------------------------------------
def split_polygon_by_lon5(input_fc, temp_gdb):
    """
    将输入的多边形要素类按 5° 经度带宽切分，以避免直接裁剪时内存不足的问题。

    参数:
    input_fc (str): 输入的多边形要素类路径
    temp_gdb (str): 临时地理数据库路径

    返回:
    list: 切分后的多边形要素类列表
    """
    split_fc_list = []
    sr = arcpy.Describe(input_fc).spatialReference  # 获取输入要素类的空间参考
    ext = arcpy.Describe(input_fc).extent  # 获取输入要素类的范围
    band_width = 5  # 设置经度带宽为 5°
    lon_min = math.floor(ext.XMin / band_width) * band_width  # 计算最小经度
    lon_max = math.ceil(ext.XMax / band_width) * band_width  # 计算最大经度
    bands = list(range(int(lon_min), int(lon_max), band_width))  # 生成经度带

    for i, left in enumerate(bands):
        right = left + band_width  # 计算右侧经度

        # 创建临时裁剪面
        clip_poly_fc = os.path.join(temp_gdb, f"clip_poly_{i}")
        if arcpy.Exists(clip_poly_fc):
            arcpy.management.Delete(clip_poly_fc)  # 如果已存在，删除旧的临时裁剪面

        arcpy.management.CreateFeatureclass(
            out_path=temp_gdb,
            out_name=f"clip_poly_{i}",
            geometry_type="POLYGON",
            spatial_reference=sr
        )  # 创建新的临时裁剪面

        # 插入矩形几何
        with arcpy.da.InsertCursor(clip_poly_fc, ["SHAPE@"]) as cursor:
            array = arcpy.Array([
                arcpy.Point(left, -90),
                arcpy.Point(right, -90),
                arcpy.Point(right, 90),
                arcpy.Point(left, 90),
                arcpy.Point(left, -90)
            ])
            polygon = arcpy.Polygon(array, sr)
            cursor.insertRow([polygon])  # 插入矩形几何

        # 执行裁剪
        out_clip = os.path.join(temp_gdb, f"clip_{i}")
        if arcpy.Exists(out_clip):
            arcpy.management.Delete(out_clip)  # 如果已存在，删除旧的裁剪结果

        try:
            arcpy.analysis.Clip(input_fc, clip_poly_fc, out_clip)  # 执行裁剪操作
            if int(arcpy.GetCount_management(out_clip)[0]) > 0:
                split_fc_list.append(out_clip)  # 如果裁剪结果中有要素，添加到列表中
        except arcpy.ExecuteError as e:
            print(f"[WARN] 段 {i} Clip 失败: {e}")
            continue

    return split_fc_list


# ----------------------------------------------------
# 处理并简化面（保留方块化）
# ----------------------------------------------------
def process_and_simplify_polygon(input_feature_class, output_feature_class):
    """
    处理并简化多边形要素类，保留方块化效果。

    参数:
    input_feature_class (str): 输入的多边形要素类路径
    output_feature_class (str): 输出的多边形要素类路径
    """
    arcpy.env.overwriteOutput = True  # 允许覆盖输出
    sr = arcpy.Describe(input_feature_class).spatialReference  # 获取输入要素类的空间参考
    scratch = arcpy.env.scratchGDB  # 获取临时地理数据库路径

    split_list = split_polygon_by_lon5(input_feature_class, scratch)  # 按 5° 经度带宽切分多边形
    if not split_list:
        print("[WARN] 无有效要素，跳过")
        return

    first_written = False  # 标记是否已写入第一个分段

    for idx, seg_fc in enumerate(split_list):
        if int(arcpy.GetCount_management(seg_fc)[0]) == 0:
            continue  # 如果分段中无要素，跳过
        if not arcpy.Describe(seg_fc).spatialReference:
            arcpy.DefineProjection_management(seg_fc, sr)  # 定义分段的空间参考

        try:
            buf = arcpy.analysis.PairwiseBuffer(
                in_features=seg_fc,
                buffer_distance_or_field="-20 Meters",
                method="GEODESIC")[0]  # 执行缓冲操作

            ras = arcpy.conversion.PolygonToRaster(
                in_features=buf,
                value_field="ORIG_FID",
                out_rasterdataset=arcpy.CreateUniqueName("ras", scratch),
                cellsize="0.00015",
                build_rat="DO_NOT_BUILD")[0]  # 将多边形转换为栅格

            poly = arcpy.conversion.RasterToPolygon(
                in_raster=ras,
                out_polygon_features=arcpy.CreateUniqueName("poly", scratch),
                simplify="NO_SIMPLIFY")[0]  # 将栅格转换为多边形

            simp = arcpy.cartography.SimplifyPolygon(
                in_features=poly,
                out_feature_class=arcpy.CreateUniqueName("simp", scratch),
                algorithm="BEND_SIMPLIFY",
                tolerance="60 Meters")[0]  # 简化多边形

            arcpy.management.AddField(simp, "area_geo", "DOUBLE")  # 添加面积字段
            arcpy.management.CalculateGeometryAttributes(
                in_features=simp,
                geometry_property=[["area_geo", "AREA_GEODESIC"]],
                area_unit="SQUARE_KILOMETERS")  # 计算面积

            with arcpy.da.UpdateCursor(simp, ["area_geo"]) as cursor:
                for row in cursor:
                    if row[0] <= 0.0036:
                        cursor.deleteRow()  # 删除面积小于 0.0036 平方公里的要素

            # 合并输出
            if not first_written:
                arcpy.management.CopyFeatures(simp, output_feature_class)  # 复制第一个分段到输出
                first_written = True
            else:
                arcpy.management.Append(simp, output_feature_class, schema_type="NO_TEST")  # 追加后续分段

        except arcpy.ExecuteError as e:
            if "000918" in str(e):
                print(f"[WARN] 段 {idx} 无法生成栅格，跳过（可能无有效几何）")
            else:
                raise

    if not first_written:
        print(f"[WARN] {input_feature_class} 所有分段均无有效输出，未生成 {output_feature_class}")


# ----------------------------------------------------
# 主函数
# ----------------------------------------------------
def main():
    """
    主函数，用于处理多个岛屿的多边形数据。
    """
    base_polygon = r'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation'
    base_workspace = r'E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\temp\polygon_merge_add'

    list_sids = read_txt_to_list('SIDS_37.txt')  # 读取岛屿列表
    list_years = [2010, 2015, 2020]  # 年份列表

    # 测试用
    # list_sids = ['FJI']
    # list_years = list_years[0:1]

    for gid in list_sids:
        start_time = time.time()
        for year in list_years:
            shp_old_polygon = os.path.join(base_polygon, fr'SIDS_CL_{str(year)[-2:]}', gid, f"_{gid}_merge_BV.shp")
            shp_add_mask = os.path.join(base_workspace, gid, f"{gid}_add_{year}.shp")

            if arcpy.Exists(shp_add_mask):
                print(f"[SKIP] {shp_add_mask} 已存在，跳过。")
                continue

            os.makedirs(os.path.dirname(shp_add_mask), exist_ok=True)
            try:
                process_and_simplify_polygon(
                    input_feature_class=shp_old_polygon,
                    output_feature_class=shp_add_mask)
                print(f"[INFO] {shp_add_mask} 处理完成")
            except Exception as e:
                print(f"[ERROR] {shp_add_mask} 处理失败: {e}")

        elapsed = timedelta(seconds=time.time() - start_time)
        hours, remainder = divmod(elapsed.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        print(f"[TIME] {gid} 完成，耗时 {hours:02d}h{minutes:02d}min{seconds:02d}s")


if __name__ == '__main__':
    main()
