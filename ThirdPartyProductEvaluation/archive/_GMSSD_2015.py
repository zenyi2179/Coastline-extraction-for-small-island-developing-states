import arcpy
import os


def extract_data_by_position(in_data, in_boun, out_data):
    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    # Process: 按位置选择图层 (按位置选择图层) (management)
    aim_layer = arcpy.management.SelectLayerByLocation(
        in_layer=[in_data], overlap_type="INTERSECT", select_features=in_boun,
        search_distance="2 Kilometers",  selection_type="NEW_SELECTION")

    # Process: 导出要素 (导出要素) (conversion)
    arcpy.conversion.ExportFeatures(in_features=aim_layer, out_features=out_data)

    # 清除选择
    arcpy.SelectLayerByAttribute_management(aim_layer, "CLEAR_SELECTION")

    print(fr'success: {out_data}')

def selected_valid_data():
    # SIDS 国家位置
    sids_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\boundary\SIDS_boun.shp'

    # GID_boundary
    continent_list = ['Africa', 'Antarctica', 'Asia', 'Europe', 'North_America', 'Oceania', 'South_America']

    for continent in continent_list:
        # 定义文件夹路径
        folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GMSSD_2015\{continent}"
        # 获取文件夹中所有文件
        all_files = os.listdir(folder_path)
        # 筛选出后缀为 .shp 的文件
        shp_files = [file for file in all_files if file.endswith('.shp')]
        # 输出结果
        print("SHAP files:", shp_files)

        for shp in shp_files:
            input_data = os.path.join(folder_path, shp)
            output_folder = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\\' \
                            fr'_ThirdProductEvaluation\GMSSD_2015\_draft'

            output_data = os.path.join(output_folder, shp)
            extract_data_by_position(
                in_data=input_data, in_boun=sids_path, out_data=output_data)

def delete_blank_shp():
    # 定义文件夹路径
    folder_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\GMSSD_2015\_draft"

    # 获取文件夹中所有文件
    all_files = os.listdir(folder_path)

    # 筛选出所有 .shp 文件
    shp_files = [file for file in all_files if file.endswith('.shp')]

    # 遍历所有 .shp 文件
    for shp_file in shp_files:
        shp_file_path = os.path.join(folder_path, shp_file)

        # 获取文件大小
        try:
            file_size = os.path.getsize(shp_file_path)
        except OSError as e:
            print(f"无法获取文件大小: {shp_file_path}, 错误: {e}")
            continue

        # 检查文件大小是否小于 100 字节且大于0字节（排除异常情况）
        if file_size <= 100:
            base_name = os.path.splitext(shp_file)[0]

            # 删除同名的其他后缀的文件
            for file in all_files:
                if file.startswith(base_name) and not file.endswith('.shp'):
                    file_path = os.path.join(folder_path, file)
                    try:
                        os.remove(file_path)
                        print(f"已删除: {file_path}")
                    except Exception as e:
                        print(f"删除文件时出错: {file_path}, 错误: {e}")

            # 删除自身 .shp 文件
            try:
                os.remove(shp_file_path)
                print(f"已删除: {shp_file_path}")
            except Exception as e:
                print(f"删除文件时出错: {shp_file_path}, 错误: {e}")

def main():
    # 筛选有效数据
    selected_valid_data()

    # 筛出无效数据 .shp < 100byte
    # delete_blank_shp()


if __name__ == '__main__':
    main()
