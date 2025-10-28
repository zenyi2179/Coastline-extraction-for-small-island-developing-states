import os
import arcpy

if __name__ == '__main__':
    arcpy.env.overwriteOutput = True
    sid_list = ["ATG",
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
]   # 37 国家
    sid_list = ['ATG']
    for sid in sid_list:
        for year in [2015]:
            # Execute Pairwise Clip
            in_features = fr"E:\_OrderingProject\F_IslandsBoundaryChange\g_QGIS\a_SIDS_Shp_Merge\{sid}\{sid}_{str(year)[-2:]}.shp"
            out_feature_class = fr"E:\_OrderingProject\F_IslandsBoundaryChange\g_QGIS\b_SIDS_Shp_Disslove\{sid}\{sid}_{str(year)[-2:]}.shp"

            arcpy.analysis.PairwiseDissolve(in_features, out_feature_class)
            print(out_feature_class)

