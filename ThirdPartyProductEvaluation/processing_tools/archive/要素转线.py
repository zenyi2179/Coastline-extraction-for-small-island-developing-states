import arcpy

if __name__ == '__main__':
    # Execute Pairwise Clip
    in_features = fr"C:\Users\23042\Desktop\test\1.shp"
    out_feature_class = fr"C:\Users\23042\Desktop\test\1_dissolved.shp",

    arcpy.env.overwriteOutput = True
    arcpy.management.FeatureToLine(in_features, out_feature_class)