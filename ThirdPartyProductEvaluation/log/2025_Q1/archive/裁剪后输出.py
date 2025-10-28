import arcpy

# 待裁剪的 9 国家
boundary_clip_list = [
    "BLZ",
"DOM",
"GNB",
"GUY",
"HTI",
"PNG",
"SUR",
"TLS",

]
# boundary_clip_list = ['DOM']
year_list = [2015]
for sids in boundary_clip_list:
    for year in year_list:
        # Execute Pairwise Clip
        arcpy.env.overwriteOutput = True
        arcpy.analysis.PairwiseClip(
            in_features=fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\k_SIDS_Smooth\{sids}\{sids}_{str(year)[-2:]}.shp",
            clip_features=fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\boundary\boun_mask\v2\{sids}.shp",
            out_feature_class=fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_{str(year)[-2:]}\{sids}\{sids}_BV_{str(year)[-2:]}.shp",
        )
        print(fr'SIDS_CL_{str(year)[-2:]}\{sids}\{sids}_BV_{str(year)[-2:]}.shp')

