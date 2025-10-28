import arcpy

if __name__ == '__main__':
    # Execute Pairwise Clip
    inputs_list = ["majorrds.shp", "Habitat_Analysis.gdb/futrds"]
    output = "C:/output/Output.gdb/allroads"

    arcpy.env.overwriteOutput = True
    arcpy.management.Merge(
        inputs=inputs_list,
        output=output)
