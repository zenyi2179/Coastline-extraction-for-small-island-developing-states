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
    # boun_list = ["BLZ"]
    # Set local variables
    for boun in boun_list:
        for year in [2010, 2020]:
            # Execute Pairwise Clip
            input_sids = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_{str(year)[-2:]}\{boun}\{boun}_BV_{str(year)[-2:]}_.shp"
            input_mask = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\boundary\boun_mask\v4\{boun}_v4.shp"
            inputs_list = [input_sids, input_mask]

            temp_output = fr"in_memory/merge"

            arcpy.env.overwriteOutput = True
            arcpy.management.Merge(inputs_list, output=temp_output)

            in_features = temp_output
            out_feature_class = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_{str(year)[-2:]}\{boun}\{boun}_BV_{str(year)[-2:]}.shp"

            arcpy.analysis.PairwiseDissolve(in_features, out_feature_class)
            print(out_feature_class)
