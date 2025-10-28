import arcpy

if __name__ == '__main__':
    # Execute Pairwise Clip
    in_features = "taxlots"
    out_feature_class = "C:/output/output.gdb/taxlots_dissolved",
    multi_part = "SINGLE_PART"
    # MULTI_PART—输出中将包含多部件要素。 这是默认设置。
    # SINGLE_PART—输出中不包含多部件要素。 系统将为各部件创建单独的要素。

    arcpy.env.overwriteOutput = True
    arcpy.analysis.PairwiseDissolve(in_features, out_feature_class, multi_part)
