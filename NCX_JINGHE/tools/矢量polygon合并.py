import os
import glob
import arcpy

# 设置 arcpy 的覆盖输出选项
arcpy.env.overwriteOutput = True


def read_dbf_column(dbf_file_path, column_index=3):
    """
    读取指定 .dbf 文件的指定列，并返回列数据的列表。

    :param dbf_file_path: 包含 .dbf 文件的路径
    :param column_index: 要提取的列的索引（从 0 开始，默认为第四列）
    :return: 包含指定列数据的列表
    """
    dbf_column_data = []

    print(f"[INFO] 正在处理文件：{dbf_file_path}")

    try:
        # 获取表的字段
        fields = arcpy.ListFields(dbf_file_path)
        field_names = [field.name for field in fields]

        # 检查是否有足够的字段
        if len(field_names) <= column_index:
            print(f"[INFO] 文件 {dbf_file_path} 的列数不足 {column_index + 1} 列，跳过该文件。")
            return dbf_column_data

        # 提取指定列的字段名
        target_column_name = field_names[column_index]

        # 使用 SearchCursor 读取指定列的数据
        dbf_column_data = [row[0] for row in arcpy.da.SearchCursor(dbf_file_path, [target_column_name])]

    except Exception as e:
        print(f"[ERROR] 读取文件 {dbf_file_path} 时出错：{e}")

    return dbf_column_data


def find_matching_shapefiles(shp_folder_path, prefixes):
    """
    在指定文件夹中查找与给定前缀匹配的 .shp 文件，并返回匹配文件的绝对路径列表。

    :param shp_folder_path: 包含 .shp 文件的文件夹路径
    :param prefixes: 包含前缀的列表，用于匹配文件名
    :return: 匹配文件的绝对路径列表
    """
    matching_files = []

    print(f"[INFO] 正在处理文件夹：{shp_folder_path}")

    # 使用 glob 获取文件夹中所有的 .shp 文件
    shp_files = glob.glob(os.path.join(shp_folder_path, "*.shp"))

    # 遍历所有 .shp 文件
    for shp_file in shp_files:
        # 获取文件名（不包含路径）
        file_name = os.path.basename(shp_file)

        # 按 '_' 分割文件名，获取前缀
        file_prefix = file_name.split('_')[0]

        # 检查前缀是否在给定的前缀列表中
        if file_prefix in prefixes:
            # 如果匹配，记录文件的绝对路径
            matching_files.append(shp_file)
            # print(f"[INFO] 匹配文件：{shp_file}")

    return matching_files


def merge_shapefiles(matching_files, output_path):
    """
    合并多个 .shp 文件并保存为一个新的 .shp 文件。

    :param matching_files: 匹配的 .shp 文件路径列表
    :param output_path: 输出合并后的 .shp 文件路径
    """
    print(f"[INFO] 合并文件至 {output_path}")

    # 使用 arcpy 的 Merge_management 工具合并文件
    arcpy.Merge_management(inputs=matching_files, output=output_path, add_source="ADD_SOURCE_INFO")


def select_and_export_shapefiles(input_layer, select_features, output_path, search_distance="1 Kilometers"):
    """
    按位置选择图层并导出为新的 .shp 文件。

    :param input_layer: 输入图层
    :param select_features: 选择特征图层
    :param output_path: 输出 .shp 文件路径
    :param search_distance: 搜索距离，默认为 "1 Kilometers"
    """

    # 使用 arcpy 的 SelectLayerByLocation_management 工具选择图层
    temp_output = arcpy.SelectLayerByLocation_management(
        in_layer=input_layer,
        overlap_type="INTERSECT",
        select_features=select_features,
        search_distance=search_distance,
        selection_type="NEW_SELECTION"
    )

    # 检查选择结果是否有效
    if temp_output is None:
        print(f"[ERROR] 选择图层失败，可能是输入图层或选择特征图层格式不正确。")
        return

    # 使用 arcpy 的 CopyFeatures_management 工具导出选择的图层
    arcpy.CopyFeatures_management(in_features=temp_output, out_feature_class=output_path)
    # print(f"[INFO] 导出文件至：{output_path}")


def main():
    """
    主函数：读取指定文件夹中所有 .dbf 文件的指定列，并查找匹配的 .shp 文件，合并并导出。
    """
    # 定义 .dbf 文件夹路径和列索引
    dbf_folder_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\f_Python\NCX_JINGHE\tools\SIDS_grid_link_37"
    column_index = 5  # 提取第 6 列

    # 定义 .shp 文件夹路径列表和年份
    years = [2010, 2015, 2020]
    # base_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\temp"
    base_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\temp\_reference_geedata"
    base_selection = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\d_SIDS_Boundary\SIDS\AdminDivision"

    # 使用 glob 获取文件夹中所有的 .dbf 文件
    dbf_files = glob.glob(os.path.join(dbf_folder_path, "*.dbf"))

    # 遍历每个年份
    for year in years:
        shp_folder_path = os.path.join(base_path, fr"polygon_map\{year}")
        print(f"[INFO] 处理年份：{year}")

        # 遍历所有 .dbf 文件
        for dbf_file in dbf_files:
            # 读取 .dbf 文件的指定列数据
            name_dbf_file = os.path.basename(dbf_file).split('_')[0]
            dbf_column_data = read_dbf_column(dbf_file, column_index)
            print(f"[INFO] 从文件 {dbf_file} 中提取的列数据：{dbf_column_data}")

            # 查找匹配的 .shp 文件
            matching_files = find_matching_shapefiles(shp_folder_path, dbf_column_data)
            print(f"[INFO] 文件 {dbf_file} 在年份 {year} 匹配的 .shp 文件路径列表：{matching_files}")

            # 定义合并后的 .shp 文件路径
            merge_folder = os.path.join(base_path, "polygon_merge", name_dbf_file)
            os.makedirs(merge_folder, exist_ok=True)
            shp_merge = os.path.join(merge_folder, f"{name_dbf_file}_{year}.shp")

            # 合并匹配的 .shp 文件
            temp_shp_merge = f"in_memory\\temp_merge_{name_dbf_file}_{year}"
            if matching_files:
                merge_shapefiles(matching_files, temp_shp_merge)
                print(f"[INFO] 合并后的文件已保存至：{temp_shp_merge}")
            else:
                print(f"[INFO] 没有匹配的 .shp 文件，跳过合并步骤。")

            # 定义选择和导出的 .shp 文件路径
            shp_selection = os.path.join(base_selection, f"{name_dbf_file}.shp")

            # 按位置选择图层并导出
            if os.path.exists(shp_selection):
                select_and_export_shapefiles(temp_shp_merge, shp_selection, shp_merge)
                print(f"[INFO] 导出文件至：{shp_merge}")
            else:
                print(f"[INFO] 选择特征文件 {shp_selection} 不存在，跳过选择和导出步骤.")


if __name__ == '__main__':
    main()