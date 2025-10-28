import os
import arcpy

def line_to_polygon(input_shp, output_shp):  # _draft

    temp_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\temp.shp"

    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    arcpy.management.FeatureToPolygon(in_features=[input_shp], out_feature_class=temp_shp, cluster_tolerance="",
                                      attributes="ATTRIBUTES", label_features="")

    arcpy.management.Dissolve(in_features=temp_shp, out_feature_class=output_shp, dissolve_field=[], statistics_fields=[],
                              multi_part="SINGLE_PART", unsplit_lines="DISSOLVE_LINES", concatenation_separator="")

    print(fr"line_to_polygon save as: {output_shp}")


def main():
    # 全 37 国家
    sids_cou_list = ["ATG",
"BHS",
"BLZ",
"BRB",
"COM",
"CPV",

"DMA",
"DOM",


"GNB",
"GRD",
"GUY",
"HTI",
"JAM",

"KNA",
"LCA",
"MDV",


"NRU",
"PLW",

"SGP",

"STP",
"SUR",

"TLS",
"TON",
"TTO",
"TUV",
"VCT",
"VUT",
"WSM",

                     ]
    for sids_cou in sids_cou_list:
        for year in [2015]:
            # 示例调用
            input_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\i_SIDS_Line\{sids_cou}\{sids_cou}_{str(year)[-2:]}.shp"
            output_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\j_SIDS_Polygon\{sids_cou}\{sids_cou}_{str(year)[-2:]}.shp"
            # 新建文件夹
            os.makedirs(name=fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\j_SIDS_Polygon\{sids_cou}",
                        exist_ok=True)

            line_to_polygon(input_shp, output_shp)


if __name__ == '__main__':
    main()
