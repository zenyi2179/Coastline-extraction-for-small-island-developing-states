import os
import time
import arcpy
from _tools import read_dbf_to_list
from _tools import list_files_with_extension
from _tools import downscaling_by_interpolation
from _tools import filter_valid_pixel_to_shp
from _tools import split_multipolygons
from _tools import format_time
import subpixel_extraction
import geojson_to_polygon

def SmoothPolygon(in_fea, out_fea):
    arcpy.env.overwriteOutput = True
    # 步骤 5：对融合后的面进行平滑处理（使用 SmoothPolygon 工具）
    arcpy.cartography.SmoothPolygon(
        in_features=in_fea,
        out_feature_class=out_fea,  # 输出平滑处理后的图层
        algorithm="PAEK",  # 使用 PAEK 算法进行平滑
        tolerance="90 Meters",  # 平滑的容忍度为 50 米
        endpoint_option="FIXED_ENDPOINT",  # 固定端点
        error_option="NO_CHECK"  # 不检查错误
    )
    print(out_fea)

def main():
    # 记录脚本开始执行的时间
    start_time = time.time()
    # 异常 BHS
    # 初始化任务配置参数
    # for year in [2000, 2010, 2020]:
    for year in [2010]:
        # sids_cou_list = ['ABW', 'CUW', 'PRI', 'MDV', 'CPV']
        sids_cou_list = ["BMU",
                     "KNA",
                     "MSR",
                     "NRU",
                     "BRB",
                     "DMA",
                     "GUM",
                     "NIU",
                     "SGP",
                     "VCT",
                     "AIA",
                     "CYM",
                     "VGB",
                     "VIR",
                     "ABW",
                     "ASM",
                     "CUW",
                     "GRD",
                     "LCA",
                     "MTQ",
                     "SXM",
                     "ATG",
                     "GLP",
                     "STP",
                     "TCA",
                     "COM",
                     "WSM",
                     "TTO",
                     "MUS",
                     "TUV",
                     "PLW",
                     "MNP",
                     "JAM",
                     "PRI",
                     "CPV",
                     "TLS",
                     "TON",
                     "COK",
                     "BLZ",
                     "GNB",
                     "SYC",
                     "HTI",
                     "DOM",
                     "VUT",
                     "MDV",
                     "NCL",
                     "KIR",
                     "MHL",
                     "FSM",
                     "FJI",
                     "SUR",
                     "SLB",
                     "BHS",
                     "CUB",
                     "GUY",
                     "PYF",
                     "PNG",
                     ]
        sids_cou_list = ["ATG",
"BLZ",
"BRB",
"COM",
"CPV",
"CUB",
"DMA",
"DOM",
"FJI",
"FSM",
"GNB",
"GRD",
"GUY",
"HTI",
"JAM",
"KIR",
"KNA",
"LCA",
"MDV",
"MHL",
"MUS",
"NRU",
"PLW",
"PNG",
"SGP",
"SLB",
"STP",
"SUR",
"SYC",
"TLS",
"TON",
"TTO",
"TUV",
"VCT",
"VUT",
"WSM",
]
        sids_cou_list = ['MDV']

        for sids_cou in sids_cou_list:
            year_crop = year  # 设置处理年份

            # 设置路径，存放国家数据
            in_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\g_QGIS\c_SIDS_no_holes\{sids_cou}\{sids_cou}_{str(year_crop)[-2:]}.shp"
            # 步骤 1：构建副图幅（进行地图裁剪和子像素提取等操作）
            output_folder = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\f_SIDS_Optimize\{sids_cou}"
            os.makedirs(output_folder, exist_ok=True)
            out_smoo_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\f_SIDS_Optimize\{sids_cou}\{sids_cou}_{str(year_crop)[-2:]}.shp"
            SmoothPolygon(in_fea=in_shp, out_fea=out_smoo_shp)
            # 步骤 2：列出指定文件夹中的所有国家图幅文件（.shp）

        # 记录脚本结束执行的时间，并计算执行时长
        end_time = time.time()
        formatted_time = format_time(end_time - start_time)
        print(f"Task completed in: {formatted_time}")


if __name__ == '__main__':
    main()
