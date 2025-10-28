import os
import arcpy

def valid_coastline_line(in_data, out_data):
    arcpy.env.overwriteOutput = True

    arcpy.management.FeatureToLine(
        in_features=[in_data], out_feature_class=out_data,
        attributes="ATTRIBUTES")

def valid_inland_line(in_data, in_mask, out_data):
    arcpy.env.overwriteOutput = True

    temp_line = fr'in_memory/temp_out_line'
    arcpy.management.FeatureToLine(
        in_features=[in_data], out_feature_class=temp_line,
        attributes="ATTRIBUTES")

    arcpy.analysis.PairwiseClip(
        in_features=temp_line, clip_features=in_mask,
        out_feature_class=out_data)

def SIDS_CL(insert_boun_list, extract_boun_list, out_folder, extend_year,  option='insert'):
    mask_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\boundary\boun_mask'
    print(fr'The command being executed is: {option}.')

    origin_data = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\f_SIDS_Optimize'

    if option == 'insert' or option == 'both':
        for insert_boun in insert_boun_list:
            out_path = os.path.join(out_folder, insert_boun)    # ABW
            os.makedirs(name=out_path, exist_ok=True)  # 构建输出路径

            input_data = os.path.join(origin_data, fr"{insert_boun}/{insert_boun}_{str(extend_year)[-2:]}.shp")
            output_data = os.path.join(out_path, fr"{insert_boun}_CL_{str(extend_year)[-2:]}.shp")

            valid_coastline_line(in_data=input_data, out_data=output_data)
            print(fr'insert success: {output_data}')

    if option == 'extract' or option == 'both':
        for insert_boun in extract_boun_list:
            out_path = os.path.join(out_folder, insert_boun)  # ABW
            os.makedirs(name=out_path, exist_ok=True)  # 构建输出路径

            input_data = os.path.join(origin_data, fr"{insert_boun}/{insert_boun}_{str(extend_year)[-2:]}.shp")
            input_mask = os.path.join(mask_path, fr"{insert_boun}_v3.shp")
            output_data = os.path.join(out_path, fr"{insert_boun}_CL_{str(extend_year)[-2:]}.shp")

            valid_inland_line(in_data=input_data, in_mask=input_mask, out_data=output_data)
            print(fr'insert success: {output_data}')



def main():
    # 不同类型的国家
    insert_boun_list = ["BMU",
                        "KNA",
                        "MSR",
                        "NRU",
                        "BRB",
                        "DMA",
                        "GUM",
                        "NIU",
                        "SGP",
                        "VCT",
                        "AIA",
                        "CYM",
                        "VGB",
                        "VIR",
                        "ABW",
                        "ASM",
                        "CUW",
                        "GRD",
                        "LCA",
                        "MTQ",
                        "ATG",
                        "GLP",
                        "STP",
                        "TCA",
                        "COM",
                        "WSM",
                        "TTO",
                        "MUS",
                        "TUV",
                        "PLW",
                        "MNP",
                        "JAM",
                        "PRI",
                        "CPV",
                        "TON",
                        "COK",
                        "SYC",
                        "VUT",
                        "MDV",
                        "NCL",
                        "KIR",
                        "MHL",
                        "FSM",
                        "FJI",
                        "SLB",
                        "BHS",
                        "CUB",
                        "PYF",
                        ]  # the insert 48 couns
    insert_boun_list = [        # 异常 "KIR",
"KNA",
"LCA",
"MDV",
"MHL",
"MUS",
"NRU",
"PLW",
"SGP",
"SLB",
"STP",
"SYC",
"TON",
"TTO",
"TUV",
"VCT",
"VUT",
"WSM",
]  # the insert 29 couns

    extract_boun_list = ["SXM",
                         "BLZ",
                         "DOM",
                         "GNB",
                         "GUY",
                         "HTI",
                         "PNG",
                         "SUR",
                         "TLS",
                         ]  # the extract 9 couns
    extract_boun_list = ["BLZ",
"DOM",
"GNB",
"GUY",
"HTI",
"PNG",
"SUR",
"TLS",
]
    # extract_boun_list = ["BLZ",]


    # option_list = ['insert', 'extract', 'both']

    # year = 2000
    # year_list = [2000, 2010, 2020]
    year_list = [2015]
    for year in year_list:
        out_folder = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_{str(year)[-2:]}'
        SIDS_CL(insert_boun_list, extract_boun_list, out_folder, extend_year=year, option='insert')


if __name__ == '__main__':
    main()
