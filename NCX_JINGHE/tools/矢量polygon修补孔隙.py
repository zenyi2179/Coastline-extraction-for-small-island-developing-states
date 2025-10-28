import os
import arcpy
import geopandas as gpd

from shapely.geometry import Polygon


def remove_polygon_holes(input_shapefile, output_shapefile):
    """
    读取 Shapefile 面文件，去除多边形中的空洞（内部环），并保存为新的 Shapefile。

    :param input_shapefile: 输入的 Shapefile 文件路径
    :param output_shapefile: 输出的 Shapefile 文件路径
    """
    try:
        # 读取数据
        geo_dataframe = gpd.read_file(input_shapefile)

        # 遍历几何对象并去除空洞
        def fix_geometry(geometry):
            if geometry.geom_type == 'Polygon':
                return Polygon(geometry.exterior)
            elif geometry.geom_type == 'MultiPolygon':
                return type(geometry)([Polygon(p.exterior) for p in geometry.geoms])
            return geometry

        geo_dataframe['geometry'] = geo_dataframe['geometry'].apply(fix_geometry)

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_shapefile), exist_ok=True)

        # 保存结果
        geo_dataframe.to_file(output_shapefile)

        # Process: 计算几何属性 (计算几何属性) (management)
        arcpy.management.CalculateGeometryAttributes(
            in_features=output_shapefile,
            geometry_property=[["area_geo", "AREA_GEODESIC"], ["leng_geo", "PERIMETER_LENGTH_GEODESIC"]],
            length_unit="KILOMETERS",
            area_unit="SQUARE_KILOMETERS")

        print(f"[INFO] 文件 {output_shapefile} 空洞修复完成")

    except Exception as error:
        print(f"[ERROR] 修复 {input_shapefile} 时出错: {error}")


if __name__ == '__main__':
    from worktools import read_txt_to_list

    """
    主函数，用于批量处理多个岛屿的多边形数据，去除空洞。
    """
    base_workspace = r'E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\temp'

    list_sids = read_txt_to_list('SIDS_37.txt')  # 读取岛屿列表
    list_years = [2010, 2015, 2020]  # 年份列表

    # 测试用
    # list_sids = ['COM', 'DOM', 'STP', 'FJI']
    list_sids = ['STP']
    list_years = [2020]

    for island_code in list_sids:
        for year in list_years:
            # 输入 Shapefile 路径
            input_shapefile_path = os.path.join(
                base_workspace,
                "polygon_merge_smooth",
                island_code,
                f"{island_code}_smooth_{year}.shp"
            )

            # 输出 Shapefile 路径
            output_shapefile_path = os.path.join(
                base_workspace,
                "polygon_merge_fixed",
                island_code,
                f"{island_code}_fixed_{year}.shp"
            )

            # 执行空洞修复
            remove_polygon_holes(input_shapefile_path, output_shapefile_path)
