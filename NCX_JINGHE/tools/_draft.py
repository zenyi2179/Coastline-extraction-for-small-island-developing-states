import arcpy
import os
from glob import glob

"""
  将多个岛屿的 polyline shapefile 合并为一个总的 shapefile。

  参数:
      base_dir (str): 各岛屿 polyline 文件所在的根目录。
      year (int): 要合并的年份。
      output_shp (str): 合并后输出的 shapefile 路径。
"""

def merge_island_polylines(base_dir: str, year: int, output_shp: str):
    arcpy.env.overwriteOutput = True

    # 1. 搜索所有子文件夹中的对应年份 shapefile
    search_pattern = os.path.join(base_dir, "*", f"*polyline_{year}.shp")
    input_shps = glob(search_pattern)

    if not input_shps:
        print(f"[WARN] 未找到匹配的 shapefile: {search_pattern}")
        return

    print(f"[INFO] 找到 {len(input_shps)} 个文件，开始合并...")
    for shp in input_shps:
        print("  -", shp)

    # 2. 合并
    arcpy.management.Merge(input_shps, output_shp)
    print("[INFO] 合并完成:", output_shp)


if __name__ == '__main__':
    base_dir = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_Polyline_v1"
    year = 2020
    output_shp = os.path.join(base_dir, f"SIDS_SV_Polyline_{year}.shp")

    merge_island_polylines(base_dir, year, output_shp)
