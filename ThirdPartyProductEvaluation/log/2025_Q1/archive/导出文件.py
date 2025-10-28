import os

import arcpy

if __name__ == '__main__':
    # Execute Pairwise Clip
    arcpy.env.overwriteOutput = True
    # 29 国家
    boun_list = ["ATG",
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
    for boun in boun_list:
        for year in [2015]:
            in_features = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\k_SIDS_Smooth\{boun}\{boun}_{str(year)[-2:]}.shp"
            folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_{str(year)[-2:]}\{boun}"
            os.makedirs(folder_path, exist_ok=True)
            out_features = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_{str(year)[-2:]}\{boun}\{boun}_BV_{str(year)[-2:]}.shp"

            arcpy.conversion.ExportFeatures(in_features, out_features)
            print(out_features)