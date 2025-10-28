import os

def list_files_with_extension(folder_path, extension, if_print=0):
    """
    获取指定文件夹中所有以指定扩展名结尾的文件名称，并返回文件名列表。

    参数:
        folder_path (str): 文件夹的路径。
        extension (str): 需要筛选的文件扩展名，例如 '_MNDWI.tif'。

    返回:
        list: 文件名列表，包含所有符合条件的文件名称。
    """
    matching_files = []

    # 检查文件夹是否存在
    if not os.path.isdir(folder_path):
        raise ValueError(f"指定的路径不存在或不是文件夹: {folder_path}")

    # 遍历文件夹中的文件，筛选符合扩展名的文件
    for filename in os.listdir(folder_path):
        if filename.endswith(extension):
            matching_files.append(filename)

    if if_print:
        print(matching_files)

    return matching_files


if __name__ == '__main__':
    # 设置文件夹路径和扩展名
    folder_path = r"E:\_GoogleDrive\SouthChinaSea"
    extension = "_DBNDWI.tif"

    # 获取符合条件的文件名列表
    mndwi_files = list_files_with_extension(folder_path, extension, if_print=1)

    # 去除每个文件名的 "_MNDWI.tif" 后缀
    # records_list_exist = [filename.replace('_MNDWI.tif', '') for filename in records_list_exist_temp]
