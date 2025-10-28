# -*- coding: utf-8 -*-
import os
import glob
import time
import arcpy


def merge_shapefiles_by_year(root_folder: str, output_dir: str, year: str, geometry_type: str) -> None:
    """
    按年份和几何类型合并所有 *_<geometry_type>_<year>.shp，并添加字段 gid。

    :param root_folder: 根目录，包含国家代码子文件夹
    :param output_dir:  输出目录
    :param year:        四位年份字符串，例如 '2010'
    :param geometry_type: 几何类型，例如 'polygon' 或 'polyline'
    """
    start_time = time.time()
    print(f"[INFO]  | 任务启动，PID={os.getpid()}")

    # 1. 构造搜索模式：递归查找 *_<geometry_type>_<year>.shp
    search_pattern = os.path.join(root_folder, "**", f"*_{geometry_type}_{year}.shp")
    shapefile_list = glob.glob(search_pattern, recursive=True)
    if not shapefile_list:
        print(f"[ERROR] | 未找到任何 *_{geometry_type}_{year}.shp 文件")
        return

    print(f"[INFO]  | 共发现 {len(shapefile_list)} 个 shapefile")

    # 2. 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    output_name = f"SIDS_SV_{geometry_type}_{year}.shp"
    output_path = os.path.join(output_dir, output_name)

    # 如果输出文件已存在则先删除
    if arcpy.Exists(output_path):
        arcpy.Delete_management(output_path)

    temp_files = []

    # 3. 遍历 shapefile，逐个添加字段 gid 并赋值
    for file_path in shapefile_list:
        country_code = os.path.basename(os.path.dirname(file_path))  # 父文件夹名

        # 复制一份临时文件避免覆盖原始数据
        temp_fc = os.path.join(output_dir, f"temp_{country_code}_{os.path.basename(file_path)}")
        arcpy.Copy_management(file_path, temp_fc)

        # 如果没有 gid 字段则添加
        field_names = [f.name for f in arcpy.ListFields(temp_fc)]
        if "gid" not in field_names:
            arcpy.AddField_management(temp_fc, "gid", "TEXT", field_length=50)

        # 更新 gid 字段值
        with arcpy.da.UpdateCursor(temp_fc, ["gid"]) as cursor:
            for row in cursor:
                row[0] = country_code
                cursor.updateRow(row)

        temp_files.append(temp_fc)

    # 4. 合并
    arcpy.Merge_management(temp_files, output_path)

    # 5. 清理临时文件
    for temp_fc in temp_files:
        if arcpy.Exists(temp_fc):
            arcpy.Delete_management(temp_fc)

    elapsed = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - start_time))
    print(f"[INFO]  | 合并完成，输出：{output_path}")
    print(f"[TIME]  | 总耗时:{elapsed}")


def main():
    """主函数"""
    ROOT_DIR = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1"
    OUT_DIR = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\_dataet_SIDS_SV"
    for year in [2010, 2015, 2020]:
        for geometry_type in ["polygon", "polyline"]:
            merge_shapefiles_by_year(ROOT_DIR, OUT_DIR, str(year), geometry_type)


if __name__ == '__main__':
    main()