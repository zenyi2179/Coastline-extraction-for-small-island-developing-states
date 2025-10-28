import geopandas as gpd
from shapely.geometry import LineString

# pip install --upgrade fiona geopandas
#    D:\ArcGISPro3\Pro\bin\Python\envs\arcgispro-py3\python.exe -m pip install --upgrade fiona geopandas -i https://pypi.doubanio.com/simple/

# Requirement already satisfied: fiona in c:\users\23242\appdata\roaming\python\python39\site-packages (1.10.1)
# Requirement already satisfied: geopandas in d:\arcgispro3\pro\bin\python\envs\arcgispro-py3\lib\site-packages (0.12.2)

import geopandas as gpd
from shapely.geometry import LineString, MultiLineString

# 定义函数用于输出组件的首尾点，并封闭线段
def process_multilinestring(geometry):
    if isinstance(geometry, MultiLineString):
        for i, component in enumerate(geometry.geoms):  # 使用 .geoms 来迭代 MultiLineString 中的每个 LineString
            coords = list(component.coords)
            start_point = coords[0]
            end_point = coords[-1]
            # # 输出每个组件的首尾点
            # print(f"Component {i + 1}:")
            # print(f"  Start Point (Index: 0): Longitude: {start_point[0]}, Latitude: {start_point[1]}")
            # print(f"  End Point (Index: {len(coords) - 1}): Longitude: {end_point[0]}, Latitude: {end_point[1]}")
            # print('-' * 50)

            # 检查首尾点是否一致，不一致则封闭
            if start_point != end_point:
                # print(f"  Closing Component {i + 1}...")
                coords.append(start_point)  # 封闭
            # else:
            #     print(f"  Component {i + 1} is already closed.")
            # print('-' * 50)
            # 返回封闭后的 LineString
            yield LineString(coords)
    else:
        print("Geometry is not MultiLineString.")
        return None

def fix_subpixel_extraction(input_geojson, output_geojson):
    # 读取 GeoJSON 文件
    # input_geojson = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\k_subPixelWaterlineExtraction\UID_114940_subpixel.geojson"
    gdf = gpd.read_file(input_geojson)

    # 处理所有要素的几何
    for idx, row in gdf.iterrows():
        geometry = row['geometry']
        # print(f"Processing Feature {idx + 1}...")
        if isinstance(geometry, MultiLineString):
            closed_components = list(process_multilinestring(geometry))  # 封闭每个组件
            # 创建封闭后的 MultiLineString 几何
            closed_multilinestring = MultiLineString(closed_components)
            gdf.at[idx, 'geometry'] = closed_multilinestring  # 更新封闭后的几何
        else:
            print(f"Feature {idx + 1} is not a MultiLineString.")

    # 输出结果
    # output_geojson = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\k_subPixelWaterlineExtraction\UID_114940_subpixel_closed.geojson"
    gdf.to_file(output_geojson, driver="GeoJSON")
    print(f"Subpixel_closed MultiLineString output: {output_geojson}")

if __name__ == "__main__":
    fix_subpixel_extraction(input_geojson=r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\k_subPixelWaterlineExtraction\UID_114940_subpixel.geojson",
                            output_geojson=r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\k_subPixelWaterlineExtraction\UID_114940_subpixel_closed.geojson")
