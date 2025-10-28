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
    sid_list = ["BHS"]   # 37 国家
    for sid in sid_list:
        for year in [2015]:
            # Execute
            fix_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_{str(year)[-2:]}\{sid}\{sid}_BV_{str(year)[-2:]}_.shp"
            add_shp = fr"C:\Users\23242\Desktop\draft0430\BV补丁\{sid}_BV_{str(year)[-2:]}_add.shp"
            temp_merge_shp = fr"in_memory/temp_merge_shp"
            arcpy.management.Merge([fix_shp, add_shp], temp_merge_shp)
            print(temp_merge_shp)

            # Execute Pairwise Clip
            out_feature_class = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_{str(year)[-2:]}\{sid}\{sid}_BV_{str(year)[-2:]}.shp"
            arcpy.analysis.PairwiseDissolve(temp_merge_shp, out_feature_class, multi_part="SINGLE_PART")
            print(out_feature_class)
