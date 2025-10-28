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
