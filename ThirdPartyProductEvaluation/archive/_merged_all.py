
# ====== _GCL_FCS30.py ======
import arcpy
import os


def extract_data_by_position(in_data, in_boun, out_data):
    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    # Process: 按位置选择图层 (按位置选择图层) (management)
    aim_layer = arcpy.management.SelectLayerByLocation(
        in_layer=[in_data], overlap_type="INTERSECT", select_features=in_boun,
        search_distance="2 Kilometers",  selection_type="NEW_SELECTION")

    # Process: 导出要素 (导出要素) (conversion)
    arcpy.conversion.ExportFeatures(in_features=aim_layer, out_features=out_data)

    # 清除选择
    arcpy.SelectLayerByAttribute_management(aim_layer, "CLEAR_SELECTION")

    print(fr'success: {out_data}')

def selected_valid_data():
    # SIDS 国家位置
    sids_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\boundary\SIDS_boun.shp'

    # GID_boundary
    continent_list = ['Africa', 'Antarctica', 'Asia', 'Europe', 'North_America', 'Oceania', 'South_America']

    for continent in continent_list:
        # 定义文件夹路径
        folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GMSSD_2015\{continent}"
        # 获取文件夹中所有文件
        all_files = os.listdir(folder_path)
        # 筛选出后缀为 .shp 的文件
        shp_files = [file for file in all_files if file.endswith('.shp')]
        # 输出结果
        print("SHAP files:", shp_files)

        for shp in shp_files:
            input_data = os.path.join(folder_path, shp)
            output_folder = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\\' \
                            fr'_ThirdProductEvaluation\GMSSD_2015\_draft'

            output_data = os.path.join(output_folder, shp)
            extract_data_by_position(
                in_data=input_data, in_boun=sids_path, out_data=output_data)

def delete_blank_shp():
    # 定义文件夹路径
    folder_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\GMSSD_2015\_draft"

    # 获取文件夹中所有文件
    all_files = os.listdir(folder_path)

    # 筛选出所有 .shp 文件
    shp_files = [file for file in all_files if file.endswith('.shp')]

    # 遍历所有 .shp 文件
    for shp_file in shp_files:
        shp_file_path = os.path.join(folder_path, shp_file)

        # 获取文件大小
        try:
            file_size = os.path.getsize(shp_file_path)
        except OSError as e:
            print(f"无法获取文件大小: {shp_file_path}, 错误: {e}")
            continue

        # 检查文件大小是否小于 100 字节且大于0字节（排除异常情况）
        if file_size <= 100:
            base_name = os.path.splitext(shp_file)[0]

            # 删除同名的其他后缀的文件
            for file in all_files:
                if file.startswith(base_name) and not file.endswith('.shp'):
                    file_path = os.path.join(folder_path, file)
                    try:
                        os.remove(file_path)
                        print(f"已删除: {file_path}")
                    except Exception as e:
                        print(f"删除文件时出错: {file_path}, 错误: {e}")

            # 删除自身 .shp 文件
            try:
                os.remove(shp_file_path)
                print(f"已删除: {shp_file_path}")
            except Exception as e:
                print(f"删除文件时出错: {shp_file_path}, 错误: {e}")

def main():
    # 筛选有效数据
    # selected_valid_data()

    # 筛出无效数据 .shp < 100byte
    # delete_blank_shp()




if __name__ == '__main__':
    main()


# ====== _GMSSD_2015.py ======
import arcpy
import os


def extract_data_by_position(in_data, in_boun, out_data):
    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    # Process: 按位置选择图层 (按位置选择图层) (management)
    aim_layer = arcpy.management.SelectLayerByLocation(
        in_layer=[in_data], overlap_type="INTERSECT", select_features=in_boun,
        search_distance="2 Kilometers",  selection_type="NEW_SELECTION")

    # Process: 导出要素 (导出要素) (conversion)
    arcpy.conversion.ExportFeatures(in_features=aim_layer, out_features=out_data)

    # 清除选择
    arcpy.SelectLayerByAttribute_management(aim_layer, "CLEAR_SELECTION")

    print(fr'success: {out_data}')

def selected_valid_data():
    # SIDS 国家位置
    sids_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\boundary\SIDS_boun.shp'

    # GID_boundary
    continent_list = ['Africa', 'Antarctica', 'Asia', 'Europe', 'North_America', 'Oceania', 'South_America']

    for continent in continent_list:
        # 定义文件夹路径
        folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GMSSD_2015\{continent}"
        # 获取文件夹中所有文件
        all_files = os.listdir(folder_path)
        # 筛选出后缀为 .shp 的文件
        shp_files = [file for file in all_files if file.endswith('.shp')]
        # 输出结果
        print("SHAP files:", shp_files)

        for shp in shp_files:
            input_data = os.path.join(folder_path, shp)
            output_folder = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\\' \
                            fr'_ThirdProductEvaluation\GMSSD_2015\_draft'

            output_data = os.path.join(output_folder, shp)
            extract_data_by_position(
                in_data=input_data, in_boun=sids_path, out_data=output_data)

