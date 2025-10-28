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
    # Set local variables
    in_features = "majorrds.shp"
    clip_features = "study_quads.shp"
    out_feature_class = "C:/output/studyarea.shp"

    # Execute Pairwise Clip
    arcpy.env.overwriteOutput = True
    arcpy.analysis.PairwiseClip(in_features, clip_features, out_feature_class)
