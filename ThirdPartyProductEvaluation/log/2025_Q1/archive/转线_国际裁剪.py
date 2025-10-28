import arcpy

if __name__ == '__main__':
    # Execute Pairwise Clip
    arcpy.env.overwriteOutput = True
    # 8 国家 异常 KIR
    boun_list = [
"BLZ",
"DOM",
"GNB",
"GUY",
"HTI",
"PNG",
"SUR",
"TLS",

]
    for boun in boun_list:
        for year in [2015]:
            in_features = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_{str(year)[-2:]}\{boun}\{boun}_BV_{str(year)[-2:]}.shp"

            temp_features = fr"in_memory\line"

            arcpy.env.overwriteOutput = True
            arcpy.management.PolygonToLine(in_features, temp_features)

            out_features = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_{str(year)[-2:]}\{boun}\{boun}_CL_{str(year)[-2:]}.shp"
            boundary_GID = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\boundary\boun_mask\{boun}_v3.shp"
            arcpy.analysis.Clip(in_features=temp_features, clip_features=boundary_GID, out_feature_class=out_features)
            print(out_features)