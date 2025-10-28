import os
import sys

from worktools import get_files_by_extension

sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # 添加项目根目录

from tools.影像噪声过滤 import apply_filter_to_raster
from tools.影像otsu分类 import otsu_threshold_with_gdal
from tools.剔除小型斑块 import apply_cluster_filter
from tools.影像孔隙填补 import fill_internal_holes


def main():
    path_base = fr'E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV'
    list_year = [2010, 2015, 2020]
    list_year = [2010]  # 当前只处理2010年的数据
    print(f"[INFO] 开始处理年份列表：{list_year}")

    for year in list_year:
        path_tif_gee = fr'E:\_GoogleDrive\SIDs_Grid_{year}'
        print(f"[INFO] 获取路径 {path_tif_gee} 下的 .tif 文件")
        list_tif = get_files_by_extension(
            path_tif_gee, '.tif', return_absolute_path=True
        )
        print(f"[INFO] 找到 {len(list_tif)} 个 .tif 文件")

        for tif_path in list_tif:
            tif_name = os.path.split(tif_path)[-1]
            print(f"[INFO] 开始处理文件：{tif_path}")

            # 应用影像噪声过滤
            path_filter = os.path.join(path_base, 'temp', 'apply_filter_to_raster')
            tif_filter = os.path.join(path_filter, 'tif_filter.tif')
            apply_filter_to_raster(input_path=tif_path,
                                   output_path=tif_filter,
                                   window_size=31,
                                   max_threshold=20)
            print(f"[INFO] 完成影像噪声过滤，输出路径：{tif_filter}")

            # 应用 Otsu 分类
            path_otsu = os.path.join(path_base, 'temp', 'otsu_threshold_with_gdal')
            tif_otsu = os.path.join(path_otsu, 'tif_otsu.tif')
            otsu_threshold_with_gdal(input_tif_path=tif_filter,
                                     output_tif_path=tif_otsu)
            print(f"[INFO] 完成 Otsu 分类，输出路径：{tif_otsu}")

            # 剔除小型斑块
            path_cluster = os.path.join(path_base, 'temp', 'apply_cluster_filter')
            tif_cluster = os.path.join(path_cluster, 'tif_cluster.tif')
            apply_cluster_filter(input_path=tif_otsu,
                                 output_path=tif_cluster,
                                 min_cluster_size=4)
            print(f"[INFO] 完成剔除小型斑块，输出路径：{tif_cluster}")

            # 影像孔隙填补
            path_holes = os.path.join(path_base, 'temp', 'fill_internal_holes')
            tif_holes = os.path.join(path_holes, tif_name)
            fill_internal_holes(input_tif=tif_cluster,
                                output_tif=tif_holes)
            print(f"[INFO] 完成影像孔隙填补，输出路径：{tif_holes}")

            print(f"[INFO] 文件 {tif_path} 处理完成")


if __name__ == '__main__':
    print("[INFO] 程序开始运行")
    main()
    print("[INFO] 程序运行结束")