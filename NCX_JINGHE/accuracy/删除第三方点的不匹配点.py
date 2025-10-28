import os.path

import arcpy


def read_txt_to_list(file_path: str) -> list[str]:
    """
    读取文本文件内容为列表
    :param file_path: 文本文件路径
    :return: 行内容组成的字符串列表
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        print(f"[ERROR] 读取文件失败 {file_path}: {e}")
        return []


if __name__ == '__main__':
    list_sids = read_txt_to_list(file_path=fr"SIDS_37.txt")
    # sids_cou_list = ['SGP']
    for sid in list_sids:
        path_work = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation"
        shp_GCL_10 = os.path.join(path_work, fr"{sid}\2010\ThirdPartyDataSource\GCL_SP_{sid}_10.shp")
        shp_GCL_15 = os.path.join(path_work, fr"{sid}\2015\ThirdPartyDataSource\GCL_SP_{sid}_15.shp")
        shp_GCL_20 = os.path.join(path_work, fr"{sid}\2020\ThirdPartyDataSource\GCL_SP_{sid}_20.shp")
        shp_GMSSD = os.path.join(path_work, fr"{sid}\2015\ThirdPartyDataSource\GMSSD_SP_{sid}_15.shp")
        shp_GSV = os.path.join(path_work, fr"{sid}\2015\ThirdPartyDataSource\GSV_SP_{sid}_15.shp")
        shp_OSM = os.path.join(path_work, fr"{sid}\2020\ThirdPartyDataSource\OSM_SP_{sid}_20.shp")

        # list_shp_delete = [shp_GCL_10, shp_GCL_15, shp_GCL_20, shp_GMSSD, shp_GSV, shp_OSM]
        # list_shp_delete = [shp_GCL_10, shp_GCL_15, shp_GCL_20]
        list_shp_delete = [shp_GSV]
        # Process: 按属性选择图层 (按属性选择图层) (management)
        for shp_poi in list_shp_delete:
            layer_select = arcpy.management.SelectLayerByAttribute(
                in_layer_or_view=shp_poi, selection_type="NEW_SELECTION",
                where_clause="NEAR_DIST > 120 Or NEAR_DIST = -1", invert_where_clause=""
            )
            arcpy.management.DeleteRows(layer_select)
            arcpy.management.SelectLayerByAttribute(layer_select, "CLEAR_SELECTION")
            print(shp_poi, fr"deleted")





