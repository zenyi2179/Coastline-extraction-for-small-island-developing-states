
# ====== 列表输出excel.py ======
import pandas as pd

def save_to_excel(data, file_name):
    """
    将二维列表保存为Excel文件

    参数:
        data (list of lists): 二维列表，其中每一行是一个列表
        file_name (str): 输出的Excel文件名，应包含扩展名（如.xlsx）
    """
    # 将二维列表转换为DataFrame
    df = pd.DataFrame(data)
    # 保存为Excel文件
    df.to_excel(file_name, index=False, header=False)
    print(f"数据已成功保存到 {file_name}")

# 示例用法
data = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]
save_to_excel(data, "example.xlsx")

# ====== 删除.py ======
import arcpy

if __name__ == '__main__':
    # Execute Pairwise Clip
    in_data = "majorrds.shp"

    arcpy.env.overwriteOutput = True
    arcpy.Delete_management(in_data)


# ====== 合并.py ======
import arcpy

if __name__ == '__main__':
    # Execute Pairwise Clip
    inputs_list = ["majorrds.shp", "Habitat_Analysis.gdb/futrds"]
    output = "C:/output/Output.gdb/allroads"

    arcpy.env.overwriteOutput = True
    arcpy.management.Merge(
        inputs=inputs_list,
        output=output)


# ====== 导出.py ======
import arcpy

if __name__ == '__main__':
    # Execute Pairwise Clip
    in_features = "C:/output/Output.gdb/in"
    out_features = "C:/output/Output.gdb/allroads"

    arcpy.conversion.ExportFeatures(in_features, out_features)

# ====== 批量文件夹合并.py ======
# -*- coding:utf-8 -*-
"""
将具有相同前缀 SIDs_Grid_Y15 的文件夹中的所有文件，提取并统一复制到指定的目标文件夹中。
"""
import os
import shutil

def merge_files_from_folders_with_prefix(src_root, folder_prefix, dst_folder):
    """
    将所有以指定前缀开头的文件夹中的文件合并复制到目标文件夹

    :param src_root: 源文件夹的根目录，例如 'E:/_GoogleDrive'
    :param folder_prefix: 文件夹的公共前缀，例如 'SIDs_Grid_Y15'
    :param dst_folder: 目标文件夹路径，例如 'E:/_OrderingProject/F_IslandsBoundaryChange/c_GeeData/SIDs_Grid_Y15'
    """
    # 确保目标文件夹存在
    os.makedirs(dst_folder, exist_ok=True)

    # 遍历根目录下的所有文件夹
    for folder_name in os.listdir(src_root):
        folder_path = os.path.join(src_root, folder_name)
        # 判断是否是目录且名称以指定前缀开头
        if os.path.isdir(folder_path) and folder_name.startswith(folder_prefix):
            print(f"处理文件夹：{folder_path}")
            # 遍历文件夹中的文件
            for file_name in os.listdir(folder_path):
                src_file = os.path.join(folder_path, file_name)
                dst_file = os.path.join(dst_folder, file_name)

                # 如果文件已存在可选择覆盖或跳过（此处选择覆盖）
                shutil.copy2(src_file, dst_file)
                print(f"已复制文件：{src_file} → {dst_file}")


if __name__ == '__main__':
    merge_files_from_folders_with_prefix(
        src_root="E:/_GoogleDrive",
        folder_prefix="SIDs_Grid_Y15",
        dst_folder="E:/_OrderingProject/F_IslandsBoundaryChange/c_GeeData/SIDs_Grid_Y15"
    )


