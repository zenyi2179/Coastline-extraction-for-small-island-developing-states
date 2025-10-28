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