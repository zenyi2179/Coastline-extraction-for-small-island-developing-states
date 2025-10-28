# -*- coding:utf-8 -*-
import os
import math
from dbfread import DBF


def determine_map_position(longitude, latitude, if_print=1):
    """
    根据给定的经度和纬度确定地图上的位置，并返回一个格式化的字符串。

    参数:
    - longitude (float): 经度值
    - latitude (float): 纬度值
    - if_print (int): 是否打印结果，默认为1（打印）

    返回:
    - str: 格式化的地图位置字符串

    示例:
    - determine_map_position(-73.997826, 40.744754)
    coordinate [-73.997826, 40.744754] translate to: 74W40Nr.
    """

    # 初始化经度的整数部分
    abs_var_lon = int(abs(longitude - 1)) if longitude < 0 else int(abs(longitude))
    var_lon = -abs_var_lon if longitude < 0 else abs_var_lon

    # 初始化纬度的整数部分
    abs_var_lat = int(abs(latitude - 1)) if latitude < 0 else int(abs(latitude))
    var_lat = -abs_var_lat if latitude < 0 else abs_var_lat

    # 确定东西方向标识符
    var_WE = 'W' if longitude < 0 else 'E'

    # 确定南北方向标识符
    var_NS = 'N' if latitude > 0 else 'S'

    # 根据输入值和整数部分计算左右方向标识符
    var_lr = 'l' if longitude < var_lon + 0.5 else 'r'

    # 根据输入值和整数部分计算上下方向标识符
    var_ub = 'b' if latitude < var_lat + 0.5 else 'u'

    # 格式化输出为所需的字符串格式
    map_position = fr'{abs_var_lon}{var_WE}{abs_var_lat}{var_NS}{var_lr}{var_ub}'

    # 如果 if_print 为 1，则打印结果
    if if_print:
        print(fr"coordinate [{longitude}, {latitude}] translate to: {map_position}.")

    return map_position


def get_grid_coordinates(longitude, latitude):
    # 计算经度的网格左下角坐标
    grid_longitude = math.floor(longitude * 2) / 2
    # 计算纬度的网格左下角坐标
    grid_latitude = math.floor(latitude * 2) / 2

    return grid_longitude, grid_latitude


def read_dbf_to_list(dbf_path, if_print=0):
    """
    读取 DBF 文件并将内容存储为二维列表。

    参数:
    dbf_path (str): DBF 文件的路径。
    if_print (int): 是否打印二维列表的开关，0表示不打印，1表示打印。

    返回:
    list_of_records (list): 二维列表，每个子列表代表一条记录。
    """
    list_of_records = []
    dbf = DBF(dbf_path, encoding='utf-8')  # 打开 DBF 文件并设置编码为 'utf-8'

    # 获取并打印 DBF 文件的字段名称，即表头
    # print("Field names:", [field.name for field in dbf.fields])

    # 遍历 DBF 文件中的每条记录
    for record in dbf:
        # 将每条记录的值转换为列表，并添加到二维列表中
        list_of_records.append(list(record.values()))

    # 根据 if_print 参数决定是否打印二维列表
    if if_print:
        print("Records list:")
        print(list_of_records)

    return list_of_records


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



def main():
    pass


if __name__ == '__main__':
    main()