# ====== 按行读取txt返回list.py ======
def read_txt_to_list(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    # 去除每行末尾的换行符
    lines = [line.strip() for line in lines]
    return lines

# 示例用法
file_path = 'example.txt'  # 替换为你的txt文件路径
result = read_txt_to_list(file_path)
print(result)

# ====== 文件移动.py ======
import os
import shutil

# 源目录路径
src_folder = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\k_SIDS_Smooth\ABW"
# 目标目录路径
dst_folder = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_00\ABW"

# 原始文件名前缀
original_prefix = "ABW_00"
# 重命名的新前缀
new_prefix = "ABW_BV_00"

def move_and_rename_files(src_dir: str, dst_dir: str, old_prefix: str, new_prefix: str) -> None:
    """
    查找源目录中以 old_prefix 开头的文件，将其重命名为 new_prefix 并移动到目标目录。
    """
    # 如果目标目录不存在，创建之
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
        print(f"创建目标文件夹: {dst_dir}")

    # 遍历源目录的所有文件
    for filename in os.listdir(src_dir):
        if filename.startswith(old_prefix):
            # 获取文件扩展名
            file_ext = os.path.splitext(filename)[1]
            # 构建新的文件名
            new_filename = f"{new_prefix}{file_ext}"
            # 构建源文件路径和目标文件路径
            src_path = os.path.join(src_dir, filename)
            dst_path = os.path.join(dst_dir, new_filename)

            # 移动并重命名文件
            shutil.move(src_path, dst_path)
            print(f"移动并重命名文件: {filename} -> {new_filename}")

if __name__ == "__main__":
    move_and_rename_files(src_folder, dst_folder, original_prefix, new_prefix)


# ====== 清除选择.py ======
# -*- coding:utf-8 -*-
"""
作者：23242
日期：2025年06月29日
"""
import arcpy

selected = arcpy.management.SelectLayerByLocation(
    in_layer=[valid_pixel_shp],
    overlap_type="INTERSECT",
    select_features=country_shp,
    search_distance="300 Meters",
    selection_type="NEW_SELECTION"
)
arcpy.management.SelectLayerByAttribute(selected, "CLEAR_SELECTION")

# ====== 获得特定后缀的文件.py ======
import os

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

# 示例使用
folder_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\e_SIDS_Shp\ATG\2015"
suffix = '.shp'  # 指定后缀
files_paths = get_files_absolute_paths(folder_path, suffix)
for path in files_paths:
    print(path)

# ====== 融合.py ======
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


# ====== 裁剪.py ======
import arcpy

def ShpClip(in_features, clip_features, out_feature_class):
    arcpy.env.overwriteOutput = True
    # Process: 成对裁剪 (成对裁剪) (analysis)
    arcpy.analysis.PairwiseClip(
        in_features=in_features,
        clip_features=clip_features,
        out_feature_class=out_feature_class
    )

if __name__ == '__main__':
    # Set local variables
    in_features = "majorrds.shp"
    clip_features = "study_quads.shp"
    out_feature_class = "C:/output/studyarea.shp"

    # Execute Pairwise Clip
    arcpy.env.overwriteOutput = True
    arcpy.analysis.PairwiseClip(in_features, clip_features, out_feature_class)


# ====== 要素转线.py ======
import arcpy

if __name__ == '__main__':
    # Execute Pairwise Clip
    in_features = fr"C:\Users\23042\Desktop\test\1.shp"
    out_feature_class = fr"C:\Users\23042\Desktop\test\1_dissolved.shp",

    arcpy.env.overwriteOutput = True
    arcpy.management.FeatureToLine(in_features, out_feature_class)

# ====== 要素转面.py ======
# Name: FeatureToPolygon_Example2.py
# Description: Use FeatureToPolygon function to construct habitat areas
#              from park boundaries and rivers.

# Import system modules
import arcpy

# Set environment settings
arcpy.env.workspace = "C:/data/parks_analysis.gdb"

# Set local parameters
inFeatures = ["park_boundaries", "rivers"]
outFeatureClass = "c:/output/output.gdb/habitat_areas"

# Use the FeatureToPolygon function to form new areas
arcpy.FeatureToPolygon_management(inFeatures, outFeatureClass)

# ====== 重命名.py ======
import os


def rename_matching_files(folder_path: str, old_prefix: str, new_prefix: str, extensions: list = None):
    """
    批量重命名指定文件夹下匹配特定前缀（和可选扩展名）的文件。

    :param folder_path: 要处理的目标文件夹路径
    :param old_prefix: 原文件名前缀，例如 '_ATG_merge'
    :param new_prefix: 新文件名前缀，例如 '_ATG_merge_CL'
    :param extensions: 可选参数：要处理的扩展名列表，例如 ['.cpg', '.shp.xml']；默认为 None，表示处理所有扩展名
    """
    for filename in os.listdir(folder_path):
        # 获取完整路径
        file_path = os.path.join(folder_path, filename)

        # 确保是文件
        if not os.path.isfile(file_path):
            continue

        # 拆分文件名为 name 和 extension
        name, ext = os.path.splitext(filename)

        # 判断是否匹配命名前缀
        if filename.startswith(old_prefix):
            # 如果指定扩展名列表，则判断当前扩展是否在列表中（注意 .shp.xml 特例）
            if extensions is not None:
                # 如果文件是复合扩展名（如 .shp.xml）
                if filename[len(old_prefix):] in extensions:
                    suffix = filename[len(old_prefix):]
                else:
                    continue  # 不处理该文件
            else:
                # 默认保留所有旧前缀之后的内容
                suffix = filename[len(old_prefix):]

            # 构造新文件名
            new_filename = new_prefix + suffix
            new_file_path = os.path.join(folder_path, new_filename)

            try:
                os.rename(file_path, new_file_path)
                print(f"重命名成功: {filename} → {new_filename}")
            except Exception as e:
                print(f"重命名失败: {filename}，错误信息: {e}")


# ========== 主程序入口 ==========
if __name__ == '__main__':
    # 设置路径和前后缀
    folder = r"C:\Users\23242\Desktop\ATG"
    old_prefix = "_ATG_merge"
    new_prefix = "_ATG_merge_CL"

    # ✅ 选项 1：默认处理所有以 old_prefix 开头的文件
    rename_matching_files(folder, old_prefix, new_prefix)

    # ✅ 选项 2：只处理指定扩展名
    # rename_matching_files(folder, old_prefix, new_prefix, extensions=[".cpg", ".shp.xml"])

