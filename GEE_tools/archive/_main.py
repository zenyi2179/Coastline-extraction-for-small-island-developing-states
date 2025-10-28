# -*- coding:utf-8 -*-
"""
作者：23242
日期：2024年09月18日
"""
from h_bandInterpolation import downscaling_by_interpolation
from i_cadulateMNDWI import calculate_band_ratio
from j_distinguishRange import extract_by_mask
# from k_subPixelWaterlineExtraction import subpixel_extraction
from k_v2 import subpixel_extraction
# from l_buildShapeFeature import geojson_to_polygon
from l_v2 import geojson_to_polygon
from m_caculateFields import caculate_area_length
import os

def main():
    # 初始 Landsat 8 tif
    # input_tif_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\a_ArcData\GEE_valid\ISID_224209.tif'
    # input_tif_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\c_YY_2020\Africa\UID_130247.tif'

    # 指定的文件夹路径
    folder_path = r'E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\c_YY_2015\temp'

    # 使用os.listdir()来获取文件夹中的所有文件名和子目录名
    entries = os.listdir(folder_path)

    # 打印所有的条目
    for entry in entries:
        input_tif_path = os.path.join(folder_path, entry)
        print(input_tif_path)

        # uid 选择
        uid_is_temp = input_tif_path.split('\\')[-1]
        uid_is_temp2 = uid_is_temp.split('_')[-1]
        uid_is = uid_is_temp2.split('.')[0]
        print(uid_is)

        # 利用插值法降尺度全色（PAN）波段
        zoom_tif = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\h_bandInterpolation\UID_{uid_is}_zoom.tif'
        downscaling_by_interpolation(origin_tif=input_tif_path, zoom_tif=zoom_tif, zoom_ratio=3)

        # 计算水分指数：MNDWI 水体指数（使用 Landsat 的绿色和短波红外 (SWIR) 1 波段）4-SR6 2-SR3
        MNDWI_tif = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\i_cadulateMNDWI\UID_{uid_is}_ND.tif'
        calculate_band_ratio(input_path=zoom_tif, output_path=MNDWI_tif, band1=2, band2=4)

        # 裁剪有效范围
        mask_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\SmallIslands_con_buffer.gdb\Africa_buffer"
        valid_tif = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\j_distinguishRange\UID_{uid_is}_extract.tif"
        extract_by_mask(origin_tif=MNDWI_tif, mask=mask_shp, identifier=uid_is, output_tif=valid_tif)

        # 亚像元边界提取
        subpixel_tif = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\k_subPixelWaterlineExtraction\UID_{uid_is}_subpixel.geojson"
        subpixel_extraction(input_tif=valid_tif, z_values=10.5, subpixel_tif=subpixel_tif)

        shp_mask = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\SmallIslands_continent.gdb\Africa"
        coast_line_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Landsat_output\YY_2015\Africa\UID_{uid_is}_after.shp"
        try:
            # 构建有效面要素
            geojson_to_polygon(extract_geojson=subpixel_tif, shp_mask=shp_mask, identifier=uid_is, tolerance=60, coast_line_shp=coast_line_shp)
            # 整理 shp 的字段及计算几何属性
            caculate_area_length(origin_fields_shp=coast_line_shp)
        except Exception as e:
            print(fr'geojson_to_polygon {uid_is} failed.')


if __name__ == "__main__":
    main()
