import os
import arcpy

def get_files_absolute_paths(folder_path, suffix=None):
    """
    获取指定文件夹下所有指定后缀的文件的绝对路径名称

    :param folder_path: 指定文件夹的路径
    :param suffix: 文件后缀（可选），如 '.shp'。如果不指定，则获取所有文件的路径
    :return: 指定后缀的文件的绝对路径名称列表
    """
    files_paths = []
    # 遍历指定文件夹
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 如果指定了后缀，则判断文件后缀是否匹配
            if suffix is None or file.endswith(suffix):
                # 获取文件的绝对路径并添加到列表中
                files_paths.append(os.path.abspath(os.path.join(root, file)))
    return files_paths

if __name__ == '__main__':
    arcpy.env.overwriteOutput = True
    sid_list = ["ATG",
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
]   # 37 国家
    for sid in sid_list:
        for year in [2015]:
            # 制定国家的图幅列表
            folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\e_SIDS_Shp\{sid}\{year}"
            suffix = fr'.shp'
            shp_files_paths = get_files_absolute_paths(folder_path=folder_path, suffix=suffix)

            # Execute Pairwise Clip
            merge_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\g_QGIS\a_SIDS_Shp_Merge\{sid}\{sid}_{str(year)[-2:]}.shp"
            arcpy.management.Merge(shp_files_paths, merge_shp)
            print(merge_shp)
