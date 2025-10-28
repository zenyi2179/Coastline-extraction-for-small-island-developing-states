import os
import arcpy

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
    print(fr"SmoothPolygon save as: {out_fea}")

# def SmoothLine(in_fea, out_fea):  # _draft
#     arcpy.env.overwriteOutput = True
#
#     ABW_00 = "ABW_00"
#     arcpy.cartography.SmoothLine(
#         in_features=in_fea, out_feature_class=out_fea,
#         algorithm="PAEK", tolerance="90 Meters",
#         endpoint_option="FIXED_CLOSED_ENDPOINT",
#         error_option="NO_CHECK", in_barriers=[])

def main():
    # 全 37 国家
    sids_cou_list = ["ATG",
"BHS",
"BLZ",
"BRB",
"COM",
"CPV",

"DMA",
"DOM",


"GNB",
"GRD",
"GUY",
"HTI",
"JAM",

"KNA",
"LCA",
"MDV",


"NRU",
"PLW",

"SGP",

"STP",
"SUR",

"TLS",
"TON",
"TTO",
"TUV",
"VCT",
"VUT",
"WSM",

                     ]
    for sids_cou in sids_cou_list:
        for year in [2015]:
            # 要素初始化
            in_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\j_SIDS_Polygon\{sids_cou}\{sids_cou}_{str(year)[-2:]}.shp"
            out_smoo_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\k_SIDS_Smooth\{sids_cou}\{sids_cou}_{str(year)[-2:]}.shp"

            # 新建文件夹
            output_folder = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\k_SIDS_Smooth\{sids_cou}"
            os.makedirs(output_folder, exist_ok=True)
            SmoothPolygon(in_fea=in_shp, out_fea=out_smoo_shp)


if __name__ == '__main__':
    main()