def delete_blank_shp():
    # 定义文件夹路径
    folder_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\GMSSD_2015\_draft"

    # 获取文件夹中所有文件
    all_files = os.listdir(folder_path)

    # 筛选出所有 .shp 文件
    shp_files = [file for file in all_files if file.endswith('.shp')]

    # 遍历所有 .shp 文件
    for shp_file in shp_files:
        shp_file_path = os.path.join(folder_path, shp_file)

        # 获取文件大小
        try:
            file_size = os.path.getsize(shp_file_path)
        except OSError as e:
            print(f"无法获取文件大小: {shp_file_path}, 错误: {e}")
            continue

        # 检查文件大小是否小于 100 字节且大于0字节（排除异常情况）
        if file_size <= 100:
            base_name = os.path.splitext(shp_file)[0]

            # 删除同名的其他后缀的文件
            for file in all_files:
                if file.startswith(base_name) and not file.endswith('.shp'):
                    file_path = os.path.join(folder_path, file)
                    try:
                        os.remove(file_path)
                        print(f"已删除: {file_path}")
                    except Exception as e:
                        print(f"删除文件时出错: {file_path}, 错误: {e}")

            # 删除自身 .shp 文件
            try:
                os.remove(shp_file_path)
                print(f"已删除: {shp_file_path}")
            except Exception as e:
                print(f"删除文件时出错: {shp_file_path}, 错误: {e}")

def main():
    # 筛选有效数据
    selected_valid_data()

    # 筛出无效数据 .shp < 100byte
    # delete_blank_shp()


if __name__ == '__main__':
    main()


# ====== _SIDS_CL.py ======
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


# ====== dbf_to_excel.py ======
import os
import pandas as pd
from dbfread import DBF


def read_dbf_file(dbf_file_path, field_name):
    """
    读取指定的 DBF 文件并获取指定字段的第一个值。
    如果字段不存在或文件为空，则返回 0。

    参数:
        dbf_file_path (str): DBF 文件的路径。
        field_name (str): 需要读取的字段名称。

    返回:
        float: 指定字段的第一个值，或 0。
    """
    try:
        # 读取 DBF 文件
        table = DBF(dbf_file_path)
        # 获取指定字段的所有值
        values = [record[field_name] for record in table if field_name in record]
        # 返回第一个值，如果列表为空则返回 0
        return values[0] if values else 0
    except Exception as e:
        print(f"读取 {dbf_file_path} 时出错: {e}")
        return 0


def process_data(data_path, data_name_list, boundary_list):
    """
    处理数据并生成二维列表，用于后续转换为 DataFrame。

    参数:
        data_path (str): 数据文件夹的路径。
        data_name_list (list): 数据表名称列表。
        boundary_list (list): 边界名称列表。

    返回:
        list: 包含所有数据的二维列表。
    """
    # 初始化二维列表，第一行为字段名
    fields_list = ['ID', 'GID'] + data_name_list
    dbf_data = [fields_list]

    # 遍历每个边界
    row_count = 1
    for boundary in boundary_list:
        row_data = [row_count, boundary]  # 初始化行数据，包含 ID 和 GID
        # 遍历每个数据表
        for data_name in data_name_list:
            # 构造 DBF 文件路径
            dbf_file_path = os.path.join(data_path, data_name, f"{boundary}\_{boundary}_merge.dbf")
            # 读取 DBF 文件并获取 'Leng_Geo' 字段的值
            length_geo_value = read_dbf_file(dbf_file_path, 'Leng_Geo')
            row_data.append(length_geo_value)
        # 将当前行数据添加到总数据列表中
        dbf_data.append(row_data)
        row_count += 1

    return dbf_data


def save_to_excel(data, output_file):
    """
    将二维列表数据保存为 Excel 文件。

    参数:
        data (list): 二维列表数据。
        output_file (str): 输出的 Excel 文件路径。
    """
    # 将二维列表转换为 DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])
    # 保存为 Excel 文件
    df.to_excel(output_file, index=False)
    print(f"数据已成功导出到 {output_file}")


def main():
    # 数据路径和相关参数
    data_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation"
    data_name_list = ['SIDS_CL_10', 'SIDS_CL_15', 'SIDS_CL_20',
                      'GSV', 'GMSSD_2015', 'OSM',
                      'GCL_FCS30_10', 'GCL_FCS30_15','GCL_FCS30_20']
    # 全 57 国家
    boundary_list = [
        "BMU",
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
        "SXM",
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
        "TLS",
        "TON",
        "COK",
        "BLZ",
        "GNB",
        "SYC",
        "HTI",
        "DOM",
        "VUT",
        "MDV",
        "NCL",
        "KIR",
        "MHL",
        "FSM",
        "FJI",
        "SUR",
        "SLB",
        "BHS",
        "CUB",
        "GUY",
        "PYF",
        "PNG",
    ]
    # 全 37 国家
    boundary_list = ["ATG",
                     "BHS",
                     "BLZ",
                     "BRB",
                     "COM",
                     "CPV",
                     "CUB",
                     "DMA",
                     "DOM",
                     "FJI",
                     "FSM",
                     "GNB",
                     "GRD",
                     "GUY",
                     "HTI",
                     "JAM",
                     "KIR",
                     "KNA",
                     "LCA",
                     "MDV",
                     "MHL",
                     "MUS",
                     "NRU",
                     "PLW",
                     "PNG",
                     "SGP",
                     "SLB",
                     "STP",
                     "SUR",
                     "SYC",
                     "TLS",
                     "TON",
                     "TTO",
                     "TUV",
                     "VCT",
                     "VUT",
                     "WSM",
                     ]

    # 处理数据并生成二维列表
    dbf_data = process_data(data_path, data_name_list, boundary_list)
    print("生成的二维列表数据：")
    print(dbf_data)

    # 保存数据到 Excel 文件
    output_file = "output0530.xlsx"
    save_to_excel(dbf_data, output_file)


