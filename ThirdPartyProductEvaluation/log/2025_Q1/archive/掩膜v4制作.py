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
    boun_list = ["BLZ",
                         "DOM",
                         "GNB",
                         "GUY",
                         "HTI",
                         "PNG",
                         "SUR",
                         "TLS",
                         ]
    # Set local variables
    for boun in boun_list:
        in_features = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\boundary\boun_mask\v2\{boun}.shp"
        clip_features = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\boundary\boun_mask\{boun}_v3.shp"
        out_feature_class = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\boundary\boun_mask\v4\{boun}_v4.shp"

        # Execute Pairwise Clip
        arcpy.env.overwriteOutput = True
        arcpy.analysis.PairwiseErase(in_features, clip_features, out_feature_class)
        print(out_feature_class)
