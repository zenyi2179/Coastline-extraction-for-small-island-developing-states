import os
import pandas as pd

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
    dbndwi_files = list_files_with_extension(folder_path, extension, if_print=1)

    result_dict = {}
    # 遍历文件名列表，提取键和值
    for file_name in dbndwi_files:
        # 分割文件名以获取键和值
        parts = file_name.split('_')
        key = parts[0]  # 键是文件名的前缀部分
        value = parts[1]  # 值是文件名中的波段信息部分
        result_dict[key] = value

    # 输出构建的字典
    print(result_dict)

    # 将字典转换为DataFrame
    df = pd.DataFrame(list(result_dict.items()), columns=['Location', 'BandCount'])

    # 将DataFrame导出到Excel文件
    df.to_excel('output.xlsx', index=False, engine='openpyxl')


    # 去除每个文件名的 "_MNDWI.tif" 后缀
    # records_list_exist = [filename.replace('_MNDWI.tif', '') for filename in records_list_exist_temp]
