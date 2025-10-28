import os
import arcpy
from Z_面转栅格 import vector_to_raster
from Z_TiftoJson import subpixel_extraction
from Z_Json转线 import geojson_to_shp
from Z_线转面 import line_to_polygon

def main():
    sids_cou_list = ["SYC",]
    for sids_cou in sids_cou_list:
        # for year in [2000, 2010, 2020]:
        for year in [2015]:
            # 初始化变量
            end_add_list = ['_1', '_2', '_3', '_4', '_5', '_6', '_7', ]
            for end_add in end_add_list[0:8]:
                # end_add = end_add_list[1]
                input_origin = fr'C:\Users\23242\Desktop\check\250412\{sids_cou}\{sids_cou}_{str(year)[-2:]}{end_add}.shp'

                # input_origin = fr"E:\_OrderingProject\F_IslandsBoundaryChange\g_QGIS\c_SIDS_no_holes\{sids_cou}\{sids_cou}_{str(year)[-2:]}.shp"

                to_raster = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\h_SIDS_Tif\{sids_cou}\{sids_cou}_{str(year)[-2:]}{end_add}.tif'
                to_json = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Geojson\{sids_cou}\{sids_cou}_{str(year)[-2:]}{end_add}.geojson"
                to_line = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\i_SIDS_Line\{sids_cou}\{sids_cou}_{str(year)[-2:]}{end_add}.shp"
                to_polygon = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\j_SIDS_Polygon\{sids_cou}\{sids_cou}_{str(year)[-2:]}{end_add}.shp"

                # Z_面转栅格
                os.makedirs(name=fr"E:\_OrderingProject\F_IslandsBoundaryChange\g_QGIS\h_SIDS_Tif\{sids_cou}",
                            exist_ok=True)
                vector_to_raster(
                    vector_path=input_origin,
                    raster_path=to_raster,
                    reference_raster=r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\bandInterpolation"
                                     r"\_zoom.tif",
                    value=10)

                # Z_TiftoJson
                os.makedirs(name=fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Geojson\{sids_cou}",
                            exist_ok=True)
                subpixel_extraction(input_tif=to_raster, z_values=0, subpixel_tif=to_json)

                # Z_Json转线
                os.makedirs(name=fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\i_SIDS_Line\{sids_cou}",
                            exist_ok=True)
                geojson_to_shp(input_geojson=to_json, output_shp=to_line)

                # Z_线转面
                os.makedirs(name=fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\j_SIDS_Polygon\{sids_cou}",
                            exist_ok=True)
                line_to_polygon(input_shp=to_line, output_shp=to_polygon)


if __name__ == '__main__':
    main()