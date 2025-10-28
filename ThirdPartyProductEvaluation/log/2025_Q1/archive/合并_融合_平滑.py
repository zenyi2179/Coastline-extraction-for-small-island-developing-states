import arcpy

if __name__ == '__main__':
    boun_list = ['CUB']
    for boun in boun_list:
        for year in [2015]:
            inputs_list = [
                fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\j_SIDS_Polygon\{boun}\{boun}_{str(year)[-2:]}_1.shp',
                fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\j_SIDS_Polygon\{boun}\{boun}_{str(year)[-2:]}_2.shp',
                fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\j_SIDS_Polygon\{boun}\{boun}_{str(year)[-2:]}_3.shp',
                ]

            temp_output = fr"in_memory/merge"

            arcpy.env.overwriteOutput = True
            arcpy.management.Merge(inputs_list, output=temp_output)

            in_features = temp_output

            temp_smoo_shp = fr"in_memory/smoo_merge"
            arcpy.analysis.PairwiseDissolve(in_features, temp_smoo_shp)

            out_feature_class = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\k_SIDS_Smooth\{boun}\{boun}_{str(year)[-2:]}.shp"
            # 步骤 5：对融合后的面进行平滑处理（使用 SmoothPolygon 工具）
            arcpy.cartography.SmoothPolygon(
                in_features=temp_smoo_shp,
                out_feature_class=out_feature_class,  # 输出平滑处理后的图层
                algorithm="PAEK",  # 使用 PAEK 算法进行平滑
                tolerance="90 Meters",  # 平滑的容忍度为 50 米
                endpoint_option="FIXED_ENDPOINT",  # 固定端点
                error_option="NO_CHECK"  # 不检查错误
            )
            print(out_feature_class)
