import os
import sys
import arcpy
import tempfile

from worktools import get_files_by_extension

from tools.海岸线json import subpixel_extraction
from tools.海岸线polygon import geojson_to_polygon

sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # 添加项目根目录


def main():
    path_base = fr'E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\temp'  # 基础路径
    list_year = [2010, 2015, 2020]  # 年份列表
    # list_year = [2015]  # 当前只处理2010年的数据
    print(f"[INFO] 开始处理年份列表：{list_year}")

    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"[INFO] 创建临时目录：{temp_dir}")
        for year in list_year:
            print(f"[INFO] 开始处理年份：{year}")
            # path_tif = os.path.join(path_base, fr'extract_connected_patches\{year}')  # 获取tif文件路径
            path_tif = os.path.join(path_base, fr'_reference_geedata\extract_connected_patches\{year}')  # 获取tif文件路径
            print(f"[INFO] 获取路径 {path_tif} 下的 .tif 文件")
            list_tif = get_files_by_extension(
                path_tif, '.tif', return_absolute_path=True
            )
            print(f"[INFO] 找到 {len(list_tif)} 个 .tif 文件")

            for tif_gee in list_tif:
                try:
                    tif_name = os.path.split(tif_gee)[-1]  # 获取文件名
                    print(f"[INFO] 开始处理文件：{tif_gee}")

                    # 亚像素提取
                    geojson_name = tif_name.replace('.tif', '.geojson')  # 生成geojson文件名
                    path_geojson = os.path.join(temp_dir, geojson_name)  # geojson文件路径
                    print(f"[INFO] 亚像素提取，输出路径：{path_geojson}")
                    subpixel_extraction(
                        input_tif=tif_gee,
                        z_values=0,
                        subpixel_tif=path_geojson)
                    print(f"[INFO] 完成亚像素提取，输出路径：{path_geojson}")

                    # geojson转polygon
                    polygon_name = tif_name.replace('.tif', '.shp')  # 生成shp文件名
                    # path_polygon = os.path.join(path_base, fr'polygon_map\{year}', polygon_name)  # shp文件路径
                    path_polygon = os.path.join(path_base, fr'_reference_geedata\polygon_map\{year}', polygon_name)  # shp文件路径
                    os.makedirs(os.path.dirname(path_polygon), exist_ok=True)
                    print(f"[INFO] geojson转polygon，输出路径：{path_polygon}")
                    geojson_to_polygon(
                        input_geojson=path_geojson,
                        output_shp=path_polygon
                    )
                    print(f"[INFO] 完成 geojson 转 polygon，输出路径：{path_polygon}")
                    print(f"[INFO] 文件 {tif_gee} 处理完成")
                except Exception as e:
                    print('[ERROR]', e)


if __name__ == '__main__':
    print("[INFO] 程序开始运行")
    main()
    print("[INFO] 程序运行结束")