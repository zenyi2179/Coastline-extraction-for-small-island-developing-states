import os
import arcpy


def create_sample_points(StP_GID, S_CL, SP_GID):
    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    # Process: 复制要素 (复制要素) (management)
    StP_Copy_shp = fr"in_memory\StP_Copy"
    arcpy.management.CopyFeatures(in_features=StP_GID, out_feature_class=StP_Copy_shp)

    # Process: 邻近分析 (邻近分析) (analysis)
    Stp_Near = arcpy.analysis.Near(in_features=StP_Copy_shp, near_features=[S_CL], search_radius="500 Meters",
                                   location="LOCATION", method="GEODESIC",
                                   field_names=[["NEAR_FID", "NEAR_FID"], ["NEAR_DIST", "NEAR_DIST"],
                                                ["NEAR_X", "NEAR_X"], ["NEAR_Y", "NEAR_Y"]])[0]

    # Process: XY 表转点 (XY 表转点) (management)
    arcpy.management.XYTableToPoint(in_table=Stp_Near, out_feature_class=SP_GID,
                                    x_field="NEAR_X", y_field="NEAR_Y")
    print(SP_GID, 'finish')


if __name__ == '__main__':
    # 全局环境设置
    year_list = [2010, 2015, 2020]
    sids_cou_list = ["ATG",
                     "BHS",
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
    for sid in sids_cou_list:
        for year in year_list:
            work_folder = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\{sid}\{year}"
            standard_points = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\\" \
                              fr"{sid}\{year}\StP_{sid}_{str(year)[-2:]}.shp"
            # 初始化第三方文件夹
            third_path_output = os.path.join(work_folder, fr"ThirdPartyDataSource")
            # 确定是否存在文件夹
            os.makedirs(os.path.join(third_path_output), exist_ok=True)
            # SIDS_BV :
            sample_lines = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\\" \
                           fr"SIDS_CL_{str(year)[-2:]}\{sid}\{sid}_CL_{str(year)[-2:]}.shp"
            sample_points = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\\" \
                            fr"{sid}\{year}\SP_{sid}_{str(year)[-2:]}.shp"
            # OSM :
            # sample_lines = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\\" \
            #                fr"OSM\{sid}\_{sid}_merge.shp"
            # sample_points = os.path.join(third_path_output, fr"OSM_SP_{sid}_{str(year)[-2:]}.shp")
            # # GCL_FCS30 :
            # sample_lines = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\\" \
            #                fr"GCL_FCS30_{str(year)[-2:]}\{sid}\_{sid}_merge.shp"
            # sample_points = os.path.join(third_path_output, fr"GCL_SP_{sid}_{str(year)[-2:]}.shp")
            # # GSV :
            # sample_lines = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\\" \
            #                fr"GSV\{sid}\_{sid}_merge.shp"
            # sample_points = os.path.join(third_path_output, fr"GSV_SP_{sid}_{str(year)[-2:]}.shp")
            # GMSSD_2015 :
            # sample_lines = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\\" \
            #                fr"GMSSD_2015\{sid}\_{sid}_merge.shp"
            # sample_points = os.path.join(third_path_output, fr"GMSSD_SP_{sid}_{str(year)[-2:]}.shp")

            create_sample_points(standard_points, sample_lines, sample_points)
