import os
import arcpy
arcpy.env.overwriteOutput = True  # 允许覆盖输出文件
from worktools import read_txt_to_list  # 从worktools模块导入读取文本文件到列表的函数

# 定义一个函数，用于合并SIDs的Shapefile
def merge_sids_shp(path_dataset, list_sids):
    # 定义输出路径
    path_output = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\_third_party_dataset'
    list_sids_shp = []  # 用于存储每个SID的Shapefile路径
    name_dataset = os.path.basename(path_dataset)  # 获取数据集的名称

    # 遍历每个SID
    for sid in list_sids:
        # print(f"正在处理SID: {sid}")  # 提示当前处理的SID
        shp_path = os.path.join(path_dataset, sid, fr'_{sid}_merge.shp')  # 构造Shapefile的路径
        temp_shp_path = fr'in_memory\_temp_{sid}_merge'  # 创建一个临时内存路径

        # 复制Shapefile到临时内存
        arcpy.management.CopyFeatures(
            in_features=shp_path, out_feature_class=temp_shp_path)
        # print(f"已复制SID {sid} 的Shapefile到临时内存")  # 提示复制完成

        # 为Shapefile添加字段并计算值
        shp_add_path = arcpy.management.CalculateFields(
            in_table=temp_shp_path, expression_type="PYTHON3",
            fields=[["country", fr"'{sid}'", "", "TEXT"]]
        )[0]
        # print(f"已为SID {sid} 的Shapefile添加字段并计算值")  # 提示字段添加和计算完成

        list_sids_shp.append(shp_add_path)  # 将处理后的Shapefile路径添加到列表

    # 构造最终输出的Shapefile路径
    shp_output = os.path.join(path_output, fr'{name_dataset}_37.shp')
    # print(f"正在合并所有SID的Shapefile到: {shp_output}")  # 提示合并操作

    # 合并所有Shapefile
    arcpy.management.Merge(list_sids_shp, shp_output)
    print(f"合并完成，输出文件路径: {shp_output}")  # 提示合并完成

# 主函数
def main():
    # 定义SIDs文件路径
    path_sids = 'SIDS_37.txt'
    # 定义第三方数据集的路径
    path_third_data = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation'
    # 读取SIDs列表
    list_sids = read_txt_to_list(path_sids)
    print("SIDs列表已加载")  # 提示SIDs列表加载完成

    # 定义第三方数据集的名称列表
    list_third_dataset = [
        'GSV', 'GMSSD_2015', 'OSM',
        'GCL_FCS30_10', 'GCL_FCS30_15', 'GCL_FCS30_20',
    ]

    # 遍历每个第三方数据集
    for third_data in list_third_dataset:
        print(f"正在处理第三方数据集: {third_data}")  # 提示当前处理的数据集
        path = fr'{path_third_data}\{third_data}'  # 构造数据集路径
        merge_sids_shp(
            path_dataset=path,
            list_sids=list_sids
        )
        print(f"第三方数据集 {third_data} 处理完成")  # 提示当前数据集处理完成

if __name__ == '__main__':
    main()
    print("程序运行完成")  # 提示程序运行完成