if __name__ == "__main__":
    main()

# ====== extract_valid_data.py ======
# -*- coding: utf-8 -*-
"""
Generated by ArcGIS ModelBuilder on : 2025-04-18 16:27:58
"""
import arcpy
import os


def extract_data_by_position(in_data, in_boun, out_data):
    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    # Process: 按位置选择图层 (按位置选择图层) (management)
    aim_layer = arcpy.management.SelectLayerByLocation(
        in_layer=[in_data], overlap_type="INTERSECT", select_features=in_boun,
        search_distance="200 Meters", selection_type="NEW_SELECTION")

    # Process: 导出要素 (导出要素) (conversion)
    arcpy.conversion.ExportFeatures(in_features=aim_layer, out_features=out_data)

    # 清除选择
    arcpy.SelectLayerByAttribute_management(aim_layer, "CLEAR_SELECTION")


def extract_data_by_mask(in_data, in_boun, in_mask_boun, out_data):
    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    # Process: 按位置选择图层 (按位置选择图层) (management)
    aim_layer = arcpy.management.SelectLayerByLocation(
        in_layer=[in_data], overlap_type="INTERSECT", select_features=in_boun,
        search_distance="200 Meters", selection_type="NEW_SELECTION")

    # Process: 成对裁剪 (成对裁剪) (analysis)
    arcpy.analysis.PairwiseClip(
        in_features=aim_layer, clip_features=in_mask_boun, out_feature_class=out_data)


def CSV(insert_boun_list, extract_boun_list, origin_data_list, out_folder, option='both'):
    admin_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\d_SIDS_Boundary\SIDS\AdminDivision'
    mask_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\boundary\boun_mask'
    print(fr'The command being executed is: {option}.')

    if option == 'insert' or option == 'both':
        for insert_boun in insert_boun_list:
            input_boun = os.path.join(admin_path, fr'{insert_boun}.shp')
            for input_data in origin_data_list:
                out_path = os.path.join(out_folder, insert_boun)
                os.makedirs(name=out_path, exist_ok=True)
                output_name = fr'{insert_boun}_{os.path.splitext(os.path.basename(input_data))[0]}.shp'

                # 针对 相交类 岛屿导出
                extract_data_by_position(
                    in_data=input_data, in_boun=input_boun, out_data=os.path.join(out_path, output_name)
                )
                print(fr'insert success: {output_name}')

    if option == 'extract' or option == 'both':
        for insert_boun in extract_boun_list:
            input_boun = os.path.join(admin_path, fr'{insert_boun}.shp')
            for input_data in origin_data_list:
                out_path = os.path.join(out_folder, insert_boun)
                os.makedirs(name=out_path, exist_ok=True)
                output_name = fr'{insert_boun}_{os.path.splitext(os.path.basename(input_data))[0]}.shp'

                # 针对 大陆裁剪类
                input_mask_boun = os.path.join(mask_path, fr'{insert_boun}_v2.shp')
                extract_data_by_mask(
                    in_data=input_data, in_boun=input_boun, in_mask_boun=input_mask_boun,
                    out_data=os.path.join(out_path, output_name)
                )
                print(fr'extract success: {output_name}')


def GMSSD_2015(insert_boun_list, extract_boun_list, out_folder, option='insert'):
    admin_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\d_SIDS_Boundary\SIDS\AdminDivision'
    mask_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\boundary\boun_mask'
    print(fr'The command being executed is: {option}.')

    # 有效 shp 名称列表
    origin_data = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\GMSSD_2015\_draft'
    data_files = os.listdir(origin_data)
    origin_data_list = [os.path.join(origin_data, data) for data in data_files if data.endswith('.shp')]

    if option == 'insert' or option == 'both':
        for insert_boun in insert_boun_list:
            input_boun = os.path.join(admin_path, fr'{insert_boun}.shp')    # 国家边界
            for input_data in origin_data_list:
                out_path = os.path.join(out_folder, insert_boun)
                os.makedirs(name=out_path, exist_ok=True)   # 构建输出路径
                input_data_name = os.path.basename(input_data)
                output_name = fr"{insert_boun}_{input_data_name.split('_')[0]}_{input_data_name.split('_')[1]}.shp"

                # 针对 相交类 岛屿导出
                extract_data_by_position(
                    in_data=input_data, in_boun=input_boun, out_data=os.path.join(out_path, output_name)
                )
                print(fr'insert success: {output_name}')

    if option == 'extract' or option == 'both':
        for insert_boun in extract_boun_list:
            input_boun = os.path.join(admin_path, fr'{insert_boun}.shp')
            for input_data in origin_data_list:
                out_path = os.path.join(out_folder, insert_boun)
                os.makedirs(name=out_path, exist_ok=True)
                input_data_name = os.path.basename(input_data)
                output_name = fr"{insert_boun}_{input_data_name.split('_')[0]}_{input_data_name.split('_')[1]}.shp"

                # 针对 大陆裁剪类
                input_mask_boun = os.path.join(mask_path, fr'{insert_boun}_v2.shp')
                extract_data_by_mask(
                    in_data=input_data, in_boun=input_boun, in_mask_boun=input_mask_boun,
                    out_data=os.path.join(out_path, output_name)
                )
                print(fr'extract success: {output_name}')


