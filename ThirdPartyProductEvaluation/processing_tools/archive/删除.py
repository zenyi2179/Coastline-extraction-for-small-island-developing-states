import arcpy

if __name__ == '__main__':
    # Execute Pairwise Clip
    in_data = "majorrds.shp"

    arcpy.env.overwriteOutput = True
    arcpy.Delete_management(in_data)
