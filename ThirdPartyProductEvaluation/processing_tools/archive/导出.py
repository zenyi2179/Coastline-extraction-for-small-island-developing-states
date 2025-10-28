import arcpy

if __name__ == '__main__':
    # Execute Pairwise Clip
    in_features = "C:/output/Output.gdb/in"
    out_features = "C:/output/Output.gdb/allroads"

    arcpy.conversion.ExportFeatures(in_features, out_features)