def GCL_FCS30(insert_boun_list, extract_boun_list, out_folder, extend_year, option='insert'):
    admin_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\d_SIDS_Boundary\SIDS\AdminDivision'
    mask_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\boundary\boun_mask'
    print(fr'The command being executed is: {option}.')

    # 有效 shp 名称列表
    origin_data = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\GCL_FCS30_{str(extend_year)[-2:]}\_draft'
    input_data = [os.path.join(origin_data, fr'GCL{extend_year}.shp')]

    if option == 'insert' or option == 'both':
        for insert_boun in insert_boun_list:
            input_boun = os.path.join(admin_path, fr'{insert_boun}.shp')    # 国家边界
            out_path = os.path.join(out_folder, insert_boun)
            os.makedirs(name=out_path, exist_ok=True)  # 构建输出路径
            output_name = fr"{insert_boun}_GCL_{extend_year}.shp"
            # 针对 相交类 岛屿导出
            extract_data_by_position(
                in_data=input_data, in_boun=input_boun, out_data=os.path.join(out_path, output_name)
            )
            print(fr'insert success: {output_name}')

    if option == 'extract' or option == 'both':
        for insert_boun in extract_boun_list:
            input_boun = os.path.join(admin_path, fr'{insert_boun}.shp')
            out_path = os.path.join(out_folder, insert_boun)
            os.makedirs(name=out_path, exist_ok=True)
            output_name = fr"{insert_boun}_GCL_{extend_year}.shp"

            # 针对 大陆裁剪类
            input_mask_boun = os.path.join(mask_path, fr'{insert_boun}_v2.shp')
            extract_data_by_mask(
                in_data=input_data, in_boun=input_boun, in_mask_boun=input_mask_boun,
                out_data=os.path.join(out_path, output_name)
            )
            print(fr'extract success: {output_name}')



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
    # insert_boun_list = ['BLZ']
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

    out_folder = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\GSV'
    data_name_list = ['Continent', 'Big', 'Small', 'VerySmall']
    origin_data_list = [os.path.join(out_folder, fr'_draft\{name}.shp') for name in data_name_list]
    # option_list = ['insert', 'extract', 'both']

    # CSV(insert_boun_list, extract_boun_list, origin_data_list, out_folder, option='extract')
    # ----------------------------------------------------------------------------------------------------------------
    # out_folder = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\GMSSD_2015'
    # GMSSD_2015(insert_boun_list, extract_boun_list, out_folder, option='extract')
    # ----------------------------------------------------------------------------------------------------------------
    year = 2020
    out_folder = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\GCL_FCS30_{str(year)[-2:]}'
    GCL_FCS30(insert_boun_list, extract_boun_list, out_folder, extend_year=year, option='both')



if __name__ == '__main__':
    main()


# ====== extract_valid_data_l.py ======
# -*- coding: utf-8 -*-
"""
Generated by ArcGIS ModelBuilder on : 2025-04-18 16:27:58
"""
import arcpy
import os


def extract_data_by_position(in_data, in_boun, out_data):
    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    # Process: 按位置选择图层 (按位置选择图层) (management)
    aim_layer = arcpy.management.SelectLayerByLocation(
        in_layer=[in_data], overlap_type="INTERSECT", select_features=in_boun,
        search_distance="200 Meters", selection_type="NEW_SELECTION")

    # Process: 导出要素 (导出要素) (conversion)
    arcpy.conversion.ExportFeatures(in_features=aim_layer, out_features=out_data)

    # 清除选择
    arcpy.SelectLayerByAttribute_management(aim_layer, "CLEAR_SELECTION")


def extract_data_by_mask(in_data, in_boun, in_mask_boun, out_data):
    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    # Process: 按位置选择图层 (按位置选择图层) (management)
    aim_layer = arcpy.management.SelectLayerByLocation(
        in_layer=[in_data], overlap_type="INTERSECT", select_features=in_boun,
        search_distance="200 Meters", selection_type="NEW_SELECTION")

    # Process: 成对裁剪 (成对裁剪) (analysis)
    arcpy.analysis.PairwiseClip(
        in_features=aim_layer, clip_features=in_mask_boun, out_feature_class=out_data)


