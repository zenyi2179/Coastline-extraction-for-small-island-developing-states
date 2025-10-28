import os.path

import arcpy

def ShpClip(in_features, clip_features, out_feature_class):
    arcpy.env.overwriteOutput = True
    # Process: 成对裁剪 (成对裁剪) (analysis)
    arcpy.analysis.PairwiseClip(
        in_features=in_features,
        clip_features=clip_features,
        out_feature_class=out_feature_class
    )

if __name__ == '__main__':
    years = [2015]
    # 需要裁剪的 8 国
    country_codes = ["BLZ",
"DOM",
"GNB",
"GUY",
"HTI",
"PNG",
"SUR",
"TLS",
                     ]
    # country_codes = ['BLZ']

    for year in years:
        for country_code in country_codes:
            # Set local variables
            in_features = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\f_SIDS_Optimize\{country_code}\{country_code}_{str(year)[-2:]}.shp"
            clip_features = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\boundary\boun_mask\v2\{country_code}.shp"

            fold_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_{str(year)[-2:]}\{country_code}"
            os.makedirs(fold_path, exist_ok=True)
            out_feature_class = os.path.join(fold_path, fr"{country_code}_BV_{str(year)[-2:]}.shp")

            # Execute Pairwise Clip
            arcpy.env.overwriteOutput = True
            arcpy.analysis.PairwiseClip(in_features, clip_features, out_feature_class)
            print(out_feature_class)
