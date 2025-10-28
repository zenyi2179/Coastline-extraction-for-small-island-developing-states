import os
import arcpy

if __name__ == '__main__':
    arcpy.env.overwriteOutput = True
    # 29国家
    sid_list = ["ATG",
"BHS",
"BRB",
"COM",
"CPV",
"CUB",
"DMA",
"FJI",
"FSM",
"GRD",
"JAM",
"KIR",
"KNA",
"LCA",
"MDV",
"MHL",
"MUS",
"NRU",
"PLW",
"SGP",
"SLB",
"STP",
"SYC",
"TON",
"TTO",
"TUV",
"VCT",
"VUT",
"WSM",
]
    sid_list = ['SGP']
    for sid in sid_list:
        for year in [2015]:
            # Execute Pairwise Clip
            in_features = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_{str(year)[-2:]}\{sid}\{sid}_BV_{str(year)[-2:]}.shp"
            out_feature_class = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_{str(year)[-2:]}\{sid}\{sid}_CL_{str(year)[-2:]}.shp"

            arcpy.management.PolygonToLine(in_features, out_feature_class)
            print(out_feature_class)