def CSV(insert_boun_list, extract_boun_list, origin_data_list, out_folder, option='both'):
    admin_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\d_SIDS_Boundary\SIDS\AdminDivision'
    mask_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\boundary\boun_mask'
    print(fr'The command being executed is: {option}.')

    if option == 'insert' or option == 'both':
        for insert_boun in insert_boun_list:
            input_boun = os.path.join(admin_path, fr'{insert_boun}.shp')
            for input_data in origin_data_list:
                out_path = os.path.join(out_folder, insert_boun)
                os.makedirs(name=out_path, exist_ok=True)
                output_name = fr'{insert_boun}_{os.path.splitext(os.path.basename(input_data))[0]}.shp'

                # 针对 相交类 岛屿导出
                extract_data_by_position(
                    in_data=input_data, in_boun=input_boun, out_data=os.path.join(out_path, output_name)
                )
                print(fr'insert success: {output_name}')

    if option == 'extract' or option == 'both':
        for insert_boun in extract_boun_list:
            input_boun = os.path.join(admin_path, fr'{insert_boun}.shp')
            for input_data in origin_data_list:
                out_path = os.path.join(out_folder, insert_boun)
                os.makedirs(name=out_path, exist_ok=True)
                output_name = fr'{insert_boun}_{os.path.splitext(os.path.basename(input_data))[0]}.shp'

                # 针对 大陆裁剪类
                input_mask_boun = os.path.join(mask_path, fr'{insert_boun}_v3.shp')
                extract_data_by_mask(
                    in_data=input_data, in_boun=input_boun, in_mask_boun=input_mask_boun,
                    out_data=os.path.join(out_path, output_name)
                )
                print(fr'extract success: {output_name}')

def GMSSD_2015(insert_boun_list, extract_boun_list, out_folder, option='insert'):
    admin_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\d_SIDS_Boundary\SIDS\AdminDivision'
    mask_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\boundary\boun_mask'
    print(fr'The command being executed is: {option}.')

    # 有效 shp 名称列表
    origin_data = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\GMSSD_2015\_draft'
    data_files = os.listdir(origin_data)
    origin_data_list = [os.path.join(origin_data, data) for data in data_files if data.endswith('.shp')]

    if option == 'insert' or option == 'both':
        for insert_boun in insert_boun_list:
            input_boun = os.path.join(admin_path, fr'{insert_boun}.shp')    # 国家边界
            for input_data in origin_data_list:
                out_path = os.path.join(out_folder, insert_boun)
                os.makedirs(name=out_path, exist_ok=True)   # 构建输出路径
                input_data_name = os.path.basename(input_data)
                output_name = fr"{insert_boun}_{input_data_name.split('_')[0]}_{input_data_name.split('_')[1]}.shp"

                # 针对 相交类 岛屿导出
                extract_data_by_position(
                    in_data=input_data, in_boun=input_boun, out_data=os.path.join(out_path, output_name)
                )
                print(fr'insert success: {output_name}')

    if option == 'extract' or option == 'both':
        for insert_boun in extract_boun_list:
            input_boun = os.path.join(admin_path, fr'{insert_boun}.shp')
            for input_data in origin_data_list:
                out_path = os.path.join(out_folder, insert_boun)
                os.makedirs(name=out_path, exist_ok=True)
                input_data_name = os.path.basename(input_data)
                output_name = fr"{insert_boun}_{input_data_name.split('_')[0]}_{input_data_name.split('_')[1]}.shp"

                # 针对 大陆裁剪类
                input_mask_boun = os.path.join(mask_path, fr'{insert_boun}_v3.shp')
                extract_data_by_mask(
                    in_data=input_data, in_boun=input_boun, in_mask_boun=input_mask_boun,
                    out_data=os.path.join(out_path, output_name)
                )
                print(fr'extract success: {output_name}')

def GCL_FCS30(insert_boun_list, extract_boun_list, out_folder, extend_year, option='insert'):
    admin_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\d_SIDS_Boundary\SIDS\AdminDivision'
    mask_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\boundary\boun_mask'
    print(fr'The command being executed is: {option}.')

    # 有效 shp 名称列表
    origin_data = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\GCL_FCS30_{str(extend_year)[-2:]}\_draft'
    input_data = [os.path.join(origin_data, fr'GCL{extend_year}.shp')]

    if option == 'insert' or option == 'both':
        for insert_boun in insert_boun_list:
            input_boun = os.path.join(admin_path, fr'{insert_boun}.shp')    # 国家边界
            out_path = os.path.join(out_folder, insert_boun)
            os.makedirs(name=out_path, exist_ok=True)  # 构建输出路径
            output_name = fr"{insert_boun}_GCL_{extend_year}.shp"
            # 针对 相交类 岛屿导出
            extract_data_by_position(
                in_data=input_data, in_boun=input_boun, out_data=os.path.join(out_path, output_name)
            )
            print(fr'insert success: {output_name}')

    if option == 'extract' or option == 'both':
        for insert_boun in extract_boun_list:
            input_boun = os.path.join(admin_path, fr'{insert_boun}.shp')
            out_path = os.path.join(out_folder, insert_boun)
            os.makedirs(name=out_path, exist_ok=True)
            output_name = fr"{insert_boun}_GCL_{extend_year}.shp"

            # 针对 大陆裁剪类
            input_mask_boun = os.path.join(mask_path, fr'{insert_boun}_v3.shp')
            extract_data_by_mask(
                in_data=input_data, in_boun=input_boun, in_mask_boun=input_mask_boun,
                out_data=os.path.join(out_path, output_name)
            )
            print(fr'extract success: {output_name}')

