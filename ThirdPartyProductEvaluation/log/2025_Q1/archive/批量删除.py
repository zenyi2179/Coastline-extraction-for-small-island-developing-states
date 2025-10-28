import arcpy

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
        for year in [2010, 2020]:
            # Execute Pairwise Clip
            in_data = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_{str(year)[-2:]}\{boun}\{boun}_BV_{str(year)[-2:]}_.shp"

            arcpy.env.overwriteOutput = True
            arcpy.Delete_management(in_data)
            print(in_data)
