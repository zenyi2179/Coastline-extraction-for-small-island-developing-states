import os
import sys
import tempfile

from worktools import get_files_by_extension

sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # 添加项目根目录

from tools.影像噪声过滤 import apply_filter_to_raster
from tools.影像阈值分类 import threshold_with_gdal
from tools.剔除小型斑块 import apply_cluster_filter
from tools.影像孔隙填补 import fill_internal_holes


def main():
    path_base = fr'E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV'
    list_year = [2010, 2015, 2020]
    # list_year = [2020]  # 当前只处理2010年的数据
    print(f"[INFO] 开始处理年份列表：{list_year}")

    for year in list_year:
        # path_tif_gee = fr'E:\_GoogleDrive\SIDs_Grid_{year}'
        path_tif_gee = os.path.join(path_base, fr'GEE_4_10_neg_mndwi', fr'SIDs_Grid_{year}')
        # path_tif_gee = os.path.join(path_base, fr'GEE_1_12_neg_mndwi', fr'SIDs_Grid_{year}')
        print(f"[INFO] 获取路径 {path_tif_gee} 下的 .tif 文件")
        list_tif = get_files_by_extension(
            path_tif_gee, '.tif', return_absolute_path=True
        )
        print(f"[INFO] 找到 {len(list_tif)} 个 .tif 文件")

        for tif_path in list_tif:
            tif_name = os.path.split(tif_path)[-1]
            print(f"[INFO] 开始处理文件：{tif_path}")

            with tempfile.TemporaryDirectory() as temp_dir:
                # 应用影像噪声过滤
                max_threshold = {2010: 15, 2015: 15, 2020: 20}.get(year)
                tif_filter = os.path.join(temp_dir, 'tif_filter.tif')
                apply_filter_to_raster(input_path=tif_path,
                                       output_path=tif_filter,
                                       window_size=41,
                                       max_threshold=max_threshold)
                print(f"[INFO] 完成影像噪声过滤，输出路径：{tif_filter}")

                # 应用 阈值 分类
                threshold = {2010: 1, 2015: 5, 2020: 8}.get(year)
                tif_threshold = os.path.join(temp_dir, 'tif_threshold.tif')
                threshold_with_gdal(input_tif_path=tif_filter,
                                    output_tif_path=tif_threshold,
                                    threshold=threshold)
                print(f"[INFO] 完成阈值 {threshold} 分类，输出路径：{tif_threshold}")

                # 剔除小型斑块
                tif_cluster = os.path.join(temp_dir, 'fill_internal_holes')
                apply_cluster_filter(input_path=tif_threshold,
                                     output_path=tif_cluster,
                                     min_cluster_size=4)
                print(f"[INFO] 完成剔除小型斑块，输出路径：{tif_cluster}")

                # 影像孔隙填补
                tif_holes = os.path.join(path_base, fr'temp\apply_cluster_filter\{year}', tif_name)
                # tif_holes = os.path.join(path_base, fr'temp\_reference_geedata\apply_cluster_filter\{year}', tif_name)
                os.makedirs(os.path.dirname(tif_holes), exist_ok=True)
                fill_internal_holes(input_tif=tif_cluster,
                                    output_tif=tif_holes)
                print(f"[INFO] 完成影像孔隙填补，输出路径：{tif_holes}")

                print(f"[INFO] 文件 {tif_path} 处理完成")


if __name__ == '__main__':
    print("[INFO] 程序开始运行")
    main()
    print("[INFO] 程序运行结束")