def OSM(insert_boun_list, extract_boun_list, out_folder, option='both'):
    admin_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\d_SIDS_Boundary\SIDS\AdminDivision'
    mask_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\boundary\boun_mask'
    print(fr'The command being executed is: {option}.')

    # 有效 shp 名称列表
    origin_data = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\OSM\_draft'
    input_data = [os.path.join(origin_data, fr'coastlines_2020.shp')]

    if option == 'insert' or option == 'both':
        for insert_boun in insert_boun_list:
            input_boun = os.path.join(admin_path, fr'{insert_boun}.shp')  # 国家边界
            out_path = os.path.join(out_folder, insert_boun)
            os.makedirs(name=out_path, exist_ok=True)  # 构建输出路径
            output_name = fr"{insert_boun}_CL_2020.shp"
            # 针对 相交类 岛屿导出
            extract_data_by_position(
                in_data=input_data, in_boun=input_boun, out_data=os.path.join(out_path, output_name)
            )
            print(fr'insert success: {output_name}')

    if option == 'extract' or option == 'both':
        for insert_boun in extract_boun_list:
            input_boun = os.path.join(admin_path, fr'{insert_boun}.shp')
            out_path = os.path.join(out_folder, insert_boun)
            os.makedirs(name=out_path, exist_ok=True)
            output_name = fr"{insert_boun}_CL_2020.shp"

            # 针对 大陆裁剪类
            input_mask_boun = os.path.join(mask_path, fr'{insert_boun}_v3.shp')
            extract_data_by_mask(
                in_data=input_data, in_boun=input_boun, in_mask_boun=input_mask_boun,
                out_data=os.path.join(out_path, output_name)
            )
            print(fr'extract success: {output_name}')


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
    # insert_boun_list = ['BLZ']
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
    extract_boun_list = ["SXM"]

    out_folder = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\GSV'
    data_name_list = ['Continent_l', 'Big_l', 'Small_l', 'VerySmall_l']
    origin_data_list = [os.path.join(out_folder, fr'_draft\{name}.shp') for name in data_name_list]
    # option_list = ['insert', 'extract', 'both']

    # CSV(insert_boun_list, extract_boun_list, origin_data_list, out_folder, option='extract')
    # ----------------------------------------------------------------------------------------------------------------
    # out_folder = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\GMSSD_2015'
    # GMSSD_2015(insert_boun_list, extract_boun_list, out_folder, option='extract')
    # ----------------------------------------------------------------------------------------------------------------
    # for year in [2010, 2015, 2020]:
    #     out_folder = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\GCL_FCS30_{str(year)[-2:]}'
    #     GCL_FCS30(insert_boun_list, extract_boun_list, out_folder, extend_year=year, option='extract')
    # ----------------------------------------------------------------------------------------------------------------
    out_folder = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\OSM'
    OSM(insert_boun_list, extract_boun_list, out_folder, option='extract')


if __name__ == '__main__':
    main()


# ====== merge_calculate_fields.py ======
# -*- coding: utf-8 -*-
"""
Generated by ArcGIS ModelBuilder on : 2025-04-19 13:25:47
"""
import os
import arcpy


def merge_calculate(in_data_list, out_data):
    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    # Process: 合并 (合并) (management)
    temp_merge = fr'in_memory\shp_merge'
    arcpy.management.Merge(
        inputs=in_data_list,
        output=temp_merge)

    # Process: 成对融合 (成对融合) (analysis)
    arcpy.analysis.PairwiseDissolve(
        in_features=temp_merge, out_feature_class=out_data,
        multi_part="MULTI_PART")

    # Process: 计算几何属性 (计算几何属性) (management)
    output_path = arcpy.management.CalculateGeometryAttributes(
        in_features=out_data,
        geometry_property=[["Leng_Geo", "PERIMETER_LENGTH_GEODESIC"], ["Area_Geo", "AREA_GEODESIC"]],
        length_unit="KILOMETERS", area_unit="SQUARE_KILOMETERS", coordinate_format="SAME_AS_INPUT")[0]

    print(fr'merge_calculate: {out_data}')


def GSV(boun_list, work_path):
    print('GSV start:')
    data_name_list = ['Continent', 'Big', 'Small', 'VerySmall']
    for boun in boun_list:
        input_data_path = os.path.join(work_path, boun)

        # 获取文件夹中所有文件
        data_files = os.listdir(input_data_path)

        # 筛选出符合条件的文件
        selected_data_list = []
        for file in data_files:
            if file.endswith('.shp'):  # 确保是 .shp 文件
                # 去掉文件扩展名，只保留文件名
                file_name_without_extension = os.path.splitext(file)[0]
                # 检查文件名是否包含指定的后缀名
                for name in data_name_list:
                    if name in file_name_without_extension:
                        selected_data_list.append(file)
                        break  # 匹配到一个就跳出内层循环

        # 输出结果
        print("Selected files:", selected_data_list)

        # 合并的数据列表
        output_path = os.path.join(input_data_path, fr'_{boun}_merge.shp')
        input_data_list = [os.path.join(input_data_path, selected_data) for selected_data in selected_data_list]
        merge_calculate(in_data_list=input_data_list, out_data=output_path)

def GMSSD_2015(boun_list, work_path):
    print('GMSSD_2015 start:')

    for boun in boun_list:
        data_sids_path = os.path.join(work_path, boun)
        data_files = os.listdir(data_sids_path)
        input_data_list = [os.path.join(data_sids_path, data) for data in data_files if data.endswith('.shp')]

        # 输出结果
        print("Selected files:", input_data_list)

        # 合并的数据列表
        output_path = os.path.join(data_sids_path, fr'_{boun}_merge.shp')
        merge_calculate(in_data_list=input_data_list, out_data=output_path)

def GCL_FCS30(boun_list, extend_year, work_path):
    print('GCL_FCS30 start:')

    for boun in boun_list:
        data_sids_path = os.path.join(work_path, boun)
        data_files = os.listdir(data_sids_path)
        input_data_list = [os.path.join(data_sids_path, data) for data in data_files if data.endswith('.shp')]

        # 输出结果
        print("Selected files:", input_data_list)

        # 合并的数据列表
        output_path = os.path.join(data_sids_path, fr'_{boun}_merge.shp')
        merge_calculate(in_data_list=input_data_list, out_data=output_path)

def SIDS_BV(boun_list, extend_year, work_path):
    print('SIDS_BV start:')

    for boun in boun_list:
        data_sids_path = os.path.join(work_path, boun)
        input_data_list = [os.path.join(data_sids_path, fr"{boun}_BV_{str(extend_year)[-2:]}.shp")]

        # 输出结果
        print("Selected files:", input_data_list)

        # 合并的数据列表
        output_path = os.path.join(data_sids_path, fr'_{boun}_merge_BV.shp')
        merge_calculate(in_data_list=input_data_list, out_data=output_path)

def main():
    # 全 57 国家
    boundary_list = [
        "BMU",
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
        "SXM",
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
        "TLS",
        "TON",
        "COK",
        "BLZ",
        "GNB",
        "SYC",
        "HTI",
        "DOM",
        "VUT",
        "MDV",
        "NCL",
        "KIR",
        "MHL",
        "FSM",
        "FJI",
        "SUR",
        "SLB",
        "BHS",
        "CUB",
        "GUY",
        "PYF",
        "PNG",
    ]
    # 全 37 国家
    boundary_list = ["ATG",
"BHS",
"BLZ",
"BRB",
"COM",
"CPV",
"CUB",
"DMA",
"DOM",
"FJI",
"FSM",
"GNB",
"GRD",
"GUY",
"HTI",
"JAM",
"KIR",
"KNA",
"LCA",
"MDV",
"MHL",
"MUS",
"NRU",
"PLW",
"PNG",
"SGP",
"SLB",
"STP",
"SUR",
"SYC",
"TLS",
"TON",
"TTO",
"TUV",
"VCT",
"VUT",
"WSM",
]

    # SIDS_BV -------------------------------------------------------------------------------------------
    # work_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\k_SIDS_Smooth'
    # SIDS_BV(boun_list=boundary_list, extend_year=year, work_path=work_path)
    # GSV -------------------------------------------------------------------------------------------
    # work_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\GSV'
    # GSV(boun_list=boundary_list, work_path=work_path)
    # -----------------------------------------------------------------------------------------------------------------
    # work_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\GMSSD_2015'
    # GMSSD_2015(boun_list=boundary_list, work_path=work_path)
    # -----------------------------------------------------------------------------------------------------------------
    # work_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\GCL_FCS30_{str(year)[-2:]}'
    # GCL_FCS30(boun_list=boundary_list, extend_year=year, work_path=work_path)
    # -----------------------------------------------------------------------------------------------------------------
    for year in [2015]:
        work_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_{str(year)[-2:]}'
        SIDS_BV(boun_list=boundary_list, extend_year=year, work_path=work_path)


if __name__ == '__main__':
    main()


# ====== merge_calculate_fields_l.py ======
# -*- coding: utf-8 -*-
"""
Generated by ArcGIS ModelBuilder on : 2025-04-19 13:25:47
"""
import os
import arcpy


def merge_calculate(in_data_list, out_data):
    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    # Process: 合并 (合并) (management)
    temp_merge = fr'in_memory\shp_merge'
    arcpy.management.Merge(
        inputs=in_data_list,
        output=temp_merge)

    # Process: 成对融合 (成对融合) (analysis)
    arcpy.analysis.PairwiseDissolve(
        in_features=temp_merge, out_feature_class=out_data,
        multi_part="MULTI_PART")

    # Process: 计算几何属性 (计算几何属性) (management)
    output_path = arcpy.management.CalculateGeometryAttributes(
        in_features=out_data,
        geometry_property=[["Leng_Geo", "LENGTH_GEODESIC"]],
        length_unit="KILOMETERS", coordinate_format="SAME_AS_INPUT")[0]

    print(fr'merge_calculate: {out_data}')


def GSV(boun_list, work_path):
    print('GSV start:')

    for boun in boun_list:
        data_sids_path = os.path.join(work_path, boun)
        data_files = os.listdir(data_sids_path)
        input_data_list = [os.path.join(data_sids_path, data) for data in data_files if data.endswith('.shp')]

        # 输出结果
        print("Selected files:", input_data_list)

        # 合并的数据列表
        output_path = os.path.join(data_sids_path, fr'_{boun}_merge.shp')
        merge_calculate(in_data_list=input_data_list, out_data=output_path)

def GMSSD_2015(boun_list, work_path):
    print('GMSSD_2015 start:')

    for boun in boun_list:
        data_sids_path = os.path.join(work_path, boun)
        data_files = os.listdir(data_sids_path)
        input_data_list = [os.path.join(data_sids_path, data) for data in data_files if data.endswith('.shp')]

        # 输出结果
        print("Selected files:", input_data_list)

        # 合并的数据列表
        output_path = os.path.join(data_sids_path, fr'_{boun}_merge.shp')
        merge_calculate(in_data_list=input_data_list, out_data=output_path)

def GCL_FCS30(boun_list, extend_year, work_path):
    print('GCL_FCS30 start:')

    for boun in boun_list:
        data_sids_path = os.path.join(work_path, boun)
        data_files = os.listdir(data_sids_path)
        input_data_list = [os.path.join(data_sids_path, data) for data in data_files if data.endswith('.shp')]

        # 输出结果
        print("Selected files:", input_data_list)

        # 合并的数据列表
        output_path = os.path.join(data_sids_path, fr'_{boun}_merge.shp')
        merge_calculate(in_data_list=input_data_list, out_data=output_path)

def OSM(boun_list, work_path):
    print('OSM start:')

    for boun in boun_list:
        data_sids_path = os.path.join(work_path, boun)
        data_files = os.listdir(data_sids_path)
        input_data_list = [os.path.join(data_sids_path, data) for data in data_files if data.endswith('.shp')]

        # 输出结果
        print("Selected files:", input_data_list)

        # 合并的数据列表
        output_path = os.path.join(data_sids_path, fr'_{boun}_merge.shp')
        merge_calculate(in_data_list=input_data_list, out_data=output_path)

def SIDS_CL(boun_list, work_path, year):
    print('SIDS_CL start:')

    for boun in boun_list:
        data_sids_path = os.path.join(work_path, boun)
        input_data_list = [os.path.join(data_sids_path, fr"{boun}_CL_{str(year)[-2:]}.shp")]

        # 输出结果
        print("Selected files:", input_data_list)

        # 合并的数据列表
        output_path = os.path.join(data_sids_path, fr'_{boun}_merge_CL.shp')
        merge_calculate(in_data_list=input_data_list, out_data=output_path)



def main():
    # 全 57 国家
    boundary_list = [
        "BMU",
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
        "SXM",
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
        "TLS",
        "TON",
        "COK",
        "BLZ",
        "GNB",
        "SYC",
        "HTI",
        "DOM",
        "VUT",
        "MDV",
        "NCL",
        "KIR",
        "MHL",
        "FSM",
        "FJI",
        "SUR",
        "SLB",
        "BHS",
        "CUB",
        "GUY",
        "PYF",
        "PNG",
    ]
    # 全 37 国家
    boundary_list = ["ATG",
"BHS",
"BLZ",
"BRB",
"COM",
"CPV",
"CUB",
"DMA",
"DOM",
"FJI",
"FSM",
"GNB",
"GRD",
"GUY",
"HTI",
"JAM",
"KIR",
"KNA",
"LCA",
"MDV",
"MHL",
"MUS",
"NRU",
"PLW",
"PNG",
"SGP",
"SLB",
"STP",
"SUR",
"SYC",
"TLS",
"TON",
"TTO",
"TUV",
"VCT",
"VUT",
"WSM",
]

    # GSV -------------------------------------------------------------------------------------------
    # work_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\GSV'
    # GSV(boun_list=boundary_list, work_path=work_path)
    # -----------------------------------------------------------------------------------------------------------------
    # work_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\GMSSD_2015'
    # GMSSD_2015(boun_list=boundary_list, work_path=work_path)
    # -----------------------------------------------------------------------------------------------------------------
    # for year in [2010, 2015, 2020]:
    #     work_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\GCL_FCS30_{str(year)[-2:]}'
    #     GCL_FCS30(boun_list=boundary_list, extend_year=year, work_path=work_path)
    # -----------------------------------------------------------------------------------------------------------------
    # work_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\OSM'
    # OSM(boun_list=boundary_list, work_path=work_path)
    # -----------------------------------------------------------------------------------------------------------------
    # for year in [2000, 2010, 2020]:
    for year in [2015]:
        work_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_{str(year)[-2:]}'
        SIDS_CL(boun_list=boundary_list, work_path=work_path, year=year)


if __name__ == '__main__':
    main()


# ====== statistics_dbf_excel.py ======
import pandas as pd

# 读取Excel文件
file_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\三方数据统计.xlsx"
df = pd.read_excel(file_path)

# 定义需要处理的列（假设这些是需要比较的列）
# columns_to_compare = ['SIDS_CL_00', 'SIDS_CL_10', 'SIDS_CL_20', 'GSV', 'GMSSD_2015', 'OSM']
columns_to_compare = ['SIDS_CL_10', 'SIDS_CL_15', 'SIDS_CL_20', 'GSV', 'GMSSD_2015']

# 遍历每一行，找到最大值和最小值对应的列名
results = []
for index, row in df.iterrows():
    # 获取当前行的指定列数据
    row_data = row[columns_to_compare]

    # 找到最大值和最小值对应的列名
    max_column = row_data.idxmax()
    min_column = row_data.idxmin()

    # 将结果存储到列表中
    results.append({
        'ID': row['ID'],
        'GID': row['GID'],
        'Max_Value_Column': max_column,
        'Min_Value_Column': min_column
    })

# 将结果转换为DataFrame
result_df = pd.DataFrame(results)

# 输出结果
print(result_df)

# 如果需要，可以将结果保存到新的Excel文件
result_df.to_excel('max_min_columns.xlsx', index=False)
