
# ====== ABC.py ======
"""
├── main()                      # 总控函数，调用 a/b/c 的流程
│
├── tif_preprocessing.py       # 来自代码块 a（预处理 TIF）
├── raster_to_vector.py        # 来自代码块 b（TIF 转矢量 + 矢量筛选）
├── vector_fix_and_rasterize.py# 来自代码块 c（修复矢量并重转栅格）
│
└── utils.py                   # 公共函数（读取 txt/dbf，获取文件路径）

"""
import arcpy
import os
from pathlib import Path
import numpy as np
import rasterio
import geopandas as gpd
from dbfread import DBF
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from rasterio.features import shapes, rasterize
from scipy.ndimage import maximum_filter, label, binary_fill_holes

arcpy.env.overwriteOutput = True

# ========== utils ==========
def read_txt_to_list(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        print(f"错误：读取文件 {file_path} 失败 - {str(e)}")
        return []

def get_files_absolute_paths(folder_path, suffix=None):
    return [
        os.path.abspath(os.path.join(root, file))
        for root, _, files in os.walk(folder_path)
        for file in files
        if suffix is None or file.endswith(suffix)
    ]

def read_dbf_to_list(dbf_path, if_print=0):
    list_of_records = []
    dbf = DBF(dbf_path, encoding='utf-8')
    for record in dbf:
        list_of_records.append(list(record.values()))
    if if_print:
        print("Records list:", list_of_records)
    return list_of_records

# ========== A. TIF预处理 ==========
def extract_pixels_gt_threshold(data, threshold=5.0, nodata_value=0.0):
    return np.where(data > threshold, data, nodata_value)

def filter_by_local_max(data, window_size=31, max_threshold=10.0, nodata_value=0.0):
    local_max = maximum_filter(data, size=window_size, mode='nearest')
    return np.where(local_max < max_threshold, nodata_value, data)

def remove_small_clusters(data, min_cluster_size=4, nodata_value=0.0):
    mask = data != 0
    structure = np.array([[0,1,0],[1,1,1],[0,1,0]])
    labeled, _ = label(mask, structure=structure)
    counts = np.bincount(labeled.ravel())
    keep_mask = np.isin(labeled, np.where(counts >= min_cluster_size)[0])
    return np.where(keep_mask, data, nodata_value)

def fill_internal_holes(data, fill_value=20.0, max_hole_size=500):
    foreground = data != 0
    filled = binary_fill_holes(foreground)
    holes = filled & (~foreground)
    labeled, _ = label(holes, structure=np.ones((3, 3)))
    counts = np.bincount(labeled.ravel())
    valid_labels = np.where((counts > 0) & (counts <= max_hole_size))[0]
    mask_fill = np.isin(labeled, valid_labels)
    data[mask_fill] = fill_value
    return data

def filter_clusters_by_median(data, threshold=10.0, connectivity=8):
    mask = data != 0
    # structure = np.ones((3,3)) if connectivity == 8 else np.array([[0,1,0],[1,1,1],[0,1,0]])
    structure = np.ones((3,3)) if connectivity == 8 else np.array([[1,1,1],[1,1,1],[1,1,1]])
    labeled, num_features = label(mask, structure=structure)
    for region_label in range(1, num_features + 1):
        region_mask = labeled == region_label
        if np.median(data[region_mask]) < threshold:
            data[region_mask] = 0
    return data

def tif_preprocessing(extract_threshold, filter_threshold, tif_input, tif_output):
    with rasterio.open(tif_input) as src:
        data = src.read(1)
        profile = src.profile
    data = extract_pixels_gt_threshold(data, extract_threshold)
    data = filter_by_local_max(data, 31, filter_threshold)
    data = remove_small_clusters(data, 4)
    data = fill_internal_holes(data, 20.0)
    data = filter_clusters_by_median(data, filter_threshold)
    profile.update(dtype=rasterio.float32, count=1, nodata=0.0)
    with rasterio.open(tif_output, 'w', **profile) as dst:
        dst.write(data.astype(np.float32), 1)
    print(f"✅ 输出预处理结果：{tif_output}")

# ========== B. TIF -> 矢量 & 按国家筛选 ==========
def tif_to_merged_regions_shp(input_tif, output_shp, threshold=0.0):
    with rasterio.open(input_tif) as src:
        data = src.read(1)
        transform = src.transform
        crs = src.crs
        binary_mask = (data > threshold).astype(np.uint8)
        labeled_array, num_features = label(binary_mask)
        if num_features == 0:
            print(f"⚠️ 无连通区域: {input_tif}")
            return
        shapes_gen = shapes(labeled_array, mask=binary_mask, transform=transform)
        geometries = [{"geometry": shape(geom), "properties": {"id": int(val)}}
                      for geom, val in shapes_gen if val != 0]
        gdf = gpd.GeoDataFrame.from_features(geometries, crs=crs)
        gdf.to_file(output_shp, driver='ESRI Shapefile')
        print(f"✅ 矢量输出：{output_shp}")

def select_valid_polygons(valid_pixel_shp, country_shp, output_shp):
    os.makedirs(os.path.dirname(output_shp), exist_ok=True)
    selected = arcpy.management.SelectLayerByLocation(
        in_layer=[valid_pixel_shp],
        overlap_type="INTERSECT",
        select_features=country_shp,
        search_distance="300 Meters",
        selection_type="NEW_SELECTION"
    )
    arcpy.conversion.ExportFeatures(in_features=selected, out_features=output_shp)
    arcpy.management.SelectLayerByAttribute(selected, "CLEAR_SELECTION")
    print(f"✅ 选中有效矢量：{output_shp}")

# ========== C. 修复矢量 + 栅格化 ==========
def fix_holes_in_shp(input_shp, output_shp, min_area=0.0):
    gdf = gpd.read_file(input_shp)
    fixed_geoms = []
    for geom in gdf.geometry:
        if geom.geom_type == 'Polygon':
            interiors = [i for i in geom.interiors if Polygon(i).area > min_area]
            fixed_geoms.append(Polygon(geom.exterior, interiors))
        elif geom.geom_type == 'MultiPolygon':
            fixed_polygons = []
            for poly in geom.geoms:
                interiors = [i for i in poly.interiors if Polygon(i).area > min_area]
                fixed_polygons.append(Polygon(poly.exterior, interiors))
            fixed_geoms.append(MultiPolygon(fixed_polygons))
        else:
            fixed_geoms.append(geom)
    gdf.geometry = fixed_geoms
    gdf.to_file(output_shp)
    print(f"✅ 修复完成：{output_shp}")

def vector_to_raster(vector_path, raster_path, reference_raster, value=30):
    vector_data = gpd.read_file(vector_path)
    with rasterio.open(reference_raster) as ref:
        pixel_size = ref.res[0]
    bounds = vector_data.total_bounds
    width = int((bounds[2] - bounds[0]) / pixel_size)
    height = int((bounds[3] - bounds[1]) / pixel_size)
    transform = rasterio.Affine(pixel_size, 0, bounds[0], 0, -pixel_size, bounds[3])
    rasterized = rasterize(
        [(mapping(geom), value) for geom in vector_data.geometry],
        out_shape=(height, width),
        transform=transform,
        fill=0, dtype='uint8'
    )
    with rasterio.open(raster_path, 'w', driver='GTiff', height=height, width=width,
                       count=1, dtype='uint8', crs=vector_data.crs,
                       transform=transform, nodata=0) as dst:
        dst.write(rasterized, 1)
    print(f"✅ 栅格保存至：{raster_path}\n")

# ========== MAIN 调度 ==========
def main():
    # main_path
    path_tif_gee = fr"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData"
    path_work = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp"
    path_sids_boundary = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\j_SIDS_Polygon"
    path_tif_reference = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\_draft\_reference_raster.tif"
    # work
    list_year = ['2010', '2015', '2020']
    list_sids = read_txt_to_list("draft.txt")
    # for year in ['2020']:
    for year in list_year:
        for sids in ['PNG']:
        # for sids in list_sids:
            dbf_path = fr".\SIDS_grid_link\{sids}_grid.dbf"
            list_maps = [rec[4] for rec in read_dbf_to_list(dbf_path)]
            for map_name in list_maps:
                try:
                    tif_input = os.path.join(
                        path_tif_gee, fr'SIDs_Grid_Y{year[-2:]}', fr'{map_name}_ls578_Index.tif')
                    tif_output = os.path.join(
                        path_work, 'a_tif_GeeData', fr'{sids}\{year}\{sids}_{map_name}.tif')
                    os.makedirs(os.path.dirname(tif_output), exist_ok=True)
                    threshold = {'2010': 1.0, '2015': 5.0, '2020': 9.0}.get(year, 0.0)
                    tif_preprocessing(
                        extract_threshold=threshold, filter_threshold=30, tif_input=tif_input, tif_output=tif_output)

                    temp_shp = os.path.join(
                        path_work, '_draft', fr'{sids}_{map_name}.shp')
                    shp_sids_boundary = os.path.join(
                        path_sids_boundary, fr'{sids}\{sids}_20.shp')
                    out_shp = os.path.join(
                        path_work, 'b_shp_GeeData', fr'{sids}\{year}\{sids}_{map_name}.shp')
                    tif_to_merged_regions_shp(input_tif=tif_output, output_shp=temp_shp)
                    select_valid_polygons(
                        valid_pixel_shp=temp_shp, country_shp=shp_sids_boundary, output_shp=out_shp)

                    shp_fixed = os.path.join(
                        path_work, 'c_shp_fixed', fr'{sids}\{year}\{sids}_{map_name}.shp')
                    os.makedirs(os.path.dirname(shp_fixed), exist_ok=True)
                    fix_holes_in_shp(input_shp=out_shp, output_shp=shp_fixed)

                    tif_fixed = os.path.join(
                        path_work, 'd_tif_fixed', fr'{sids}\{year}\{sids}_{map_name}.tif')
                    os.makedirs(os.path.dirname(tif_fixed), exist_ok=True)
                    vector_to_raster(shp_fixed, tif_fixed, reference_raster=path_tif_reference)
                except Exception as e:
                    pass

if __name__ == '__main__':
    main()


# ====== DEF.py ======
import arcpy
import os
import pandas as pd
import geopandas as gpd
import rasterio
import numpy as np
import xarray as xr
import rioxarray
from dbfread import DBF
from shapely.geometry import LineString, MultiLineString, Polygon, MultiPolygon, shape, mapping
from shapely.ops import unary_union
from rasterio import Affine
from dea_tools.spatial import subpixel_contours

arcpy.env.overwriteOutput = True
# -------------------------
# 通用工具函数 Utils
# -------------------------
def read_txt_to_list(file_path: str) -> list[str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines()]
    except Exception as e:
        print(f"[ERROR] Failed to read TXT file: {file_path} - {str(e)}")
        return []

def get_files_absolute_paths(folder_path, suffix=None):
    result = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if suffix is None or file.endswith(suffix):
                result.append(os.path.abspath(os.path.join(root, file)))
    return result

# -------------------------
# D - 子像素边界提取模块
# -------------------------
def add_zero_buffer(input_tif, output_tif, buffer_size=1):
    with rasterio.open(input_tif) as src:
        profile = src.profile.copy()
        width, height = src.width, src.height
        new_width = width + 2 * buffer_size
        new_height = height + 2 * buffer_size
        new_transform = src.transform * Affine.translation(-buffer_size, -buffer_size)
        profile.update({'width': new_width, 'height': new_height, 'transform': new_transform})
        new_data = np.zeros((src.count, new_height, new_width), dtype=src.dtypes[0])
        original_data = src.read()
        new_data[:, buffer_size:buffer_size + height, buffer_size:buffer_size + width] = original_data
        with rasterio.open(output_tif, 'w', **profile) as dst:
            dst.write(new_data)
    print(f"[INFO] Added zero buffer to: {output_tif}")

def process_multilinestring(geometry, x_offset, y_offset):
    if isinstance(geometry, MultiLineString):
        for component in geometry.geoms:
            coords = [(x + x_offset, y + y_offset) for x, y in component.coords]
            if coords[0] != coords[-1]:
                coords.append(coords[0])
            yield LineString(coords)
    else:
        print("[WARN] Geometry is not MultiLineString.")
        return None

def fix_subpixel_extraction(input_geojson, output_geojson, x_offset, y_offset):
    gdf = gpd.read_file(input_geojson)
    for idx, row in gdf.iterrows():
        if isinstance(row.geometry, MultiLineString):
            fixed_lines = list(process_multilinestring(row.geometry, x_offset, y_offset))
            gdf.at[idx, 'geometry'] = MultiLineString(fixed_lines)
    gdf.to_file(output_geojson, driver="GeoJSON")
    print(f"[INFO] Closed MultiLineString saved to: {output_geojson}")

def subpixel_extraction(input_tif, z_values, subpixel_geojson):
    temp_zero_buffer = os.path.join(os.path.dirname(subpixel_geojson), 'temp_zero_buffer.tif')
    add_zero_buffer(input_tif, temp_zero_buffer, buffer_size=1)

    with rasterio.open(temp_zero_buffer) as src:
        raster_data = src.read(1)
        transform = src.transform
        crs = src.crs
        height, width = raster_data.shape
        x_offset = transform[0] / 2
        y_offset = transform[4] / 2
        x_coords = [transform * (col, 0) for col in range(width)]
        y_coords = [transform * (0, row) for row in range(height)]
        data_array = xr.DataArray(
            raster_data,
            coords=[[y[1] for y in y_coords], [x[0] for x in x_coords]],
            dims=["y", "x"],
            attrs={'crs': str(crs), 'transform': transform}
        ).rio.write_crs("EPSG:4326", inplace=True)

    temp_geojson = subpixel_geojson.replace('.geojson', '_temp.geojson')
    subpixel_contours(data_array, z_values=z_values, output_path=temp_geojson)
    fix_subpixel_extraction(temp_geojson, subpixel_geojson, x_offset, y_offset)

# -------------------------
# E - GeoJSON 转面
# -------------------------
def geojson_to_shp(input_geojson, output_shp):
    # gdf = gpd.read_file(input_geojson)
    # gdf.to_file(output_shp, driver='ESRI Shapefile')
    temp_line = fr"in_memory\geojson_to_shp"
    arcpy.conversion.JSONToFeatures(
        in_json_file=input_geojson, out_features=temp_line, geometry_type='POLYLINE')
    arcpy.management.FeatureToLine(in_features=temp_line, out_feature_class=output_shp)
    print(f"[INFO] Converted GeoJSON to Shapefile: {output_shp}")

def line_to_polygon(input_shp, output_shp):
    temp_shp = "in_memory/temp_line"
    arcpy.env.overwriteOutput = True
    arcpy.management.FeatureToPolygon([input_shp], temp_shp)
    arcpy.management.Dissolve(
        in_features=temp_shp,
        out_feature_class=output_shp,
        dissolve_field=[],
        multi_part="SINGLE_PART",
        unsplit_lines="DISSOLVE_LINES"
    )
    print(f"[INFO] Converted Line to Polygon: {output_shp}")

# -------------------------
# F - 面合并与修复
# -------------------------
def merge_shapefiles_gpd(input_folder, output_shp, extra_shp):
    gdfs = []
    for fname in os.listdir(input_folder):
        if fname.endswith('.shp'):
            gdf = gpd.read_file(os.path.join(input_folder, fname))
            gdfs.append(gdf)
    if os.path.exists(extra_shp):
        gdf_extra = gpd.read_file(extra_shp)
        gdfs.append(gdf_extra)
    merged = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=gdfs[0].crs)
    dissolved = unary_union(merged.geometry)
    gdf_out = gpd.GeoDataFrame(geometry=[dissolved], crs=merged.crs)
    os.makedirs(os.path.dirname(output_shp), exist_ok=True)
    gdf_out.to_file(output_shp)
    print(f"[INFO] Merged polygons to: {output_shp}")

def fix_shapefiles(shp_input, shp_fixed):
    arcpy.env.overwriteOutput = True
    temp_line = "in_memory/shp_temp_line"
    temp_poly = "in_memory/shp_temp_polygon"
    arcpy.management.FeatureToLine([shp_input], temp_line)
    arcpy.management.FeatureToPolygon(temp_line, temp_poly)
    arcpy.analysis.PairwiseDissolve(temp_poly, shp_fixed, multi_part="SINGLE_PART")
    print(f"[INFO] Fixed geometry and saved to: {shp_fixed}")

# -------------------------
# 主调度函数 main()
# -------------------------
def main():
    base_dir = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp"
    list_year = ['2010', '2015', '2020']
    list_sids = read_txt_to_list("draft.txt")

    # for year in ['2015']:
    for year in list_year:
        for sids in ['SUR']:  # 或 list_sids
        # for sids in list_sids:  # 或 list_sids
            print(f"\n[INFO] === 处理国家: {sids}, 年份: {year} ===")

            # --- D 阶段：子像素提取 ---
            tif_folder = os.path.join(base_dir, "d_tif_fixed", sids, year)
            geojson_out_folder = os.path.join(base_dir, "e_geojson", sids, year)
            os.makedirs(geojson_out_folder, exist_ok=True)
            for tif in get_files_absolute_paths(tif_folder, ".tif"):
                geojson_out = os.path.join(geojson_out_folder, os.path.splitext(os.path.basename(tif))[0] + ".geojson")
                subpixel_extraction(tif, z_values=0, subpixel_geojson=geojson_out)

            # --- E 阶段：GeoJSON → 面 ---
            line_folder = os.path.join(base_dir, "f_shp_line", sids, year)
            poly_folder = os.path.join(base_dir, "g_shp_polygon", sids, year)
            os.makedirs(line_folder, exist_ok=True)
            os.makedirs(poly_folder, exist_ok=True)

            for geojson in get_files_absolute_paths(geojson_out_folder, ".geojson"):
                line_shp = os.path.join(line_folder, os.path.splitext(os.path.basename(geojson))[0] + ".shp")
                # 核心检查线
                geojson_to_shp(geojson, line_shp)
                poly_shp = os.path.join(poly_folder, os.path.basename(line_shp))
                line_to_polygon(line_shp, poly_shp)

            # --- F 阶段：面合并与修复 ---
            input_folder = poly_folder
            # 删除temp文件
            [os.remove(os.path.join(input_folder, f)) for f in os.listdir(input_folder) if 'temp' in f and os.path.isfile(os.path.join(input_folder, f))]
            [os.remove(os.path.join(line_folder, f)) for f in os.listdir(line_folder) if 'temp' in f and os.path.isfile(os.path.join(line_folder, f))]
            extra_shp = os.path.join(base_dir, "g_shp_polygon", sids, f"{sids}_add.shp")
            merged_shp = os.path.join(base_dir, "_draft", f"{sids}_{year}.shp")
            fixed_shp = os.path.join(base_dir, "h_shp_merge", sids, f"{sids}_{year}.shp")

            merge_shapefiles_gpd(input_folder, merged_shp, extra_shp)
            os.makedirs(os.path.dirname(fixed_shp), exist_ok=True)
            fix_shapefiles(merged_shp, fixed_shp)


if __name__ == "__main__":
    main()


# ====== _.py ======
import os

import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon


def fix_holes_in_shp(input_shp: str, output_shp: str, min_area: float = 0.0) -> None:
    """
    修复Shapefile面要素中的空洞。

    参数:
        input_shp (str): 输入Shapefile路径
        output_shp (str): 输出Shapefile路径
        min_area (float): 保留的最小空洞面积，小于此面积的空洞将被填充
    """
    # 读取Shapefile
    gdf = gpd.read_file(input_shp)

    # 处理每个几何对象
    fixed_geometries = []
    for geom in gdf.geometry:
        if geom.geom_type == 'Polygon':
            # 处理单个多边形
            exterior = geom.exterior
            interiors = [interior for interior in geom.interiors if interior.area > min_area]
            fixed_geom = Polygon(exterior, interiors)
            fixed_geometries.append(fixed_geom)
        elif geom.geom_type == 'MultiPolygon':
            # 处理多个多边形
            fixed_polygons = []
            for poly in geom.geoms:
                exterior = poly.exterior
                interiors = [interior for interior in poly.interiors if interior.area > min_area]
                fixed_poly = Polygon(exterior, interiors)
                fixed_polygons.append(fixed_poly)
            fixed_geom = MultiPolygon(fixed_polygons)
            fixed_geometries.append(fixed_geom)
        else:
            # 非面要素直接添加
            fixed_geometries.append(geom)

    # 更新几何列
    gdf.geometry = fixed_geometries

    # 保存结果
    gdf.to_file(output_shp)
    print(f"已修复空洞并保存至: {output_shp}")

input_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\b_shp_GeeData\ATG\2010\ATG_62W17Nlb.shp"
output_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\c_shp_fixed\ATG\2010\ATG_62W17Nlb.shp"
os.makedirs(os.path.dirname(output_shp), exist_ok=True)
fix_holes_in_shp(input_shp, output_shp)

# ====== __.py ======
import os
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from shapely.geometry import mapping


def vector_to_raster(vector_path, raster_path, reference_raster, value=10):
    """
    将矢量文件转换为栅格，并赋值为指定的值。

    :param vector_path: 输入矢量文件路径 (Shapefile)
    :param raster_path: 输出栅格文件路径
    :param reference_raster: 参考栅格文件路径，仅用于获取像元大小信息
    :param value: 转换后的栅格像元值
    """
    try:
        # 读取矢量数据
        vector_data = gpd.read_file(vector_path)

        # 获取矢量数据的 CRS 和几何边界
        crs = vector_data.crs
        bounds = vector_data.total_bounds  # 获取矢量数据的边界框

        # 读取参考栅格的像元大小信息
        with rasterio.open(reference_raster) as ref_src:
            pixel_size = ref_src.res[0]  # 假设像元大小在 x 和 y 方向相同

        # 计算输出栅格的宽度和高度
        width = int((bounds[2] - bounds[0]) / pixel_size)
        height = int((bounds[3] - bounds[1]) / pixel_size)

        # 计算仿射变换矩阵
        transform = rasterio.Affine(pixel_size, 0, bounds[0], 0, -pixel_size, bounds[3])

        # 获取矢量文件的几何数据
        geometries = vector_data.geometry

        # 创建栅格化的图像
        rasterized_data = rasterize(
            [(mapping(geometry), value) for geometry in geometries],
            out_shape=(height, width),
            transform=transform,
            fill=0,  # 设置非矢量区域的值为 0
            dtype='uint8'
        )

        # 确保输出文件的目录存在
        output_dir = os.path.dirname(raster_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 保存为输出栅格文件
        with rasterio.open(
                raster_path,
                'w',
                driver='GTiff',
                height=height,
                width=width,
                count=1,
                dtype=rasterized_data.dtype,
                crs=crs,
                transform=transform,
                nodata=0  # 设置空值为 0
        ) as dst:
            dst.write(rasterized_data, 1)

        print(f"Tif saved as: {raster_path}")

    except Exception as e:
        print(f"发生错误: {e}")


def read_txt_to_list(file_path: str) -> list[str]:
    """读取文本文件内容并返回一个列表"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        print(f"错误：读取文件 {file_path} 失败 - {str(e)}")
        return []

def get_files_absolute_paths(folder_path, suffix=None):
    """
    获取指定文件夹下所有指定后缀的文件的绝对路径名称

    :param folder_path: 指定文件夹的路径
    :param suffix: 文件后缀（可选），如 '.shp'。如果不指定，则获取所有文件的路径
    :return: 指定后缀的文件的绝对路径名称列表
    """
    files_paths = []
    # 遍历指定文件夹
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 如果指定了后缀，则判断文件后缀是否匹配
            if suffix is None or file.endswith(suffix):
                # 获取文件的绝对路径并添加到列表中
                files_paths.append(os.path.abspath(os.path.join(root, file)))
    return files_paths

def main():# 初始化处理的国家和年份
    vector_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\c_shp_fixed\ATG\2010\ATG_62W17Nlb.shp"
    # 新建文件夹
    tif_fixed = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\d_tif_fixed\ATG_62W17Nlb.tif'
    os.makedirs(os.path.dirname(tif_fixed), exist_ok=True)

    # 样板tif
    reference_raster = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\a_tif_GeeData\ATG\2010\ATG_62W16Nlu.tif"

    # 执行转换
    vector_to_raster(vector_path, tif_fixed, reference_raster, value=20)


if __name__ == '__main__':
    main()


# ====== _calculate_error_v2.py ======
# -*- coding: utf-8 -*-
"""
Generated by ArcGIS ModelBuilder on : 2025-01-08 09:04:02
"""
import os
import arcpy
import numpy as np
from dbfread import DBF

def calculate_statistics(dbf_file_path):
    """
    计算DBF文件中 'NEAR_DIST' 列的统计数据：
    - 平均值
    - 值小于30的个数百分比
    - 值小于60的个数百分比
    - 标准差
    - 均方根误差 (RMSE)

    参数:
    dbf_file_path (str): DBF文件路径

    返回:
    dict: 包含上述统计数据的字典
    """

    # 读取DBF文件
    dbf = DBF(dbf_file_path, encoding='utf-8')

    # 提取'NEAR_DIST'列的数据
    # near_dist_values = [record['NEAR_DIST'] for record in dbf if 'NEAR_DIST' in record]
    near_dist_values = []
    for record in dbf:
        if 'NEAR_DIST' in record:
            value = record['NEAR_DIST']
            if value >= 0:
                near_dist_values.append(value)

    # 如果没有数据，返回None
    if not near_dist_values:
        return None

    # 将数据转化为numpy数组
    near_dist_values = np.array(near_dist_values)

    # 计算统计值

    count_30 = np.sum(near_dist_values < 30)
    count_60 = np.sum(near_dist_values < 60)
    count_90 = np.sum(near_dist_values < 90)
    count_120 = np.sum(near_dist_values < 120)
    count_150 = np.sum(near_dist_values < 150)

    count_all = len(near_dist_values)
    percent_30 = count_30 / count_all * 100
    percent_60 = count_60 / count_all * 100
    percent_90 = count_90 / count_all * 100
    percent_120 = count_120 / count_all * 100
    percent_150 = count_150 / count_all * 100
    mean_value = np.mean(near_dist_values)
    std_dev = np.std(near_dist_values)
    rmse = np.sqrt(np.mean(near_dist_values ** 2))


    # 返回结果
    return {
        'count_30': count_30,
        'count_60': count_60,
        'count_90': count_90,
        'count_120': count_120,
        'count_150': count_150,
        'count_all': count_all,
        'percent_30': percent_30,
        'percent_60': percent_60,
        'percent_90': percent_90,
        'percent_120': percent_120,
        'percent_150': percent_150,
        'mean_value': mean_value,
        'std_dev': std_dev,
        'rmse': rmse
    }


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
    print("year gid mean_value	std_dev	rmse	percent_30	percent_60	percent_90	percent_120	percent_150	count_30	count_60	count_90	count_120	count_150	count_all")

    list_year = ['2015']
    list_sids = read_txt_to_list(file_path=fr"SIDS_37.txt")
    for year in list_year:
        for sid in list_sids:

            # 示例使用 sids
            # folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\{sid}\{year}"
            # near_table = os.path.join(folder_path, fr'SP_{sid}_{str(year)[-2:]}.dbf')

            # # 第三方数据集初始化
            folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\{sid}\{year}\ThirdPartyDataSource"
            # OSM
            # near_table = os.path.join(folder_path, fr'OSM_SP_{sid}_{str(year)[-2:]}.dbf')
            # # GCL_FCS30
            # near_table = os.path.join(folder_path, fr'GCL_SP_{sid}_{str(year)[-2:]}.dbf')
            # # GSV
            # near_table = os.path.join(folder_path, fr'GSV_SP_{sid}_{str(year)[-2:]}.dbf')
            # # GMSSD
            near_table = os.path.join(folder_path, fr'GMSSD_SP_{sid}_{str(year)[-2:]}.dbf')

            # 计算DBF文件中 'NEAR_DIST' 列的统计数据
            statistics = calculate_statistics(near_table)
            if statistics:
                # print("统计结果:", statistics)
                # print(year, sid,
                #       statistics['mean_value'],
                #       statistics['std_dev'],
                #       statistics['rmse'],
                #       statistics['percent_30'],
                #       statistics['percent_60'],
                #       statistics['percent_90'],
                #       statistics['percent_120'],
                #       statistics['percent_150'],
                #       statistics['count_30'],
                #       statistics['count_60'],
                #       statistics['count_90'],
                #       statistics['count_120'],
                #       statistics['count_150'],
                #       statistics['count_all'],
                #       )
                print(year, sid,
                      statistics['mean_value'],
                      statistics['std_dev'],
                      statistics['rmse'],
                      statistics['percent_30'],
                      statistics['percent_60'],
                      statistics['percent_90'],
                      statistics['count_30'],
                      statistics['count_60'],
                      statistics['count_90'],
                      statistics['count_all'],
                      )
            else:
                print(year, sid,)


# ====== _calculate_para.py ======
# -*- coding: utf-8 -*-
"""
Generated by ArcGIS ModelBuilder on : 2025-01-08 09:04:02
"""
import os
import arcpy
import numpy as np
from dbfread import DBF


def calculate_statistics(dbf_file_path):
    """
    计算DBF文件中 'NEAR_DIST' 列的统计数据：
    - 平均值
    - 值小于30的个数百分比
    - 值小于60的个数百分比
    - 标准差
    - 均方根误差 (RMSE)

    参数:
    dbf_file_path (str): DBF文件路径

    返回:
    dict: 包含上述统计数据的字典
    """

    # 读取DBF文件
    dbf = DBF(dbf_file_path, encoding='utf-8')

    # 提取'NEAR_DIST'列的数据
    # near_dist_values = [record['NEAR_DIST'] for record in dbf if 'NEAR_DIST' in record]
    near_dist_values = []
    for record in dbf:
        if 'NEAR_DIST' in record:
            value = record['NEAR_DIST']
            if value >= 0:
                near_dist_values.append(value)

    # 如果没有数据，返回None
    if not near_dist_values:
        return None

    # 将数据转化为numpy数组
    near_dist_values = np.array(near_dist_values)

    # 计算统计值

    count_30 = np.sum(near_dist_values < 30)
    count_60 = np.sum(near_dist_values < 60)
    count_90 = np.sum(near_dist_values < 90)
    count_all = len(near_dist_values)
    percent_30 = count_30 / count_all * 100
    percent_60 = count_60 / count_all * 100
    percent_90 = count_90 / count_all * 100
    mean_value = np.mean(near_dist_values)
    std_dev = np.std(near_dist_values)
    rmse = np.sqrt(np.mean(near_dist_values ** 2))

    # 返回结果
    return {
        'count_30': count_30,
        'count_60': count_60,
        'count_all': count_all,
        'percent_30': percent_30,
        'percent_60': percent_60,
        'percent_90': percent_90,
        'mean_value': mean_value,
        'std_dev': std_dev,
        'rmse': rmse
    }


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

    list_year = ['2020']
    list_sids = read_txt_to_list(file_path=fr"SIDS_37.txt")
    print("year gid percent_30	percent_60	mean_value	std_dev	rmse	count_30	count_60	count_all")
    for year in list_year:
        near_dist_values = []
        for sid in list_sids:

            # 示例使用 sids
            # folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\{sid}\{year}"
            # near_table = os.path.join(folder_path, fr'SP_{sid}_{str(year)[-2:]}.dbf')

            # # 第三方数据集初始化
            folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\{sid}\{year}\ThirdPartyDataSource"
            # OSM
            near_table = os.path.join(folder_path, fr'OSM_SP_{sid}_{str(year)[-2:]}.dbf')
            # # GCL_FCS30
            # near_table = os.path.join(folder_path, fr'GCL_SP_{sid}_{str(year)[-2:]}.dbf')
            # # GSV
            # near_table = os.path.join(folder_path, fr'GSV_SP_{sid}_{str(year)[-2:]}.dbf')
            # GMSSD
            # near_table = os.path.join(folder_path, fr'GMSSD_SP_{sid}_{str(year)[-2:]}.dbf')

            # 计算DBF文件中 'NEAR_DIST' 列的统计数据
            # statistics = calculate_statistics(near_table)

            # 读取DBF文件------------------------------------------------------------------------------
            dbf = DBF(near_table, encoding='utf-8')

            # 提取'NEAR_DIST'列的数据
            # near_dist_values = [record['NEAR_DIST'] for record in dbf if 'NEAR_DIST' in record]
            for record in dbf:
                if 'NEAR_DIST' in record:
                    value = record['NEAR_DIST']
                    if value >= 0:
                        near_dist_values.append(value)

        # 将数据转化为numpy数组
        near_dist_values = np.array(near_dist_values)

        # 计算统计值
        count_30 = np.sum(near_dist_values < 30)
        count_60 = np.sum(near_dist_values < 60)
        count_90 = np.sum(near_dist_values < 90)
        count_all = len(near_dist_values)
        percent_30 = count_30 / count_all * 100
        percent_60 = count_60 / count_all * 100
        percent_90 = count_90 / count_all * 100
        mean_value = np.mean(near_dist_values)
        std_dev = np.std(near_dist_values)
        rmse = np.sqrt(np.mean(near_dist_values ** 2))

        print(year,  mean_value, std_dev, rmse, percent_30, percent_60, percent_90, count_all)


# ====== _dbf_to_excel_SIDS.py ======
import os
import pandas as pd
from dbfread import DBF


def read_dbf_file(dbf_file_path, field_name):
    """
    读取指定的 DBF 文件并获取指定字段的第一个值。
    如果字段不存在或文件为空，则返回 0。

    参数:
        dbf_file_path (str): DBF 文件的路径。
        field_name (str): 需要读取的字段名称。

    返回:
        float: 指定字段的第一个值，或 0。
    """
    try:
        # 读取 DBF 文件
        table = DBF(dbf_file_path)
        # 获取指定字段的所有值
        values = [record[field_name] for record in table if field_name in record]
        # 返回第一个值，如果列表为空则返回 0
        return values[0] if values else 0
    except Exception as e:
        print(f"读取 {dbf_file_path} 时出错: {e}")
        return 0


def process_data(data_path, list_year, boundary_list):
    """
    处理数据并生成二维列表，用于后续转换为 DataFrame。

    参数:

    返回:
        list: 包含所有数据的二维列表。
    """
    # 初始化二维列表，第一行为字段名
    fields_list = ['ID', 'GID'] + list_year
    dbf_data = [fields_list]

    # 遍历每个边界
    row_count = 1
    for boundary in boundary_list:
        row_data = [row_count, boundary]  # 初始化行数据，包含 ID 和 GID
        # 遍历每个数据表
        for year in list_year:
            # 构造 DBF 文件路径
            dbf_file_path = os.path.join(data_path, f"{boundary}\{boundary}_BV_{year}.dbf")
            # 读取 DBF 文件并获取 'Leng_Geo' 字段的值
            length_geo_value = read_dbf_file(dbf_file_path, 'Area_Geo')
            # length_geo_value = read_dbf_file(dbf_file_path, 'Leng_Geo')
            row_data.append(length_geo_value)
        # 将当前行数据添加到总数据列表中
        dbf_data.append(row_data)
        row_count += 1

    return dbf_data


def save_to_excel(data, output_file):
    """
    将二维列表数据保存为 Excel 文件。

    参数:
        data (list): 二维列表数据。
        output_file (str): 输出的 Excel 文件路径。
    """
    # 将二维列表转换为 DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])
    # 保存为 Excel 文件
    df.to_excel(output_file, index=False)
    print(f"数据已成功导出到 {output_file}")


def main():
    # 数据路径和相关参数
    data_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\i_shp_smooth"
    list_year = ['2010', '2015', '2020',]

    # 全 37 国家
    boundary_list = ["ATG",
                     "BHS",
                     "BLZ",
                     "BRB",
                     "COM",
                     "CPV",
                     "CUB",
                     "DMA",
                     "DOM",
                     "FJI",
                     "FSM",
                     "GNB",
                     "GRD",
                     "GUY",
                     "HTI",
                     "JAM",
                     "KIR",
                     "KNA",
                     "LCA",
                     "MDV",
                     "MHL",
                     "MUS",
                     "NRU",
                     "PLW",
                     "PNG",
                     "SGP",
                     "SLB",
                     "STP",
                     "SUR",
                     "SYC",
                     "TLS",
                     "TON",
                     "TTO",
                     "TUV",
                     "VCT",
                     "VUT",
                     "WSM",
                     ]

    # 处理数据并生成二维列表
    dbf_data = process_data(data_path, list_year, boundary_list)
    print("生成的二维列表数据：")
    print(dbf_data)

    # 保存数据到 Excel 文件
    output_file = "SIDS_BV岛屿面积.xlsx"
    # output_file = "SIDS_BV岛屿长度.xlsx"
    save_to_excel(dbf_data, output_file)


if __name__ == "__main__":
    main()

# ====== a_.py ======
"""
1. 提取 .tif 文件中像元值大于 5 的区域并输出为新 .tif
"""
import rasterio
import numpy as np
from scipy.ndimage import maximum_filter
from scipy.ndimage import label
from scipy.ndimage import binary_fill_holes


def extract_pixels_gt_threshold(input_tif: str, output_tif: str, threshold: float = 5.0, nodata_value: float = 0.0):
    """
    提取像元值大于给定阈值的区域，并将其输出为新的 GeoTIFF 文件。

    参数:
        input_tif (str): 输入的 .tif 文件路径。
        output_tif (str): 输出的 .tif 文件路径。
        threshold (float): 像元阈值，默认是 5.0。
        nodata_value (float): 不满足条件的像元值填充值，默认是 0.0。
    """
    with rasterio.open(input_tif) as src:
        data = src.read(1)  # 读取第一个波段
        profile = src.profile

        # 创建掩码：像元值 > 阈值
        mask_data = data > threshold

        # 应用掩码：不满足条件的像元设为 nodata_value
        filtered_data = np.where(mask_data, data, nodata_value)

        # 更新 profile 信息
        profile.update(dtype=rasterio.float32, count=1, nodata=nodata_value)

        # 写入输出文件
        with rasterio.open(output_tif, 'w', **profile) as dst:
            dst.write(filtered_data.astype(rasterio.float32), 1)

    print(f"输出完成：{output_tif}")


def filter_by_local_max(input_tif: str, output_tif: str, window_size: int = 30, max_threshold: float = 10.0,
                        nodata_value: float = 0.0):
    """
    使用局部窗口（如30x30）进行最大值过滤：
    如果以像元为中心的窗口最大值 < max_threshold，则将该中心像元设置为 nodata_value。

    参数:
        input_tif (str): 输入 tif 文件路径。
        output_tif (str): 输出 tif 文件路径。
        window_size (int): 滤波窗口的大小（必须为奇数）。
        max_threshold (float): 最大值的阈值。
        nodata_value (float): 滤除后的像元值。
    """
    if window_size % 2 == 0:
        raise ValueError("window_size 必须为奇数，例如 29 或 31")

    with rasterio.open(input_tif) as src:
        data = src.read(1)  # 读取第一个波段
        profile = src.profile

        # 使用最大滤波器获取局部最大值
        local_max = maximum_filter(data, size=window_size, mode='nearest')

        # 过滤条件：窗口最大值 < 阈值 → 当前像元设为 nodata
        filtered_data = np.where(local_max < max_threshold, nodata_value, data)

        # 更新 profile
        profile.update(dtype=rasterio.float32, count=1, nodata=nodata_value)

        # 写入输出文件
        with rasterio.open(output_tif, 'w', **profile) as dst:
            dst.write(filtered_data.astype(rasterio.float32), 1)

    print(f"局部最大值过滤完成：{output_tif}")

def remove_small_clusters(input_tif: str, output_tif: str, min_cluster_size: int = 4, nodata_value: float = 0.0):
    """
    移除像元数量少于 min_cluster_size 的相邻小团块（连通区域）。

    参数:
        input_tif (str): 输入的栅格路径。
        output_tif (str): 输出文件路径。
        min_cluster_size (int): 最小保留的连通区域大小（像元数）。
        nodata_value (float): 被移除区域赋值。
    """
    with rasterio.open(input_tif) as src:
        data = src.read(1)
        profile = src.profile

        # 创建掩码：非0区域为目标区域
        mask = data != 0

        # 连通区域标记，8邻域结构
        structure = np.array([[0, 1, 0],
                              [1, 1, 1],
                              [0, 1, 0]])
        labeled, num_features = label(mask, structure=structure)

        # 统计每个区域的像元数量
        counts = np.bincount(labeled.ravel())

        # 创建掩码：保留像元数量 ≥ min_cluster_size 的区域
        keep_mask = np.isin(labeled, np.where(counts >= min_cluster_size)[0])

        # 应用掩码：过滤小团块
        filtered_data = np.where(keep_mask, data, nodata_value)

        # 更新 profile
        profile.update(dtype=rasterio.float32, count=1, nodata=nodata_value)

        # 保存结果
        with rasterio.open(output_tif, 'w', **profile) as dst:
            dst.write(filtered_data.astype(rasterio.float32), 1)

    print(f"小团块过滤完成（保留大小 ≥ {min_cluster_size}）：{output_tif}")


def fill_internal_holes(input_tif: str, output_tif: str, fill_value: float = 20.0):
    """
    封闭非零区域内部的空洞（值为0的像元），并赋值为指定值。

    参数:
        input_tif (str): 输入的.tif路径。
        output_tif (str): 输出的.tif路径。
        fill_value (float): 填充空洞的像元值，默认是 20.0。
    """
    with rasterio.open(input_tif) as src:
        data = src.read(1)
        profile = src.profile

        # 创建前景掩码（非零区域为前景）
        foreground = data != 0

        # 空洞填充：对前景进行填洞（binary_fill_holes作用于布尔数组）
        filled_foreground = binary_fill_holes(foreground)

        # 空洞区域 = 填充后 - 原前景（True表示原来是空洞）
        holes = filled_foreground & (~foreground)

        # 把空洞像元赋值为指定填充值
        data_filled = data.copy()
        data_filled[holes] = fill_value

        # 更新 profile
        profile.update(dtype=rasterio.float32, nodata=0.0)

        # 写出结果
        with rasterio.open(output_tif, 'w', **profile) as dst:
            dst.write(data_filled.astype(rasterio.float32), 1)

    print(f"空洞填充完成，空洞像元赋值为 {fill_value} ：{output_tif}")



def filter_clusters_by_median(input_tif: str, output_tif: str, threshold: float = 10.0, connectivity: int = 8):
    """
    根据像元团块中像元值的中位数过滤小团块。中位数小于 threshold 的团块将被赋值为 0。

    参数:
        input_tif (str): 输入栅格路径。
        output_tif (str): 输出栅格路径。
        threshold (float): 中位数阈值，小于该值的团块将被清除。
        connectivity (int): 连通性（4 或 8），默认使用8邻接。
    """
    with rasterio.open(input_tif) as src:
        data = src.read(1)
        profile = src.profile

        # 标记非0的连通区域
        mask = data != 0
        structure = np.array([[1,1,1],[1,1,1],[1,1,1]]) if connectivity == 8 else np.array([[0,1,0],[1,1,1],[0,1,0]])
        labeled_array, num_features = label(mask, structure=structure)

        print(f"共检测到 {num_features} 个栅格团块")

        # 复制数据用于输出
        filtered_data = data.copy()

        for region_label in range(1, num_features + 1):
            region_mask = labeled_array == region_label
            region_values = data[region_mask]

            # 计算中位数
            median_val = np.median(region_values)

            # 若中位数 < 阈值，则清除团块
            if median_val < threshold:
                filtered_data[region_mask] = 0

        # 更新并写入
        profile.update(dtype=rasterio.float32, nodata=0.0)

        with rasterio.open(output_tif, 'w', **profile) as dst:
            dst.write(filtered_data.astype(rasterio.float32), 1)

    print(f"✅ 团块过滤完成：输出为 {output_tif}")

def main():
    tif_gee = fr"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\SIDs_Grid_Y15\25W14Nru_ls578_Index.tif"
    temp_trush = fr'E:\_OrderingProject\draft0621'
    tif_temp1 = fr"{temp_trush}\temp1.tif"

    extract_pixels_gt_threshold(
        input_tif=tif_gee,
        output_tif=tif_temp1,
        threshold=1.0,
    )

    tif_temp2 = fr"{temp_trush}\temp2.tif"
    filter_by_local_max(
        input_tif=tif_temp1,
        output_tif=tif_temp2,
        window_size=31,
        max_threshold=10.0,
    )

    tif_temp3 = fr"{temp_trush}\temp3.tif"
    remove_small_clusters(
        input_tif=tif_temp2,
        output_tif=tif_temp3,
        min_cluster_size=4,
        nodata_value=0.0
    )

    tif_temp4 = fr"{temp_trush}\temp4.tif"
    fill_internal_holes(
        input_tif=tif_temp3,
        output_tif=tif_temp4,
        fill_value=20.0
    )

    tif_temp5 = fr"{temp_trush}\temp5.tif"
    filter_clusters_by_median(
        input_tif=tif_temp4,
        output_tif=tif_temp5,
        threshold=10.0,
    )


if __name__ == "__main__":
    main()


# ====== a_v2.py ======
import rasterio
import numpy as np
from scipy.ndimage import maximum_filter, label, binary_fill_holes

def extract_pixels_gt_threshold(data: np.ndarray, threshold: float = 5.0, nodata_value: float = 0.0):
    """
    提取像元值大于 threshold 的区域，其他区域赋值为 nodata_value。
    """
    return np.where(data > threshold, data, nodata_value)

def filter_by_local_max(data: np.ndarray, window_size: int = 31, max_threshold: float = 10.0, nodata_value: float = 0.0):
    """
    使用最大滤波器在局部窗口中计算最大值，如果窗口最大值小于 max_threshold，
    则将中心像元置为 nodata_value。
    """
    local_max = maximum_filter(data, size=window_size, mode='nearest')
    return np.where(local_max < max_threshold, nodata_value, data)

def remove_small_clusters(data: np.ndarray, min_cluster_size: int = 4, nodata_value: float = 0.0):
    """
    标记非零像元的连通区域，去除像元数少于 min_cluster_size 的小团块（设置为 nodata_value）。
    使用 4 邻接结构。
    """
    mask = data != 0
    structure = np.array([[0,1,0], [1,1,1], [0,1,0]])  # 4邻域结构
    labeled, num_features = label(mask, structure=structure)  # 连通区域标记
    counts = np.bincount(labeled.ravel())  # 统计每个区域的像元数
    keep_mask = np.isin(labeled, np.where(counts >= min_cluster_size)[0])  # 创建保留区域掩码
    return np.where(keep_mask, data, nodata_value)

def fill_internal_holes(data: np.ndarray, fill_value: float = 20.0):
    """
    填补前景区域（data != 0）内部的空洞（封闭的 0 区域），将其像元值赋值为 fill_value。
    """
    foreground = data != 0  # 前景布尔掩码
    filled = binary_fill_holes(foreground)  # 填补空洞
    holes = filled & (~foreground)  # 新填补的空洞区域
    data_copy = data.copy()
    data_copy[holes] = fill_value  # 赋值空洞区域
    return data_copy

def filter_clusters_by_median(data: np.ndarray, threshold: float = 10.0, connectivity: int = 8):
    """
    对每个非零连通团块，计算其像元中位数。若中位数小于 threshold，则整个团块赋值为 0。
    支持 8 或 4 邻接。
    """
    mask = data != 0
    structure = np.ones((3,3)) if connectivity == 8 else np.array([[0,1,0],[1,1,1],[0,1,0]])
    labeled, num_features = label(mask, structure=structure)  # 标记连通区域
    filtered_data = data.copy()

    for region_label in range(1, num_features + 1):
        region_mask = labeled == region_label
        region_values = data[region_mask]
        median_val = np.median(region_values)  # 计算中位数

        if median_val < threshold:
            filtered_data[region_mask] = 0  # 低于阈值则清除团块

    return filtered_data

def main():
    # 输入原始遥感指数图像
    tif_input = r"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\SIDs_Grid_Y15\25W14Nru_ls578_Index.tif"
    # 最终输出结果
    tif_output = r"E:\_OrderingProject\draft0621\temp5.tif"

    # 打开原始 tif 文件并读取波段数据与 profile（元数据）
    with rasterio.open(tif_input) as src:
        data = src.read(1)
        profile = src.profile

    # 1️⃣ 步骤1：提取像元值 > 1 的区域
    data = extract_pixels_gt_threshold(data, threshold=1.0)

    # 2️⃣ 步骤2：局部最大值滤波过滤背景噪点
    data = filter_by_local_max(data, window_size=31, max_threshold=10.0)

    # 3️⃣ 步骤3：移除面积小于 4 的栅格团块
    data = remove_small_clusters(data, min_cluster_size=4)

    # 4️⃣ 步骤4：封闭团块内的空洞，填充为20
    data = fill_internal_holes(data, fill_value=20.0)

    # 5️⃣ 步骤5：以中位数为指标清除不显著团块
    data = filter_clusters_by_median(data, threshold=10.0)

    # 更新输出影像 profile，并设置 nodata 值
    profile.update(dtype=rasterio.float32, count=1, nodata=0.0)

    # 写入最终处理结果
    with rasterio.open(tif_output, 'w', **profile) as dst:
        dst.write(data.astype(np.float32), 1)

    print(f"✅ 过滤流程完成，最终结果输出至：{tif_output}")

if __name__ == "__main__":
    main()


# ====== a_v3.py ======
import os
import rasterio
import numpy as np
from dbfread import DBF
from scipy.ndimage import maximum_filter, label, binary_fill_holes

def extract_pixels_gt_threshold(data: np.ndarray, threshold: float = 5.0, nodata_value: float = 0.0):
    """
    提取像元值大于 threshold 的区域，其他区域赋值为 nodata_value。
    """
    return np.where(data > threshold, data, nodata_value)

def filter_by_local_max(data: np.ndarray, window_size: int = 31, max_threshold: float = 10.0, nodata_value: float = 0.0):
    """
    使用最大滤波器在局部窗口中计算最大值，如果窗口最大值小于 max_threshold，
    则将中心像元置为 nodata_value。
    """
    local_max = maximum_filter(data, size=window_size, mode='nearest')
    return np.where(local_max < max_threshold, nodata_value, data)

def remove_small_clusters(data: np.ndarray, min_cluster_size: int = 4, nodata_value: float = 0.0):
    """
    标记非零像元的连通区域，去除像元数少于 min_cluster_size 的小团块（设置为 nodata_value）。
    使用 4 邻接结构。
    """
    mask = data != 0
    structure = np.array([[1,1,1], [1,1,1], [1,1,1]])  # 4邻域结构
    labeled, num_features = label(mask, structure=structure)  # 连通区域标记
    counts = np.bincount(labeled.ravel())  # 统计每个区域的像元数
    keep_mask = np.isin(labeled, np.where(counts >= min_cluster_size)[0])  # 创建保留区域掩码
    return np.where(keep_mask, data, nodata_value)

def fill_internal_holes(data: np.ndarray, fill_value: float = 20.0, max_hole_size: int = 500):
    """
    高效填补内部空洞，跳过像元数超过 max_hole_size 的区域（完全矢量化版本）
    """
    foreground = data != 0
    filled = binary_fill_holes(foreground)
    holes = filled & (~foreground)

    structure = np.ones((3, 3))  # 8邻域结构
    labeled, num_features = label(holes, structure=structure)

    # 计算每个空洞区域的像元数量
    counts = np.bincount(labeled.ravel())

    # 找出符合条件的区域索引（非0，且小于等于max_hole_size）
    valid_labels = np.where((counts > 0) & (counts <= max_hole_size))[0]

    # 构建保留掩码：只填补小于阈值的空洞区域
    mask_fill = np.isin(labeled, valid_labels)

    # 应用填补
    data_filled = data.copy()
    data_filled[mask_fill] = fill_value

    return data_filled

def filter_clusters_by_median(data: np.ndarray, threshold: float = 10.0, connectivity: int = 8):
    """
    对每个非零连通团块，计算其像元中位数。若中位数小于 threshold，则整个团块赋值为 0。
    支持 8 或 4 邻接。
    """
    mask = data != 0
    structure = np.ones((3,3)) if connectivity == 8 else np.array([[0,1,0],[1,1,1],[0,1,0]])
    labeled, num_features = label(mask, structure=structure)  # 标记连通区域
    filtered_data = data.copy()

    for region_label in range(1, num_features + 1):
        region_mask = labeled == region_label
        region_values = data[region_mask]
        median_val = np.median(region_values)  # 计算中位数

        if median_val < threshold:
            filtered_data[region_mask] = 0  # 低于阈值则清除团块

    return filtered_data

def read_txt_to_list(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    # 去除每行末尾的换行符
    lines = [line.strip() for line in lines]
    return lines


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

def tif_preprocessing(extract_threshold, fliter_threshold, tif_input, tif_output):
    # 打开原始 tif 文件并读取波段数据与 profile（元数据）
    with rasterio.open(tif_input) as src:
        data = src.read(1)
        profile = src.profile

    # 1️⃣ 步骤1：提取像元值 > 1 的区域
    data = extract_pixels_gt_threshold(data, threshold=extract_threshold)

    # 2️⃣ 步骤2：局部最大值滤波过滤背景噪点
    data = filter_by_local_max(data, window_size=31, max_threshold=fliter_threshold)

    # 3️⃣ 步骤3：移除面积小于 4 的栅格团块
    data = remove_small_clusters(data, min_cluster_size=4)

    # 4️⃣ 步骤4：封闭团块内的空洞，填充为20
    data = fill_internal_holes(data, fill_value=20.0)

    # 5️⃣ 步骤5：以中位数为指标清除不显著团块
    data = filter_clusters_by_median(data, threshold=fliter_threshold)

    # 更新输出影像 profile，并设置 nodata 值
    profile.update(dtype=rasterio.float32, count=1, nodata=0.0)

    # 写入最终处理结果
    with rasterio.open(tif_output, 'w', **profile) as dst:
        dst.write(data.astype(np.float32), 1)

    print(f"✅ 过滤流程完成，最终结果输出至：{tif_output}")


def main():
    # 初始化处理的国家和年份
    list_year = ['2010', '2015', '2020']
    list_sids = read_txt_to_list(file_path=fr"SIDS_37.txt")

    # for year in ['2015', '2020']:
    for year in list_year:
        # for sids in ['ATG']:
        for sids in list_sids:
            # 获得对应国家图幅
            dbf_grid_path = (
                fr".\SIDS_grid_link\{sids}_grid.dbf")
            list_sids_map = read_dbf_to_list(dbf_path=dbf_grid_path, if_print=0)
            # 国家图幅 ['63W16Nru', '62W16Nlu', '63W17Nrb', '62W17Nlb', '62W17Nlu']
            list_sids_map_name = [sublist[4] for sublist in list_sids_map]

            for map_name in list_sids_map_name:
                # 提取阈值
                if year == '2010':
                    extract_threshold = 1.0
                elif year == '2015':
                    extract_threshold = 5.0
                elif year == '2020':
                    extract_threshold = 9.0
                filter_threshold = 15.0
                # 输入原始遥感指数图像
                tif_input = (
                    fr"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData"
                    fr"\SIDs_Grid_Y{year[-2:]}\{map_name}_ls578_Index.tif")
                # 最终输出结果
                tif_output = (
                    fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\a_tif_GeeData"
                    fr"\{sids}\{year}\{sids}_{map_name}.tif")
                # 创建路径
                path_folder = os.path.dirname(tif_output)
                os.makedirs(path_folder, exist_ok=True)

                # 图像预处理
                try:
                    tif_preprocessing(extract_threshold, filter_threshold, tif_input, tif_output)
                except Exception as e:
                    pass


if __name__ == "__main__":
    main()


# ====== b_.py ======
import rasterio
import numpy as np
import geopandas as gpd
from shapely.geometry import shape
from rasterio.features import shapes
from scipy.ndimage import label


def tif_to_merged_regions_shp(input_tif: str, output_shp: str, threshold: float = 0.0):
    """
    将.tif中值大于指定阈值的连通区域合并为一个或多个面，并保存为shapefile。

    参数:
        input_tif (str): 输入的.tif文件路径。
        output_shp (str): 输出的.shp文件路径。
        threshold (float): 像元阈值，大于此值的区域将被合并为矢量面。
    """
    with rasterio.open(input_tif) as src:
        data = src.read(1)
        transform = src.transform
        crs = src.crs

        # 生成二值掩码（1 表示值 > 阈值）
        binary_mask = (data > threshold).astype(np.uint8)

        # 连通区域标记
        labeled_array, num_features = label(binary_mask)

        print(f"检测到 {num_features} 个连通区域")

        # 转换为矢量面
        shapes_gen = shapes(labeled_array, mask=binary_mask, transform=transform)
        geometries = [
            {"geometry": shape(geom), "properties": {"id": int(value)}}
            for geom, value in shapes_gen
            if value != 0
        ]

        # 构建 GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(geometries)
        gdf.crs = crs

        # 保存为 Shapefile
        gdf.to_file(output_shp, driver='ESRI Shapefile')

        print(f"成功输出为 shapefile：{output_shp}")

tif_to_merged_regions_shp(
    input_tif=r"E:\_OrderingProject\draft0621\ATG_62W17Nlb.tif",
    output_shp=r"E:\_OrderingProject\draft0621\ATG_62W17Nlb_regions.shp",
)


# ====== b_v2.py ======
import os
import arcpy
import rasterio
import numpy as np
import geopandas as gpd
from shapely.geometry import shape
from rasterio.features import shapes
from scipy.ndimage import label

def select_valid_polygons(valid_pixel_shp, country_shp, output_shp):
    """
    按位置选择有效的像素多边形，并导出符合条件的结果。

    参数：
    valid_pixel_shp (str)：有效像素矢量文件路径。
    country_shp (str)：国家边界矢量文件路径。
    output_shp (str)：筛选后导出的矢量文件路径。
    """
    arcpy.env.overwriteOutput = True

    # 按位置选择中心点在国家边界内的有效像素:HAVE_THEIR_CENTER_IN | INTERSECT
    selected_layer = arcpy.management.SelectLayerByLocation(
        in_layer=[valid_pixel_shp],
        overlap_type="INTERSECT",
        select_features=country_shp,
        search_distance="1 Kilometers",
        selection_type="NEW_SELECTION"
    )

    # 导出符合条件的多边形
    arcpy.conversion.ExportFeatures(in_features=selected_layer, out_features=output_shp)

    # 清除选择
    arcpy.management.SelectLayerByAttribute(selected_layer, "CLEAR_SELECTION")

    print(f"- 有效多边形已导出至：{output_shp}")


def tif_to_merged_regions_shp(input_tif: str, output_shp: str, threshold: float = 0.0):
    """
    将.tif中值大于指定阈值的连通区域合并为一个或多个面，并保存为shapefile。

    参数:
        input_tif (str): 输入的.tif文件路径。
        output_shp (str): 输出的.shp文件路径。
        threshold (float): 像元阈值，大于此值的区域将被合并为矢量面。
    """
    with rasterio.open(input_tif) as src:
        data = src.read(1)
        transform = src.transform
        crs = src.crs

        # 生成二值掩码（1 表示值 > 阈值）
        binary_mask = (data > threshold).astype(np.uint8)

        # 连通区域标记
        labeled_array, num_features = label(binary_mask)

        print(f"检测到 {num_features} 个连通区域")

        # 转换为矢量面
        shapes_gen = shapes(labeled_array, mask=binary_mask, transform=transform)
        geometries = [
            {"geometry": shape(geom), "properties": {"id": int(value)}}
            for geom, value in shapes_gen
            if value != 0
        ]

        # 构建 GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(geometries)
        gdf.crs = crs

        # 保存为 Shapefile
        gdf.to_file(output_shp, driver='ESRI Shapefile')

        print(f"成功输出为 shapefile：{output_shp}")

def read_txt_to_list(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    # 去除每行末尾的换行符
    lines = [line.strip() for line in lines]
    return lines

def get_files_absolute_paths(folder_path, suffix=None):
    """
    获取指定文件夹下所有指定后缀的文件的绝对路径名称

    :param folder_path: 指定文件夹的路径
    :param suffix: 文件后缀（可选），如 '.shp'。如果不指定，则获取所有文件的路径
    :return: 指定后缀的文件的绝对路径名称列表
    """
    files_paths = []
    # 遍历指定文件夹
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 如果指定了后缀，则判断文件后缀是否匹配
            if suffix is None or file.endswith(suffix):
                # 获取文件的绝对路径并添加到列表中
                files_paths.append(os.path.abspath(os.path.join(root, file)))
    return files_paths

def main():
    # 初始化处理的国家和年份
    list_year = ['2010', '2015', '2020']
    list_sids = read_txt_to_list(file_path=fr"SIDS_37.txt")

    for year in ['2010']:
    # for year in list_year:
        for sids in ['ATG']:
        # for sids in list_sids:
            # 示例使用
            path_folder = (
                fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp"
                fr"\a_tif_GeeData\{sids}\{year}")
            list_map_files = get_files_absolute_paths(path_folder, suffix=fr'.tif')
            for tif_file in list_map_files:
                temp1 = fr"E:\_OrderingProject\draft0621\temp9.shp"
                tif_to_merged_regions_shp(
                    input_tif=tif_file,
                    output_shp=temp1,
                )

                country_shp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\d_SIDS_Boundary\SIDS\AdminDivision\{sids}.shp"
                out_fea = r"E:\_OrderingProject\draft0621\temp10.shp"
                select_valid_polygons(valid_pixel_shp=temp1, country_shp=country_shp, output_shp=out_fea)


if __name__ == "__main__":
    main()


# ====== b_v3.py ======
import os
import arcpy
import rasterio
import numpy as np
import geopandas as gpd
from shapely.geometry import shape
from rasterio.features import shapes
from scipy.ndimage import label
from pathlib import Path

# 设置工作环境
arcpy.env.overwriteOutput = True


def select_valid_polygons(valid_pixel_shp: str, country_shp: str, output_shp: str) -> None:
    """
    按位置选择有效的像素多边形，并导出符合条件的结果。

    参数：
    valid_pixel_shp (str)：有效像素矢量文件路径。
    country_shp (str)：国家边界矢量文件路径。
    output_shp (str)：筛选后导出的矢量文件路径。
    """
    try:
        # 创建输出目录（如果不存在）
        os.makedirs(os.path.dirname(output_shp), exist_ok=True)

        # 按位置选择中心点在国家边界内的有效像素
        selected_layer = arcpy.management.SelectLayerByLocation(
            in_layer=[valid_pixel_shp],
            overlap_type="INTERSECT",
            select_features=country_shp,
            search_distance="200 Meters",
            selection_type="NEW_SELECTION"
        )

        # 导出符合条件的多边形
        arcpy.conversion.ExportFeatures(in_features=selected_layer, out_features=output_shp)

        # 清除选择
        arcpy.management.SelectLayerByAttribute(selected_layer, "CLEAR_SELECTION")

        print(f"- 有效多边形已导出至：{output_shp}")
    except Exception as e:
        print(f"警告：选择有效多边形时出错 - {str(e)}")


def tif_to_merged_regions_shp(input_tif: str, output_shp: str, threshold: float = 0.0) -> None:
    """
    将.tif中值大于指定阈值的连通区域合并为一个或多个面，并保存为shapefile。

    参数:
        input_tif (str): 输入的.tif文件路径。
        output_shp (str): 输出的.shp文件路径。
        threshold (float): 像元阈值，大于此值的区域将被合并为矢量面。
    """
    try:
        # 创建输出目录（如果不存在）
        os.makedirs(os.path.dirname(output_shp), exist_ok=True)

        with rasterio.open(input_tif) as src:
            data = src.read(1)  # 读取第一个波段
            transform = src.transform
            crs = src.crs

            # 生成二值掩码
            binary_mask = (data > threshold).astype(np.uint8)

            # 连通区域标记
            labeled_array, num_features = label(binary_mask)

            if num_features > 0:
                print(f"检测到 {num_features} 个连通区域")

                # 转换为矢量面
                shapes_gen = shapes(labeled_array, mask=binary_mask, transform=transform)
                geometries = [
                    {"geometry": shape(geom), "properties": {"id": int(value)}}
                    for geom, value in shapes_gen
                    if value != 0
                ]

                # 构建 GeoDataFrame
                gdf = gpd.GeoDataFrame.from_features(geometries)
                gdf.crs = crs

                # 保存为 Shapefile
                gdf.to_file(output_shp, driver='ESRI Shapefile')
                print(f"成功输出为 shapefile：{output_shp}")
            else:
                print(f"无有效矢量区域，未生成输出文件")
    except Exception as e:
        print(f"警告：处理栅格数据时出错 - {str(e)}")


def read_txt_to_list(file_path: str) -> list[str]:
    """读取文本文件内容并返回一个列表"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        print(f"错误：读取文件 {file_path} 失败 - {str(e)}")
        return []


def get_files_absolute_paths(folder_path: str, suffix: str = None) -> list[str]:
    """
    获取指定文件夹下所有指定后缀的文件的绝对路径名称。

    参数:
        folder_path (str): 指定文件夹的路径。
        suffix (str): 文件后缀（可选），如 '.shp'。如果不指定，则获取所有文件的路径。
    """
    if not os.path.exists(folder_path):
        print(f"警告：文件夹 {folder_path} 不存在")
        return []

    return [
        os.path.abspath(os.path.join(root, file))
        for root, _, files in os.walk(folder_path)
        for file in files
        if suffix is None or file.endswith(suffix)
    ]


def main():
    """主函数，执行整个处理流程"""
    # 项目根路径
    project_root = Path(r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData")

    # 输入数据路径
    sids_file = "SIDS_37.txt"
    sids_boundary_dir = project_root / "j_SIDS_Polygon"

    # 输出数据路径
    temp_dir = project_root / "temp"
    draft_dir = temp_dir / "_draft"
    tif_input_dir = temp_dir / "a_tif_GeeData"
    shp_output_dir = temp_dir / "b_shp_GeeData"

    # # 处理的年份和国家代码
    years = ['2010', '2015']
    # sids_list = read_txt_to_list(str(sids_file))

    # 使用示例数据进行测试
    # years = ['2010']  # 示例仅处理 2010 年
    sids_list = ['ATG']  # 示例仅处理国家代码为 ATG 的国家

    # 遍历年份和国家代码
    for year in years:
        for sids in sids_list:
            print(f"\n处理 {sids} {year} 数据...")

            # 检查国家边界文件
            country_shp = sids_boundary_dir / sids / f"{sids}_{year[-2:]}.shp"
            if not country_shp.exists():
                print(f"跳过 {sids}：边界文件 {country_shp} 不存在")
                continue

            # 获取TIF文件列表
            tif_folder = tif_input_dir / sids / year
            tif_files = get_files_absolute_paths(str(tif_folder), suffix='.tif')

            if not tif_files:
                print(f"跳过 {sids} {year}：未找到TIF文件")
                continue

            # 处理每个TIF文件
            for tif_file in tif_files:
                try:
                    tif_name = os.path.splitext(os.path.basename(tif_file))[0]

                    # 临时输出文件路径
                    temp_shp = draft_dir / f"{tif_name}.shp"

                    # 将.tif文件中的连通区域转换为矢量面
                    tif_to_merged_regions_shp(
                        input_tif=str(tif_file),
                        output_shp=str(temp_shp)
                    )

                    # 最终输出文件路径
                    out_shp = shp_output_dir / sids / year / f"{tif_name}.shp"

                    # 按位置选择有效的像素多边形
                    if os.path.exists(temp_shp):
                        select_valid_polygons(
                            valid_pixel_shp=str(temp_shp),
                            country_shp=str(country_shp),
                            output_shp=str(out_shp)
                        )
                    else:
                        print(f"警告：临时文件 {temp_shp} 不存在，跳过选择步骤")
                except Exception as e:
                    print(f"错误：处理文件 {tif_file} 时出错 - {str(e)}")


if __name__ == "__main__":
    main()


# ====== c.py ======
from shapely.geometry import Polygon, MultiPolygon
import os
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from shapely.geometry import mapping


def fix_holes_in_shp(input_shp: str, output_shp: str, min_area: float = 0.0) -> None:
    """
    修复Shapefile面要素中的空洞。

    参数:
        input_shp (str): 输入Shapefile路径
        output_shp (str): 输出Shapefile路径
        min_area (float): 保留的最小空洞面积，小于此面积的空洞将被填充
    """
    # 读取Shapefile
    gdf = gpd.read_file(input_shp)

    # 处理每个几何对象
    fixed_geometries = []
    for geom in gdf.geometry:
        if geom.geom_type == 'Polygon':
            # 处理单个多边形
            exterior = geom.exterior
            interiors = [interior for interior in geom.interiors if interior.area > min_area]
            fixed_geom = Polygon(exterior, interiors)
            fixed_geometries.append(fixed_geom)
        elif geom.geom_type == 'MultiPolygon':
            # 处理多个多边形
            fixed_polygons = []
            for poly in geom.geoms:
                exterior = poly.exterior
                interiors = [interior for interior in poly.interiors if interior.area > min_area]
                fixed_poly = Polygon(exterior, interiors)
                fixed_polygons.append(fixed_poly)
            fixed_geom = MultiPolygon(fixed_polygons)
            fixed_geometries.append(fixed_geom)
        else:
            # 非面要素直接添加
            fixed_geometries.append(geom)

    # 更新几何列
    gdf.geometry = fixed_geometries

    # 保存结果
    gdf.to_file(output_shp)
    print(f"已修复空洞并保存至: {output_shp}")


def vector_to_raster(vector_path, raster_path, reference_raster, value=10):
    """
    将矢量文件转换为栅格，并赋值为指定的值。

    :param vector_path: 输入矢量文件路径 (Shapefile)
    :param raster_path: 输出栅格文件路径
    :param reference_raster: 参考栅格文件路径，仅用于获取像元大小信息
    :param value: 转换后的栅格像元值
    """
    try:
        # 读取矢量数据
        vector_data = gpd.read_file(vector_path)

        # 获取矢量数据的 CRS 和几何边界
        crs = vector_data.crs
        bounds = vector_data.total_bounds  # 获取矢量数据的边界框

        # 读取参考栅格的像元大小信息
        with rasterio.open(reference_raster) as ref_src:
            pixel_size = ref_src.res[0]  # 假设像元大小在 x 和 y 方向相同

        # 计算输出栅格的宽度和高度
        width = int((bounds[2] - bounds[0]) / pixel_size)
        height = int((bounds[3] - bounds[1]) / pixel_size)

        # 计算仿射变换矩阵
        transform = rasterio.Affine(pixel_size, 0, bounds[0], 0, -pixel_size, bounds[3])

        # 获取矢量文件的几何数据
        geometries = vector_data.geometry

        # 创建栅格化的图像
        rasterized_data = rasterize(
            [(mapping(geometry), value) for geometry in geometries],
            out_shape=(height, width),
            transform=transform,
            fill=0,  # 设置非矢量区域的值为 0
            dtype='uint8'
        )

        # 确保输出文件的目录存在
        output_dir = os.path.dirname(raster_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 保存为输出栅格文件
        with rasterio.open(
                raster_path,
                'w',
                driver='GTiff',
                height=height,
                width=width,
                count=1,
                dtype=rasterized_data.dtype,
                crs=crs,
                transform=transform,
                nodata=0  # 设置空值为 0
        ) as dst:
            dst.write(rasterized_data, 1)

        print(f"Tif saved as: {raster_path}")

    except Exception as e:
        print(f"发生错误: {e}")


def read_txt_to_list(file_path: str) -> list[str]:
    """读取文本文件内容并返回一个列表"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        print(f"错误：读取文件 {file_path} 失败 - {str(e)}")
        return []


def get_files_absolute_paths(folder_path, suffix=None):
    """
    获取指定文件夹下所有指定后缀的文件的绝对路径名称

    :param folder_path: 指定文件夹的路径
    :param suffix: 文件后缀（可选），如 '.shp'。如果不指定，则获取所有文件的路径
    :return: 指定后缀的文件的绝对路径名称列表
    """
    files_paths = []
    # 遍历指定文件夹
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 如果指定了后缀，则判断文件后缀是否匹配
            if suffix is None or file.endswith(suffix):
                # 获取文件的绝对路径并添加到列表中
                files_paths.append(os.path.abspath(os.path.join(root, file)))
    return files_paths


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


def shp_tif_fix(year, sids, shp_file):
    # 修复几何
    shp_input = (
        fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\b_shp_GeeData"
        fr"\{sids}\{year}\{os.path.basename(shp_file)}")
    print(shp_input)
    shp_fixed = (
        fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\c_shp_fixed"
        fr"\{sids}\{year}\{os.path.basename(shp_file)}")
    os.makedirs(os.path.dirname(shp_fixed), exist_ok=True)
    fix_holes_in_shp(input_shp=shp_input, output_shp=shp_fixed)
    # 修复栅格
    tif_fixed = (
        fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\d_tif_fixed"
        fr"\{sids}\{year}\{os.path.splitext(os.path.basename(shp_file))[0]}.tif")
    reference_raster = (
        r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\a_tif_GeeData\ATG\2010\ATG_62W16Nlu.tif"
    )
    os.makedirs(os.path.dirname(tif_fixed), exist_ok=True)

    # 执行转换
    vector_to_raster(vector_path=shp_fixed, raster_path=tif_fixed, reference_raster=reference_raster, value=20)


def main():
    # 初始化处理的国家和年份
    list_year = ['2010', '2015', '2020']
    list_sids = read_txt_to_list(file_path=fr"SIDS_37.txt")

    for year in ['2010', '2015']:
        # for year in list_year:
        for sids in ['ATG']:
            # for sids in list_sids:
            # 示例使用
            path_folder = (
                fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp"
                fr"\b_shp_GeeData\{sids}\{year}")
            list_map_files = get_files_absolute_paths(path_folder, suffix=fr'.shp')
            for shp_file in list_map_files:
                try:
                    shp_tif_fix(
                        year=year,
                        sids=sids,
                        shp_file=shp_file
                    )
                except Exception as e:
                    pass


if __name__ == '__main__':
    main()


# ====== d_.py ======
# -*- coding: utf-8 -*-
"""
作者：23242
日期：2024年09月18日

功能：
- 从栅格图像中提取子像素轮廓线
- 封闭 MultiLineString 线段
"""

import os
import rasterio
import numpy as np
from rasterio import Affine
import xarray as xr
import rioxarray
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString

from shapely.geometry import LineString, MultiLineString
from shapely.ops import polygonize
from dea_tools.spatial import subpixel_contours


# 添加默认条带用于封闭
def add_zero_buffer(input_tif, output_tif, buffer_size=1):
    """
    给指定 GeoTIFF 文件的边界添加一圈栅格值为 0 的像元值。

    参数:
    input_tif (str): 输入的 GeoTIFF 文件路径
    output_tif (str): 输出的 GeoTIFF 文件路径
    buffer_size (int): 要添加的像元缓冲大小，默认值为 1（即一圈像元）
    """
    # 打开输入的 GeoTIFF 文件
    with rasterio.open(input_tif) as src:
        # 获取输入栅格的元数据
        profile = src.profile.copy()

        # 获取原始图像的宽度和高度
        width, height = src.width, src.height

        # 计算新的宽度和高度
        new_width = width + 2 * buffer_size
        new_height = height + 2 * buffer_size

        # 创建新的仿射变换，扩展边界
        new_transform = src.transform * Affine.translation(-buffer_size, -buffer_size)

        # 更新元数据以反映新的宽度、高度和变换
        profile.update({
            'width': new_width,
            'height': new_height,
            'transform': new_transform
        })

        # 创建一个新的数组，初始化为 0，表示边界缓冲的像元值为 0
        new_data = np.zeros((src.count, new_height, new_width), dtype=src.dtypes[0])

        # 读取原始图像数据
        original_data = src.read()

        # 将原始图像放置在新的数据中央
        new_data[:, buffer_size:buffer_size+height, buffer_size:buffer_size+width] = original_data

        # 写入新的 GeoTIFF 文件
        with rasterio.open(output_tif, 'w', **profile) as dst:
            dst.write(new_data)

    print(f'Periphery of fusion boundary: {output_tif}.')

# 定义函数用于处理 MultiLineString，并封闭线段和进行坐标偏移
def process_multilinestring(geometry, x_offset, y_offset):
    """
    处理 MultiLineString，进行坐标偏移并封闭线段。

    :param geometry: 输入的 MultiLineString 对象
    :param x_offset: X 方向偏移量
    :param y_offset: Y 方向偏移量
    :yield: 处理后的 LineString 对象
    """
    if isinstance(geometry, MultiLineString):
        # 遍历 MultiLineString 中的每个组件
        for component in geometry.geoms:
            coords = list(component.coords)  # 获取坐标列表
            start_point = coords[0]          # 线段起点
            end_point = coords[-1]           # 线段终点

            # 添加偏移量到每个坐标
            coords = [(x + x_offset, y + y_offset) for x, y in coords]

            # 如果首尾点不同，则添加首点以封闭线段
            if start_point != end_point:
                coords.append(coords[0])  # 闭合线段
            yield LineString(coords)      # 返回封闭后的 LineString
    else:
        print("Geometry is not MultiLineString.")
        return None


# 定义函数用于修复子像素提取，并将结果保存为 GeoJSON
def fix_subpixel_extraction(input_geojson, output_geojson, x_offset, y_offset):
    """
    处理 MultiLineString 几何对象，并对其应用坐标偏移，保存为 GeoJSON。

    :param input_geojson: 输入的 GeoJSON 文件路径
    :param output_geojson: 输出的 GeoJSON 文件路径
    :param x_offset: X 方向偏移量
    :param y_offset: Y 方向偏移量
    """
    gdf = gpd.read_file(input_geojson)  # 读取输入的 GeoJSON
    for idx, row in gdf.iterrows():
        geometry = row['geometry']  # 获取几何对象
        # 检查几何是否为 MultiLineString
        if isinstance(geometry, MultiLineString):
            closed_components = list(process_multilinestring(geometry, x_offset, y_offset))
            closed_multilinestring = MultiLineString(closed_components)
            gdf.at[idx, 'geometry'] = closed_multilinestring  # 更新几何对象
        else:
            print(f"Feature {idx + 1} is not a MultiLineString.")
    gdf.to_file(output_geojson, driver="GeoJSON")  # 保存到输出文件
    print(f"Subpixel_closed MultiLineString output: {output_geojson}")


# 定义函数进行子像素提取，并生成 GeoJSON
def subpixel_extraction(input_tif, z_values, subpixel_tif):
    """
    从 TIF 文件进行子像素提取，并生成 GeoJSON。

    :param input_tif: 输入的 TIF 文件路径
    :param z_values: 提取等高线的 Z 值
    :param subpixel_tif: 输出的 GeoJSON 文件路径
    """
    # 添加外围封闭栅格圈
    temp_zero_buffer = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Filtering\temp_zero_buffer.tif'
    add_zero_buffer(input_tif=input_tif, output_tif=temp_zero_buffer, buffer_size=1)

    tif_file = temp_zero_buffer
    with rasterio.open(tif_file) as src:
        raster_data = src.read(1)       # 读取栅格数据
        transform = src.transform       # 获取仿射变换
        crs = src.crs                   # 获取坐标参考系
        height, width = raster_data.shape

        # 计算偏移量（半个像素的长度）
        x_offset = transform[0] / 2
        y_offset = transform[4] / 2

        # 创建 x, y 坐标数组
        x_coords = [transform * (col, 0) for col in range(width)]
        y_coords = [transform * (0, row) for row in range(height)]
        x_coords = [x[0] for x in x_coords]
        y_coords = [y[1] for y in y_coords]

        # 将栅格数据转换为 xarray DataArray
        data_array = xr.DataArray(
            raster_data,
            coords=[y_coords, x_coords],
            dims=["y", "x"],
            attrs={
                'crs': str(crs),
                'transform': transform
            }
        )

    # 写入坐标参考系为 EPSG:4326
    data_array = data_array.rio.write_crs("EPSG:4326", inplace=True)

    # 创建临时的 GeoJSON 文件
    subpixel_tif_temp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Geojson\temp.geojson"

    # 进行子像素等高线提取
    subpixel_contours(da=data_array, z_values=z_values, attribute_df=None, output_path=subpixel_tif_temp)
    # subpixel_contours(da=data_array, z_values=z_values, attribute_df=None, output_path=subpixel_tif)

    # 调用修复函数，应用坐标偏移并保存最终结果
    fix_subpixel_extraction(subpixel_tif_temp, subpixel_tif, x_offset, y_offset)


def convert_geojson_to_polygons_auto(input_geojson: str, line_shp: str, polygon_shp: str):
    """
    将 geojson 中的线要素转为线 shp，并自动构面，输出 polygon shp。
    支持非闭合线段的构面。
    """

    # Step 1: 读取 geojson
    gdf = gpd.read_file(input_geojson)

    # 过滤线要素
    gdf_line = gdf[gdf.geometry.type.isin(['LineString', 'MultiLineString'])].copy()
    if gdf_line.empty:
        raise ValueError("GeoJSON 中不包含有效的线要素。")

    # 保存线文件
    gdf_line.to_file(line_shp)
    print(f"✅ 线要素保存成功：{line_shp}")

    # Step 2: 合并所有线段，统一 polygonize 输入
    all_lines = []
    for geom in gdf_line.geometry:
        if isinstance(geom, LineString):
            all_lines.append(geom)
        elif isinstance(geom, MultiLineString):
            all_lines.extend(geom.geoms)  # ✅ 正确写法

    # 使用 polygonize 自动构建闭合面
    polygons = list(polygonize(all_lines))

    if not polygons:
        raise ValueError("未能从线要素中构建出任何闭合面。请检查线是否构成闭环。")

    # 创建面要素
    gdf_poly = gpd.GeoDataFrame(geometry=polygons, crs=gdf_line.crs)
    gdf_poly.to_file(polygon_shp)

    print(f"✅ 面要素保存成功（共 {len(polygons)} 个）：{polygon_shp}")

def main():
    temp_trush = fr'E:\_OrderingProject\draft0621'
    tif_file = r'E:\_OrderingProject\draft0621\temp5.tif'
    subpixel_output = r'E:\_OrderingProject\draft0621\temp6.geojson'
    subpixel_extraction(input_tif=tif_file, z_values=0, subpixel_tif=subpixel_output)

    tif_temp7 = fr"{temp_trush}\temp7.shp"
    tif_temp8 = fr"{temp_trush}\temp8.shp"
    convert_geojson_to_polygons_auto(
        input_geojson=subpixel_output,
        line_shp=tif_temp7,
        polygon_shp=tif_temp8
    )


if __name__ == '__main__':
    main()


# ====== d_v2.py ======
# -*- coding: utf-8 -*-
"""
作者：23242
更新日期：2025年06月21日

功能：
- 从 GeoTIFF 栅格图像中提取子像素轮廓线
- 封闭并偏移 MultiLineString 几何
- 自动构面并输出面 Shapefile
"""

import os
import tempfile
import numpy as np
import rasterio
from affine import Affine
import xarray as xr
import rioxarray
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from shapely.ops import polygonize
from dea_tools.spatial import subpixel_contours


def add_zero_buffer_array(data, buffer_size=1):
    """
    为栅格数组四周添加一圈 0 值缓冲区。

    :param data: 原始二维数组
    :param buffer_size: 缓冲宽度（单位：像元）
    :return: 扩展后的二维数组
    """
    return np.pad(data, pad_width=buffer_size, mode='constant', constant_values=0)


def extract_subpixel_geometry(input_tif, z_values):
    """
    提取子像素轮廓线，闭合 MultiLineString，返回 GeoDataFrame。

    :param input_tif: 输入的 .tif 路径
    :param z_values: 等值线提取值（如 0）
    :return: GeoDataFrame，包含封闭处理后的 MultiLineString
    """
    with rasterio.open(input_tif) as src:
        data = src.read(1)
        transform = src.transform
        crs = src.crs

        # 添加一圈缓冲像元
        data = add_zero_buffer_array(data, buffer_size=1)
        transform = transform * Affine.translation(-1, -1)

        # 计算偏移量（用于封闭线恢复坐标）
        x_offset = transform[0] / 2
        y_offset = transform[4] / 2

        # 构建 xarray DataArray
        height, width = data.shape
        x_coords = [transform * (col, 0) for col in range(width)]
        y_coords = [transform * (0, row) for row in range(height)]
        x_coords = [x[0] for x in x_coords]
        y_coords = [y[1] for y in y_coords]

        da = xr.DataArray(
            data,
            coords=[y_coords, x_coords],
            dims=["y", "x"],
            attrs={'transform': transform, 'crs': str(crs)}
        ).rio.write_crs(crs)

    # 创建临时 geojson 路径，避免文件锁
    fd, geojson_path = tempfile.mkstemp(suffix=".geojson")
    os.close(fd)

    # 提取子像素轮廓线并写入
    subpixel_contours(da=da, z_values=z_values, attribute_df=None, output_path=geojson_path)

    # 读取轮廓线结果
    gdf = gpd.read_file(geojson_path)
    os.remove(geojson_path)

    # 封闭每个 MultiLineString 并应用坐标偏移
    for idx, row in gdf.iterrows():
        geometry = row.geometry
        if isinstance(geometry, MultiLineString):
            closed_lines = []
            for line in geometry.geoms:
                coords = [(x + x_offset, y + y_offset) for x, y in line.coords]
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                closed_lines.append(LineString(coords))
            gdf.at[idx, 'geometry'] = MultiLineString(closed_lines)
    return gdf


def polygonize_lines(gdf_line):
    """
    将封闭的线要素构面。

    :param gdf_line: GeoDataFrame（LineString 或 MultiLineString）
    :return: Polygon GeoDataFrame
    """
    lines = []
    for geom in gdf_line.geometry:
        if isinstance(geom, LineString):
            lines.append(geom)
        elif isinstance(geom, MultiLineString):
            lines.extend(geom.geoms)

    polygons = list(polygonize(lines))
    if not polygons:
        raise ValueError("未能构建任何闭合面。")

    return gpd.GeoDataFrame(geometry=polygons, crs=gdf_line.crs)


def main():
    tif_file = r'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\d_tif_fixed\ATG\2010\ATG_62W17Nlb.tif'
    polygon_shp_output = r'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\e_shp_subpixel\ATG\2010\ATG_62W17Nlb.shp'

    # Step 1: 提取封闭的子像素轮廓线
    gdf_lines = extract_subpixel_geometry(input_tif=tif_file, z_values=0)

    # Step 2: 构面
    gdf_polygons = polygonize_lines(gdf_lines)

    # Step 3: 保存面要素
    gdf_polygons.to_file(polygon_shp_output)
    print(f"✅ 面要素保存成功：{polygon_shp_output}")


if __name__ == '__main__':
    main()


# ====== d_v3.py ======
# -*- coding: utf-8 -*-
"""
作者：23242
日期：2024年09月18日

功能描述：
- 从栅格图像中提取子像素轮廓线（Subpixel Contours）
- 自动闭合线段（MultiLineString → 封闭 LineString）
- 自动构面（polygonize）
- 全流程仅输出最终结果（面状 Shapefile），不保存中间文件
"""

import os
import rasterio
import rioxarray
import xarray as xr
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, LineString, MultiLineString
from shapely.ops import polygonize
from dea_tools.spatial import subpixel_contours
from tempfile import NamedTemporaryFile


def process_multilinestring(geometry):
    """
    封闭 MultiLineString 中的所有 LineString 线段（若未闭合，则闭合）。

    参数:
        geometry (MultiLineString): 输入几何对象

    返回:
        生成器: 闭合后的 LineString 对象
    """
    if isinstance(geometry, MultiLineString):
        for component in geometry.geoms:
            coords = list(component.coords)
            if coords[0] != coords[-1]:  # 若未闭合，则闭合
                coords.append(coords[0])
            yield LineString(coords)
    else:
        return []


def extract_and_close_subpixel_contours(input_tif, z_values):
    """
    从栅格图像中提取子像素轮廓，并闭合线段，返回 GeoDataFrame。

    参数:
        input_tif (str): 输入 GeoTIFF 文件路径
        z_values (float or int): 提取轮廓的等值线值

    返回:
        gpd.GeoDataFrame: 封闭后的线状要素集
    """
    # 打开栅格并构建 DataArray（含空间信息）
    with rasterio.open(input_tif) as src:
        raster_data = src.read(1)
        transform = src.transform
        crs = src.crs
        height, width = raster_data.shape

        x_coords = [transform * (col, 0) for col in range(width)]
        y_coords = [transform * (0, row) for row in range(height)]
        x_coords = [x[0] for x in x_coords]
        y_coords = [y[1] for y in y_coords]

        data_array = xr.DataArray(
            raster_data,
            coords=[y_coords, x_coords],
            dims=["y", "x"],
            attrs={'crs': str(crs), 'transform': transform}
        )

    data_array.rio.write_crs("EPSG:4326", inplace=True)

    # 使用 NamedTemporaryFile 创建临时输出路径，不保存文件
    with NamedTemporaryFile(suffix='.geojson', delete=True) as tmpfile:
        # 提取子像素轮廓并输出为 GeoJSON（临时文件）
        subpixel_contours(da=data_array, z_values=z_values, attribute_df=None, output_path=tmpfile.name)

        # 读取并处理 MultiLineString（闭合线段）
        gdf = gpd.read_file(tmpfile.name)
        for idx, row in gdf.iterrows():
            geometry = row.geometry
            if isinstance(geometry, MultiLineString):
                closed_lines = list(process_multilinestring(geometry))
                gdf.at[idx, 'geometry'] = MultiLineString(closed_lines)

    return gdf


def polygonize_from_lines(gdf_line: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    从 GeoDataFrame 中的 LineString/MultiLineString 自动构面。

    参数:
        gdf_line (GeoDataFrame): 包含线要素的 GDF

    返回:
        GeoDataFrame: 构面后的 Polygon GDF
    """
    # 收集所有线段用于 polygonize
    all_lines = []
    for geom in gdf_line.geometry:
        if isinstance(geom, LineString):
            all_lines.append(geom)
        elif isinstance(geom, MultiLineString):
            all_lines.extend(geom.geoms)

    # 自动闭合并构建多边形
    polygons = list(polygonize(all_lines))
    if not polygons:
        raise ValueError("❌ 无法从线要素构建闭合面，请检查轮廓提取结果。")

    return gpd.GeoDataFrame(geometry=polygons, crs=gdf_line.crs)


def read_txt_to_list(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    # 去除每行末尾的换行符
    lines = [line.strip() for line in lines]
    return lines


def get_files_absolute_paths(folder_path, suffix=None):
    """
    获取指定文件夹下所有指定后缀的文件的绝对路径名称

    :param folder_path: 指定文件夹的路径
    :param suffix: 文件后缀（可选），如 '.shp'。如果不指定，则获取所有文件的路径
    :return: 指定后缀的文件的绝对路径名称列表
    """
    files_paths = []
    # 遍历指定文件夹
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 如果指定了后缀，则判断文件后缀是否匹配
            if suffix is None or file.endswith(suffix):
                # 获取文件的绝对路径并添加到列表中
                files_paths.append(os.path.abspath(os.path.join(root, file)))
    return files_paths

def shp_subpixel_contours(input_tif, output_shp, z_value):
    # 1️⃣ 提取子像素轮廓，并自动闭合线段
    print("⏳ 提取并闭合子像素轮廓线 ...")
    line_gdf = extract_and_close_subpixel_contours(input_tif=input_tif, z_values=z_value)

    # 2️⃣ 从闭合线段自动构面
    # print("⏳ 构建闭合多边形 ...")
    polygon_gdf = polygonize_from_lines(line_gdf)

    # 3️⃣ 输出为最终面状 Shapefile
    polygon_gdf.to_file(output_shp)
    print(f"✅ 面要素提取完成：{output_shp}")

def main():
    # 初始化处理的国家和年份
    list_year = ['2010', '2015', '2020']
    list_sids = read_txt_to_list(file_path=fr"SIDS_37.txt")

    for year in ['2010']:
    # for year in list_year:
        for sids in ['ATG']:
        # for sids in list_sids:
            # 示例使用
            path_folder = (
                fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp"
                fr"\d_tif_fixed\{sids}\{year}")
            list_map_files = get_files_absolute_paths(path_folder, suffix=fr'.tif')
            for tif_file in list_map_files:

                # 输入与输出路径
                polygon_output = (
                    fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp"
                    fr"\e_shp_subpixel\{sids}\{year}\{os.path.splitext(os.path.basename(tif_file))[0]}.shp")
                # 创建路径
                path_folder = os.path.dirname(polygon_output)
                os.makedirs(path_folder, exist_ok=True)
                print(polygon_output)

                contour_z_value = 0  # 提取子像素轮廓的值
                # 转shp
                try:
                    shp_subpixel_contours(input_tif=tif_file, output_shp=polygon_output, z_value=contour_z_value)
                except Exception as e:
                    pass


if __name__ == '__main__':
    main()


# ====== d_v4.py ======
from dea_tools.spatial import subpixel_contours
import rasterio
import numpy as np
import xarray as xr
import rioxarray
import os
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from rasterio import Affine


# 添加默认条带用于封闭
def add_zero_buffer(input_tif, output_tif, buffer_size=1):
    """
    给指定 GeoTIFF 文件的边界添加一圈栅格值为 0 的像元值。

    参数:
    input_tif (str): 输入的 GeoTIFF 文件路径
    output_tif (str): 输出的 GeoTIFF 文件路径
    buffer_size (int): 要添加的像元缓冲大小，默认值为 1（即一圈像元）
    """
    # 打开输入的 GeoTIFF 文件
    with rasterio.open(input_tif) as src:
        # 获取输入栅格的元数据
        profile = src.profile.copy()

        # 获取原始图像的宽度和高度
        width, height = src.width, src.height

        # 计算新的宽度和高度
        new_width = width + 2 * buffer_size
        new_height = height + 2 * buffer_size

        # 创建新的仿射变换，扩展边界
        new_transform = src.transform * Affine.translation(-buffer_size, -buffer_size)

        # 更新元数据以反映新的宽度、高度和变换
        profile.update({
            'width': new_width,
            'height': new_height,
            'transform': new_transform
        })

        # 创建一个新的数组，初始化为 0，表示边界缓冲的像元值为 0
        new_data = np.zeros((src.count, new_height, new_width), dtype=src.dtypes[0])

        # 读取原始图像数据
        original_data = src.read()

        # 将原始图像放置在新的数据中央
        new_data[:, buffer_size:buffer_size + height, buffer_size:buffer_size + width] = original_data

        # 写入新的 GeoTIFF 文件
        with rasterio.open(output_tif, 'w', **profile) as dst:
            dst.write(new_data)

    print(f'Periphery of fusion boundary: {output_tif}.')


# 定义函数用于处理 MultiLineString，并封闭线段和进行坐标偏移
def process_multilinestring(geometry, x_offset, y_offset):
    """
    处理 MultiLineString，进行坐标偏移并封闭线段。

    :param geometry: 输入的 MultiLineString 对象
    :param x_offset: X 方向偏移量
    :param y_offset: Y 方向偏移量
    :yield: 处理后的 LineString 对象
    """
    if isinstance(geometry, MultiLineString):
        # 遍历 MultiLineString 中的每个组件
        for component in geometry.geoms:
            coords = list(component.coords)  # 获取坐标列表
            start_point = coords[0]  # 线段起点
            end_point = coords[-1]  # 线段终点

            # 添加偏移量到每个坐标
            coords = [(x + x_offset, y + y_offset) for x, y in coords]

            # 如果首尾点不同，则添加首点以封闭线段
            if start_point != end_point:
                coords.append(coords[0])  # 闭合线段
            yield LineString(coords)  # 返回封闭后的 LineString
    else:
        print("Geometry is not MultiLineString.")
        return None


# 定义函数用于修复子像素提取，并将结果保存为 GeoJSON
def fix_subpixel_extraction(input_geojson, output_geojson, x_offset, y_offset):
    """
    处理 MultiLineString 几何对象，并对其应用坐标偏移，保存为 GeoJSON。

    :param input_geojson: 输入的 GeoJSON 文件路径
    :param output_geojson: 输出的 GeoJSON 文件路径
    :param x_offset: X 方向偏移量
    :param y_offset: Y 方向偏移量
    """
    gdf = gpd.read_file(input_geojson)  # 读取输入的 GeoJSON
    for idx, row in gdf.iterrows():
        geometry = row['geometry']  # 获取几何对象
        # 检查几何是否为 MultiLineString
        if isinstance(geometry, MultiLineString):
            closed_components = list(process_multilinestring(geometry, x_offset, y_offset))
            closed_multilinestring = MultiLineString(closed_components)
            gdf.at[idx, 'geometry'] = closed_multilinestring  # 更新几何对象
        else:
            print(f"Feature {idx + 1} is not a MultiLineString.")
    gdf.to_file(output_geojson, driver="GeoJSON")  # 保存到输出文件
    print(f"Subpixel_closed MultiLineString output: {output_geojson}")


# 定义函数进行子像素提取，并生成 GeoJSON
def subpixel_extraction(input_tif, z_values, subpixel_tif):
    """
    从 TIF 文件进行子像素提取，并生成 GeoJSON。

    :param input_tif: 输入的 TIF 文件路径
    :param z_values: 提取等高线的 Z 值
    :param subpixel_tif: 输出的 GeoJSON 文件路径
    """
    # 添加外围封闭栅格圈
    temp_zero_buffer = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Filtering\temp_zero_buffer.tif'
    add_zero_buffer(input_tif=input_tif, output_tif=temp_zero_buffer, buffer_size=1)

    tif_file = temp_zero_buffer
    with rasterio.open(tif_file) as src:
        raster_data = src.read(1)  # 读取栅格数据
        transform = src.transform  # 获取仿射变换
        crs = src.crs  # 获取坐标参考系
        height, width = raster_data.shape

        # 计算偏移量（半个像素的长度）
        x_offset = transform[0] / 2
        y_offset = transform[4] / 2

        # 创建 x, y 坐标数组
        x_coords = [transform * (col, 0) for col in range(width)]
        y_coords = [transform * (0, row) for row in range(height)]
        x_coords = [x[0] for x in x_coords]
        y_coords = [y[1] for y in y_coords]

        # 将栅格数据转换为 xarray DataArray
        data_array = xr.DataArray(
            raster_data,
            coords=[y_coords, x_coords],
            dims=["y", "x"],
            attrs={
                'crs': str(crs),
                'transform': transform
            }
        )

    # 写入坐标参考系为 EPSG:4326
    data_array = data_array.rio.write_crs("EPSG:4326", inplace=True)

    # 创建临时的 GeoJSON 文件
    subpixel_tif_temp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\GEE_Geojson\temp.geojson"

    # 进行子像素等高线提取
    subpixel_contours(da=data_array, z_values=z_values, attribute_df=None, output_path=subpixel_tif_temp)
    # subpixel_contours(da=data_array, z_values=z_values, attribute_df=None, output_path=subpixel_tif)

    # 调用修复函数，应用坐标偏移并保存最终结果
    fix_subpixel_extraction(subpixel_tif_temp, subpixel_tif, x_offset, y_offset)

def read_txt_to_list(file_path: str) -> list[str]:
    """读取文本文件内容并返回一个列表"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return [line.strip() for line in file.readlines()]
    except Exception as e:
        print(f"错误：读取文件 {file_path} 失败 - {str(e)}")
        return []

def get_files_absolute_paths(folder_path, suffix=None):
    """
    获取指定文件夹下所有指定后缀的文件的绝对路径名称

    :param folder_path: 指定文件夹的路径
    :param suffix: 文件后缀（可选），如 '.shp'。如果不指定，则获取所有文件的路径
    :return: 指定后缀的文件的绝对路径名称列表
    """
    files_paths = []
    # 遍历指定文件夹
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 如果指定了后缀，则判断文件后缀是否匹配
            if suffix is None or file.endswith(suffix):
                # 获取文件的绝对路径并添加到列表中
                files_paths.append(os.path.abspath(os.path.join(root, file)))
    return files_paths


def main():
    # 初始化处理的国家和年份
    list_year = ['2010', '2015', '2020']
    list_sids = read_txt_to_list(file_path=fr"SIDS_37.txt")

    for year in ['2010', '2015']:
        # for year in list_year:
        for sids in ['ATG']:
            # for sids in list_sids:
            # 示例使用
            path_folder = (
                fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp"
                fr"\d_tif_fixed\{sids}\{year}")
            list_map_files = get_files_absolute_paths(path_folder, suffix=fr'.tif')
            for tif_file in list_map_files:
                input_tif = (
                    fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\d_tif_fixed"
                    fr"\{sids}\{year}\{os.path.basename(tif_file)}"
                )
                output_json = (
                    fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\e_geojson"
                    fr"\{sids}\{year}\{os.path.splitext(os.path.basename(tif_file))[0]}.geojson")
                os.makedirs(os.path.dirname(output_json), exist_ok=True)
                # 执行转换
                try:
                    subpixel_extraction(input_tif=input_tif, z_values=0, subpixel_tif=output_json)
                except Exception as e:
                    pass


if __name__ == '__main__':
    main()

# ====== e_.py ======
import arcpy
import os
import geopandas as gpd


def geojson_to_shp(input_geojson, output_shp):
    """
    将 GeoJSON 文件转换为 Shapefile 文件。
    :param input_geojson: 输入的 GeoJSON 文件路径
    :param output_shp: 输出的 Shapefile 文件路径
    """
    gdf = gpd.read_file(input_geojson)
    gdf.to_file(output_shp, driver='ESRI Shapefile')
    print(f"[INFO] GeoJSON to Line: {output_shp}")


def line_to_polygon(input_shp, output_shp):
    """
    将线要素 Shapefile 转换为面要素 Shapefile。
    :param input_shp: 输入的线要素 Shapefile
    :param output_shp: 输出的面要素 Shapefile
    """
    temp_shp = r"in_memory\temp"
    arcpy.env.overwriteOutput = True

    # 线转换为面
    arcpy.management.FeatureToPolygon(
        in_features=[input_shp],
        out_feature_class=temp_shp,
        cluster_tolerance="",
        attributes="ATTRIBUTES",
        label_features=""
    )

    # 对面要素进行 Dissolve（可选）
    arcpy.management.Dissolve(
        in_features=temp_shp,
        out_feature_class=output_shp,
        dissolve_field=[],
        statistics_fields=[],
        multi_part="SINGLE_PART",
        unsplit_lines="DISSOLVE_LINES",
        concatenation_separator=""
    )

    print(f"[INFO] Line to Polygon 并保存: {output_shp}")


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


def get_files_absolute_paths(folder_path, suffix=None):
    """
    获取指定文件夹中所有指定后缀文件的绝对路径列表
    :param folder_path: 文件夹路径
    :param suffix: 文件后缀（如 '.shp'），若为 None 则返回所有文件
    :return: 文件路径列表
    """
    files_paths = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if suffix is None or file.endswith(suffix):
                files_paths.append(os.path.abspath(os.path.join(root, file)))
    return files_paths


def process_geojson_to_shp(sids, year, base_dir):
    """
    将指定国家和年份的 GeoJSON 批量转换为线状 Shapefile
    """
    input_dir = os.path.join(base_dir, "e_geojson", sids, year)
    output_dir = os.path.join(base_dir, "f_shp_line", sids, year)
    os.makedirs(output_dir, exist_ok=True)

    geojson_files = get_files_absolute_paths(input_dir, suffix=".geojson")

    for geojson_file in geojson_files:
        output_shp = os.path.join(output_dir, os.path.splitext(os.path.basename(geojson_file))[0] + ".shp")
        geojson_to_shp(geojson_file, output_shp)


def process_line_to_polygon(sids, year, base_dir):
    """
    将线状 Shapefile 批量转换为面状 Shapefile
    """
    input_dir = os.path.join(base_dir, "f_shp_line", sids, year)
    output_dir = os.path.join(base_dir, "g_shp_polygon", sids, year)
    os.makedirs(output_dir, exist_ok=True)

    shp_files = get_files_absolute_paths(input_dir, suffix=".shp")

    for shp_file in shp_files:
        output_shp = os.path.join(output_dir, os.path.basename(shp_file))
        line_to_polygon(shp_file, output_shp)


def main():
    # 设置基本路径（可修改）
    base_dir = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp"

    # 国家和年份列表（可自定义）
    years = ['2010', '2015']
    sids_list = read_txt_to_list("SIDS_37.txt")  # 读取国家 ID 列表

    for year in years:
        for sids in ['ATG']:  # 用于测试，或替换为 sids_list 遍历所有
            print(f"\n[INFO] 开始处理: 国家 = {sids}, 年份 = {year}")
            process_geojson_to_shp(sids, year, base_dir)
            process_line_to_polygon(sids, year, base_dir)


if __name__ == '__main__':
    main()


# ====== f_.py ======
import arcpy
import geopandas as gpd
import pandas as pd  # ← 你漏掉的部分
import os
from shapely.ops import unary_union

def merge_shapefiles_gpd(input_folder, extra_shp, output_shp):
    gdf_list = []

    for fname in os.listdir(input_folder):
        if fname.endswith('.shp'):
            gdf = gpd.read_file(os.path.join(input_folder, fname))
            gdf_list.append(gdf)

    gdf_extra = gpd.read_file(extra_shp)
    gdf_list.append(gdf_extra)

    # 合并属性表 + 保留地理信息
    merged_gdf = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True), crs=gdf_list[0].crs)

    # Dissolve 合并所有几何体，解决边界空洞
    dissolved = unary_union(merged_gdf.geometry)

    # 将合并后结果包装成 GeoDataFrame 并保存
    cleaned_gdf = gpd.GeoDataFrame(geometry=[dissolved], crs=merged_gdf.crs)
    os.makedirs(os.path.dirname(output_shp), exist_ok=True)
    cleaned_gdf.to_file(output_shp)

    print(f"[GPD] Polygon Merge: {output_shp}")

def fix_shapefiles(shp_input, shp_fixed):
    arcpy.env.overwriteOutput = True
    # 转线
    shp_temp_line = "in_memory/shp_temp_line"
    arcpy.management.FeatureToLine(
        in_features=[shp_input],
        out_feature_class=shp_temp_line, cluster_tolerance="", attributes="ATTRIBUTES")
    # 转面
    shp_temp_polygon = "in_memory/shp_temp_polygon"
    arcpy.FeatureToPolygon_management(
        in_features=[shp_temp_line],
        out_feature_class=shp_temp_polygon)
    # 融合分要素
    shp_dissolved = shp_fixed
    # MULTI_PART—输出中将包含多部件要素。 这是默认设置。
    # SINGLE_PART—输出中不包含多部件要素。 系统将为各部件创建单独的要素。
    arcpy.analysis.PairwiseDissolve(
        in_features=shp_temp_polygon,
        out_feature_class=shp_dissolved,
        multi_part="SINGLE_PART")
    print(f"[INFO] Polygon Fixed: {shp_dissolved}")

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

def get_files_absolute_paths(folder_path, suffix=None):
    """
    获取指定文件夹中所有指定后缀文件的绝对路径列表
    :param folder_path: 文件夹路径
    :param suffix: 文件后缀（如 '.shp'），若为 None 则返回所有文件
    :return: 文件路径列表
    """
    files_paths = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if suffix is None or file.endswith(suffix):
                files_paths.append(os.path.abspath(os.path.join(root, file)))
    return files_paths


if __name__ == '__main__':
    list_year = ['2010', '2015', '2020']
    list_sids = read_txt_to_list(file_path=fr"SIDS_37.txt")

    for year in ['2010', '2015']:
        # for year in list_year:
        for sids in ['ATG']:
            folder = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\g_shp_polygon\{sids}\{year}"
            extra = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\g_shp_polygon\{sids}\{sids}_add.shp"
            output = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\_draft\{sids}_{year}.shp"

            merge_shapefiles_gpd(folder, extra, output)

            shp_input = output
            shp_fixed = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\h_shp_merge\{sids}\{sids}_{year}.shp"

            os.makedirs(os.path.dirname(shp_fixed), exist_ok=True)
            fix_shapefiles(shp_input, shp_fixed)



# ====== g_.py ======
# -*- coding: utf-8 -*-
"""
Generated by ArcGIS ModelBuilder on : 2025-04-19 13:25:47
"""
import os
import arcpy

arcpy.env.overwriteOutput = True

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

def main():
    list_year = ['2010', '2015', '2020']
    list_sids = read_txt_to_list(file_path=fr"draft.txt")

    # for year in ['2020']:
    for year in list_year:
        for sids in ['SUR']:
        # for sids in list_sids:

            shp_input = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\h_shp_merge\{sids}\{sids}_{year}.shp"
            shp_line_smooth = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\i_shp_smooth\{sids}\{sids}_CL_{year}.shp"
            shp_polygon_smooth = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\i_shp_smooth\{sids}\{sids}_BV_{year}.shp"
            os.makedirs(os.path.dirname(shp_polygon_smooth), exist_ok=True)

            # Process: 合并 (合并) (management)
            temp_merge = fr'in_memory\shp_merge'
            arcpy.management.Merge(
                inputs=[shp_input],
                output=temp_merge)

            # Process: 成对融合 (成对融合) (analysis)
            temp_dissolve = fr'in_memory\shp_dissolve'
            arcpy.analysis.PairwiseDissolve(
                in_features=temp_merge, out_feature_class=temp_dissolve,
                multi_part="MULTI_PART")

            # Process: 平滑要素
            arcpy.cartography.SmoothPolygon(
                in_features=temp_dissolve,
                out_feature_class=shp_polygon_smooth,  # 输出平滑处理后的图层
                algorithm="PAEK",  # 使用 PAEK 算法进行平滑
                tolerance="90 Meters",  # 平滑的容忍度为 50 米
                endpoint_option="FIXED_ENDPOINT",  # 固定端点
                error_option="NO_CHECK"  # 不检查错误
            )

            # Process: 要素转线
            arcpy.management.FeatureToLine(
                in_features=shp_polygon_smooth,
                out_feature_class=shp_line_smooth)

            # Process: 计算几何属性 (计算几何属性) (management)
            arcpy.management.CalculateGeometryAttributes(
                in_features=shp_polygon_smooth,
                geometry_property=[["Leng_Geo", "PERIMETER_LENGTH_GEODESIC"], ["Area_Geo", "AREA_GEODESIC"]],
                length_unit="KILOMETERS", area_unit="SQUARE_KILOMETERS", coordinate_format="SAME_AS_INPUT")

            print(fr'merge_calculate: {shp_polygon_smooth}')


if __name__ == '__main__':
    main()


# ====== 删除文件夹.py ======
import shutil

def delete_folder(folder_path):
    try:
        # 删除文件夹
        shutil.rmtree(folder_path)
        print(f"文件夹 {folder_path} 已成功删除！")
    except FileNotFoundError:
        print(f"文件夹 {folder_path} 不存在！")
    except PermissionError:
        print(f"没有权限删除文件夹 {folder_path}，请检查文件夹的权限！")
    except Exception as e:
        print(f"删除文件夹时出错：{e}")

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
    # 全局环境设置
    year_list = [2000, 2010, 2015, 2020]
    # year_list = [2020]
    list_sids = read_txt_to_list(file_path=fr"SIDS_37.txt")
    # sids_cou_list = ['SGP']
    for sid in list_sids:
        for year in year_list:
            # 使用示例
            folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\{sid}\{year}"
            delete_folder(folder_path)

# ====== 删除第三方点的不匹配点.py ======
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







# ====== 剔除小型斑块.py ======
import numpy as np
import rasterio
from scipy.ndimage import label


def remove_small_clusters(data, min_cluster_size=50):
    """
    移除小于指定大小的连通区域（使用8邻接规则）。

    参数:
        data (np.ndarray): 输入的二维栅格数据。
        min_cluster_size (int): 需要保留的最小斑块大小（像元数）。

    返回:
        np.ndarray: 已清除小团块的数组。
    """
    mask = data != 0
    structure = np.array([[1, 1, 1],
                          [1, 1, 1],
                          [1, 1, 1]], dtype=np.uint8)
    labeled_array, _ = label(mask, structure=structure)
    counts = np.bincount(labeled_array.ravel())

    filtered_data = np.copy(data)
    for label_id, count in enumerate(counts):
        if label_id == 0:
            continue
        if count < min_cluster_size:
            filtered_data[labeled_array == label_id] = 0
    return filtered_data


def apply_cluster_filter(input_path, output_path, min_cluster_size=50):
    """
    处理输入 GeoTIFF，去除小团块并保存。

    参数:
        input_path (str): 输入文件路径。
        output_path (str): 输出文件路径。
        min_cluster_size (int): 最小像元数（保留斑块大小）。
    """
    with rasterio.open(input_path) as src:
        profile = src.profile
        data = src.read(1)
        filtered_data = remove_small_clusters(data, min_cluster_size)
        profile.update(dtype=rasterio.float32)
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(filtered_data.astype(np.float32), 1)


def main():
    """主函数：处理单个 GeoTIFF 文件"""
    tif_input = r'C:\Users\23042\Desktop\test\43E13Sru_ls578_Index_f_otsu.tif'
    tif_output = r'C:\Users\23042\Desktop\test\43E13Sru_ls578_Index_f_otsu_re.tif'
    min_cluster_size = 4
    apply_cluster_filter(tif_input, tif_output, min_cluster_size)


if __name__ == '__main__':
    main()


# ====== 将第三方矢量数据合并.py ======
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

# ====== 影像otsu分类.py ======
import numpy as np
import cv2
from osgeo import gdal, gdal_array


def otsu_threshold_with_gdal(input_tif_path, output_tif_path):
    """
    读取单波段 GeoTIFF，使用 Otsu 算法进行二值化，并保持地理参考信息输出。

    参数:
        input_tif_path (str): 输入单波段 GeoTIFF 路径。
        output_tif_path (str): 输出二值化 GeoTIFF 路径。
    """
    # 打开输入影像
    dataset = gdal.Open(input_tif_path, gdal.GA_ReadOnly)
    if dataset is None:
        raise IOError(f"Could not open file: {input_tif_path}")

    # 保存地理参考
    geo_transform = dataset.GetGeoTransform()
    projection = dataset.GetProjection()

    # 读取第一波段数据
    band = dataset.GetRasterBand(1)
    data = band.ReadAsArray()

    # 转为 uint8 并取绝对值，确保数据类型符合 Otsu 要求
    data = np.abs(data).astype(np.uint8)

    # Otsu 二值化：自动计算阈值，输出 0/255
    _, binary_image = cv2.threshold(data, 0, 255,
                                    cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 创建输出 GeoTIFF
    driver = gdal.GetDriverByName('GTiff')
    out_dataset = driver.Create(output_tif_path,
                                binary_image.shape[1],
                                binary_image.shape[0],
                                1,
                                gdal.GDT_Byte)
    out_dataset.SetGeoTransform(geo_transform)
    out_dataset.SetProjection(projection)

    # 写入二值波段
    out_band = out_dataset.GetRasterBand(1)
    out_band.WriteArray(binary_image)
    out_band.FlushCache()  # 强制落盘

    # 关闭数据集
    out_dataset = None
    dataset = None

    print(f'Otsu thresholded image saved to: {output_tif_path}')


def main():
    """
    主函数：设置输入/输出路径并调用 Otsu 二值化。
    """
    input_tif_path = r'C:\Users\23042\Desktop\test\43E13Sru_ls578_Index_f.tif'
    output_tif_path = r'C:\Users\23042\Desktop\test\43E13Sru_ls578_Index_f_otsu.tif'

    otsu_threshold_with_gdal(input_tif_path, output_tif_path)


if __name__ == '__main__':
    main()


# ====== 影像噪声过滤.py ======
import os
import numpy as np
import rasterio
from scipy.ndimage import maximum_filter


def filter_by_local_max(data, window_size=31, max_threshold=0.5):
    """
    使用最大滤波器过滤局部区域低于最大阈值的像元。

    参数:
        data (np.ndarray): 输入二维数组（单波段栅格数据）。
        window_size (int): 最大滤波器窗口大小（应为奇数）。
        max_threshold (float): 最大值阈值。

    返回:
        np.ndarray: 滤波后的数组。
    """
    local_max = maximum_filter(data, size=window_size, mode='nearest')
    mask = local_max < max_threshold

    filtered = data.copy()
    filtered[mask] = 0
    return filtered


def apply_filter_to_raster(input_path, output_path, window_size=31, max_threshold=0.5):
    """
    对指定栅格图像应用局部最大值滤波，并保存输出。

    参数:
        input_path (str): 输入的 GeoTIFF 文件路径。
        output_path (str): 输出的 GeoTIFF 文件路径。
        window_size (int): 滤波器窗口大小。
        max_threshold (float): 最大值阈值。
    """
    with rasterio.open(input_path) as src:
        profile = src.profile
        data = src.read(1)

        filtered_data = filter_by_local_max(data, window_size, max_threshold)

        profile.update(dtype=rasterio.float32, nodata=None)
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(filtered_data.astype(np.float32), 1)


def main():
    input_tif = r'C:\Users\23042\Desktop\test\43E13Sru_ls578_Index.tif'
    output_tif = r'C:\Users\23042\Desktop\test\43E13Sru_ls578_Index_f.tif'
    apply_filter_to_raster(input_tif, output_tif, window_size=31, max_threshold=20)


if __name__ == '__main__':
    main()


# ====== 影像孔隙填补.py ======
import numpy as np
import rasterio
from scipy.ndimage import binary_fill_holes


def fill_internal_holes(input_tif, output_tif):
    """
    填充栅格中目标区域内部的小孔隙（基于最大值区域）。

    参数:
        input_tif (str): 输入的二值 GeoTIFF。
        output_tif (str): 输出文件路径。
    """
    with rasterio.open(input_tif) as src:
        profile = src.profile
        data = src.read(1)

        # 找到唯一值，识别“前景”大值
        unique_values = np.unique(data)
        if len(unique_values) != 2:
            raise ValueError("该函数适用于二值图像（仅包含两个唯一值）")

        foreground_value = max(unique_values)
        background_value = min(unique_values)

        # 创建布尔掩膜，填充内部孔洞
        binary_mask = data == foreground_value
        filled_mask = binary_fill_holes(binary_mask)

        # 构建填充后的图像：前景区域设为 foreground_value，其他为 background
        filled_data = np.where(filled_mask, foreground_value, background_value)

        # 更新 profile
        profile.update(dtype=rasterio.float32)

        with rasterio.open(output_tif, 'w', **profile) as dst:
            dst.write(filled_data.astype(np.float32), 1)


def main():
    input_tif = r'C:\Users\23042\Desktop\test\43E13Sru_ls578_Index_f_otsu_re.tif'
    output_tif = r'C:\Users\23042\Desktop\test\43E13Sru_ls578_re_fi.tif'
    fill_internal_holes(input_tif, output_tif)


if __name__ == '__main__':
    main()


# ====== 样本点全匹配.py ======
import os
import arcpy


def create_sample_points(StP_GID, S_CL, SP_GID):
    # To allow overwriting outputs change overwriteOutput option to True.
    arcpy.env.overwriteOutput = True

    # Process: 复制要素 (复制要素) (management)
    StP_Copy_shp = fr"in_memory\StP_Copy"
    arcpy.management.CopyFeatures(in_features=StP_GID, out_feature_class=StP_Copy_shp)

    # Process: 邻近分析 (邻近分析) (analysis)# search_radius="500 Meters",
    Stp_Near = arcpy.analysis.Near(in_features=StP_Copy_shp, near_features=[S_CL],
                                   location="LOCATION", method="GEODESIC", search_radius="50000 Meters",
                                   field_names=[["NEAR_FID", "NEAR_FID"], ["NEAR_DIST", "NEAR_DIST"],
                                                ["NEAR_X", "NEAR_X"], ["NEAR_Y", "NEAR_Y"]])[0]

    # Process: XY 表转点 (XY 表转点) (management)
    arcpy.management.XYTableToPoint(in_table=Stp_Near, out_feature_class=SP_GID,
                                    x_field="NEAR_X", y_field="NEAR_Y")
    print(SP_GID, 'finish')

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
    # 全局环境设置
    # year_list = [2010, 2015, 2020]
    year_list = [2015]
    list_sids = read_txt_to_list(file_path=fr"SIDS_37.txt")
    # sids_cou_list = ['SGP']
    for sid in list_sids:
        for year in year_list:
            work_folder = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\{sid}\{year}"
            standard_points = (
                fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\_kml"
                fr"\{sid}\{sid}_match_{year}.shp"
            )
            # 初始化第三方文件夹
            third_path_output = os.path.join(work_folder, fr"ThirdPartyDataSource")
            # 确定是否存在文件夹
            os.makedirs(os.path.join(third_path_output), exist_ok=True)
            # SIDS_BV :
            # sample_lines = (
            #     fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\temp\i_shp_smooth"
            #     fr"\{sid}\{sid}_CL_{year}.shp")
            # sample_points = os.path.join(work_folder, fr"SP_{sid}_{str(year)[-2:]}.shp")
            # OSM :
            # sample_lines = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\\" \
            #                fr"OSM\{sid}\_{sid}_merge.shp"
            # sample_points = os.path.join(third_path_output, fr"OSM_SP_{sid}_{str(year)[-2:]}.shp")
            # # GCL_FCS30 :
            # sample_lines = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\\" \
            #                fr"GCL_FCS30_{str(year)[-2:]}\{sid}\_{sid}_merge.shp"
            # sample_points = os.path.join(third_path_output, fr"GCL_SP_{sid}_{str(year)[-2:]}.shp")
            # # GSV :
            # sample_lines = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\\" \
            #                fr"GSV\{sid}\_{sid}_merge.shp"
            # sample_points = os.path.join(third_path_output, fr"GSV_SP_{sid}_{str(year)[-2:]}.shp")
            # GMSSD_2015 :
            sample_lines = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\\" \
                           fr"GMSSD_2015\{sid}\_{sid}_merge.shp"
            sample_points = os.path.join(third_path_output, fr"GMSSD_SP_{sid}_{str(year)[-2:]}.shp")

            create_sample_points(standard_points, sample_lines, sample_points)


# ====== 海岸线json.py ======
from dea_tools.spatial import subpixel_contours
import rasterio
import numpy as np
import xarray as xr
import rioxarray
import os
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from rasterio import Affine


# 添加默认条带用于封闭
def add_zero_buffer(input_tif, output_tif, buffer_size=1):
    """
    给指定 GeoTIFF 文件的边界添加一圈栅格值为 0 的像元值。

    参数:
    input_tif (str): 输入的 GeoTIFF 文件路径
    output_tif (str): 输出的 GeoTIFF 文件路径
    buffer_size (int): 要添加的像元缓冲大小，默认值为 1（即一圈像元）
    """
    # 打开输入的 GeoTIFF 文件
    with rasterio.open(input_tif) as src:
        # 获取输入栅格的元数据
        profile = src.profile.copy()

        # 获取原始图像的宽度和高度
        width, height = src.width, src.height

        # 计算新的宽度和高度
        new_width = width + 2 * buffer_size
        new_height = height + 2 * buffer_size

        # 创建新的仿射变换，扩展边界
        new_transform = src.transform * Affine.translation(-buffer_size, -buffer_size)

        # 更新元数据以反映新的宽度、高度和变换
        profile.update({
            'width': new_width,
            'height': new_height,
            'transform': new_transform
        })

        # 创建一个新的数组，初始化为 0，表示边界缓冲的像元值为 0
        new_data = np.zeros((src.count, new_height, new_width), dtype=src.dtypes[0])

        # 读取原始图像数据
        original_data = src.read()

        # 将原始图像放置在新的数据中央
        new_data[:, buffer_size:buffer_size + height, buffer_size:buffer_size + width] = original_data

        # 写入新的 GeoTIFF 文件
        with rasterio.open(output_tif, 'w', **profile) as dst:
            dst.write(new_data)

    print(f'Periphery of fusion boundary: {output_tif}.')


# 定义函数用于处理 MultiLineString，并封闭线段和进行坐标偏移
def process_multilinestring(geometry, x_offset, y_offset):
    """
    处理 MultiLineString，进行坐标偏移并封闭线段。

    :param geometry: 输入的 MultiLineString 对象
    :param x_offset: X 方向偏移量
    :param y_offset: Y 方向偏移量
    :yield: 处理后的 LineString 对象
    """
    if isinstance(geometry, MultiLineString):
        # 遍历 MultiLineString 中的每个组件
        for component in geometry.geoms:
            coords = list(component.coords)  # 获取坐标列表
            start_point = coords[0]  # 线段起点
            end_point = coords[-1]  # 线段终点

            # 添加偏移量到每个坐标
            coords = [(x + x_offset, y + y_offset) for x, y in coords]

            # 如果首尾点不同，则添加首点以封闭线段
            if start_point != end_point:
                coords.append(coords[0])  # 闭合线段
            yield LineString(coords)  # 返回封闭后的 LineString
    else:
        print("Geometry is not MultiLineString.")
        return None


# 定义函数用于修复子像素提取，并将结果保存为 GeoJSON
def fix_subpixel_extraction(input_geojson, output_geojson, x_offset, y_offset):
    """
    处理 MultiLineString 几何对象，并对其应用坐标偏移，保存为 GeoJSON。

    :param input_geojson: 输入的 GeoJSON 文件路径
    :param output_geojson: 输出的 GeoJSON 文件路径
    :param x_offset: X 方向偏移量
    :param y_offset: Y 方向偏移量
    """
    gdf = gpd.read_file(input_geojson)  # 读取输入的 GeoJSON
    for idx, row in gdf.iterrows():
        geometry = row['geometry']  # 获取几何对象
        # 检查几何是否为 MultiLineString
        if isinstance(geometry, MultiLineString):
            closed_components = list(process_multilinestring(geometry, x_offset, y_offset))
            closed_multilinestring = MultiLineString(closed_components)
            gdf.at[idx, 'geometry'] = closed_multilinestring  # 更新几何对象
        else:
            print(f"Feature {idx + 1} is not a MultiLineString.")
    gdf.to_file(output_geojson, driver="GeoJSON")  # 保存到输出文件
    print(f"Subpixel_closed MultiLineString output: {output_geojson}")


# 定义函数进行子像素提取，并生成 GeoJSON
def subpixel_extraction(input_tif, z_values, subpixel_tif):
    """
    从 TIF 文件进行子像素提取，并生成 GeoJSON。

    :param input_tif: 输入的 TIF 文件路径
    :param z_values: 提取等高线的 Z 值
    :param subpixel_tif: 输出的 GeoJSON 文件路径
    """
    # 添加外围封闭栅格圈
    add_zero_buffer(input_tif=input_tif, output_tif=subpixel_tif, buffer_size=1)

    with rasterio.open(subpixel_tif) as src:
        raster_data = src.read(1)  # 读取栅格数据
        transform = src.transform  # 获取仿射变换
        crs = src.crs  # 获取坐标参考系
        height, width = raster_data.shape

        # 计算偏移量（半个像素的长度）
        x_offset = transform[0] / 2
        y_offset = transform[4] / 2

        # 创建 x, y 坐标数组
        x_coords = [transform * (col, 0) for col in range(width)]
        y_coords = [transform * (0, row) for row in range(height)]
        x_coords = [x[0] for x in x_coords]
        y_coords = [y[1] for y in y_coords]

        # 将栅格数据转换为 xarray DataArray
        data_array = xr.DataArray(
            raster_data,
            coords=[y_coords, x_coords],
            dims=["y", "x"],
            attrs={
                'crs': str(crs),
                'transform': transform
            }
        )

    # 写入坐标参考系为 EPSG:4326
    data_array = data_array.rio.write_crs("EPSG:4326", inplace=True)

    # 进行子像素等高线提取
    subpixel_contours(da=data_array, z_values=z_values, attribute_df=None, output_path=subpixel_tif)

    # 调用修复函数，应用坐标偏移并保存最终结果
    fix_subpixel_extraction(subpixel_tif, subpixel_tif, x_offset, y_offset)


def main():
    input_tif = fr"C:\Users\23042\Desktop\test\43E13Sru_ls578_re_fi.tif"
    output_json = fr"C:\Users\23042\Desktop\test\43E13Sru_ls578_re_fi.geojson"
    subpixel_extraction(input_tif=input_tif, z_values=0, subpixel_tif=output_json)


if __name__ == '__main__':
    main()

# ====== 海岸线polygon.py ======
import arcpy


def line_to_polygon(input_shp, output_shp):
    """
    将线要素 Shapefile 转换为面要素 Shapefile。
    :param input_shp: 输入的线要素 Shapefile
    :param output_shp: 输出的面要素 Shapefile
    """
    temp_shp = r"in_memory\temp"

    # 线转换为面
    arcpy.management.FeatureToPolygon(
        in_features=[input_shp],
        out_feature_class=temp_shp,
        cluster_tolerance="0.001 Meters",  # 设置容差
        attributes="ATTRIBUTES",
        label_features=""
    )

    # 对面要素进行 Dissolve（可选）
    arcpy.management.Dissolve(
        in_features=temp_shp,
        out_feature_class=output_shp,
        dissolve_field=[],
        statistics_fields=[],
        multi_part="SINGLE_PART",
        unsplit_lines="DISSOLVE_LINES",
        concatenation_separator=""
    )

    print(f"[INFO] Line to Polygon 并保存: {output_shp}")

def geojson_to_polygon(input_geojson, output_shp):
    temp_shp_line = fr"C:\Users\23042\Desktop\test\43E13Sru_ls578_polyline.shp"

    arcpy.conversion.JSONToFeatures(
        in_json_file=input_geojson, out_features=temp_shp_line, geometry_type='POLYLINE')
    print(f"[INFO] GeoJSON to Line: {output_shp}")

    line_to_polygon(input_shp=temp_shp_line, output_shp=output_shp)

def main():
    json_input = fr"C:\Users\23042\Desktop\test\43E13Sru_ls578_re_fi.geojson"
    polygon_output = fr"C:\Users\23042\Desktop\test\43E13Sru_ls578_polygon.shp"

    geojson_to_polygon(json_input, polygon_output)

if __name__ == '__main__':
    main()

# ====== 筛除无效标准点并导出为kml.py ======
# -*- coding: utf-8 -*-
"""
Generated by ArcGIS ModelBuilder on : 2025-06-29 11:20:42
"""
import os

import arcpy
from osgeo import ogr

arcpy.env.overwriteOutput = True

def poi_kml(shp_poi_check, shp_poi, kml_select):  # _draft

    # Process: 按位置选择图层 (按位置选择图层) (management)
    layer_shp_select = arcpy.management.SelectLayerByLocation(
        in_layer=[shp_poi_check], overlap_type="INTERSECT",
        select_features=shp_poi, search_distance="100 Meters",
        selection_type="NEW_SELECTION",
        )
    shp_select = kml_select.replace(".kml", ".shp")
    arcpy.conversion.ExportFeatures(
        in_features=layer_shp_select,
        out_features=shp_select
    )
    arcpy.management.SelectLayerByAttribute(layer_shp_select, "CLEAR_SELECTION")

    # 打开 SHP 文件
    input_datasource = ogr.Open(shp_select, 0)  # 0 表示只读模式
    if input_datasource is None:
        print("无法打开 SHP 文件，请检查文件路径是否正确！")
        return

    # 获取第一个图层（通常 SHP 文件只有一个图层）
    input_layer = input_datasource.GetLayer()

    # 创建 KML 文件
    driver = ogr.GetDriverByName('KML')  # 指定输出格式为 KML
    output_datasource = driver.CreateDataSource(kml_select)
    if output_datasource is None:
        print("无法创建 KML 文件，请检查文件路径是否正确！")
        return

    # 复制图层结构到 KML 文件
    output_layer = output_datasource.CopyLayer(input_layer, input_layer.GetName())

    # 保存并关闭数据源
    input_datasource.Destroy()
    output_datasource.Destroy()

    print(f"转换完成！KML 文件已保存到 {kml_select}")


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
    list_year = ['2010', '2015', '2020']
    list_sids = read_txt_to_list(file_path=fr"SIDS_37.txt")

    for sid in list_sids:
        for year in list_year:
            shp_stp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\{sid}\{year}\StP_{sid}_{year[-2:]}.shp"
            shp_sp = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\{sid}\{year}\SP_{sid}_{year[-2:]}.shp"
            kml_out = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\_kml\{sid}\{sid}_match_{year}.kml"
            os.makedirs(os.path.dirname(kml_out), exist_ok=True)
            poi_kml(shp_poi_check=shp_stp, shp_poi=shp_sp, kml_select=kml_out)




# ====== 读取dbf行数.py ======
from dbfread import DBF


def get_dbf_row_count(dbf_file):
    try:
        # 打开 DBF 文件
        table = DBF(dbf_file)

        # 获取行数
        row_count = len(table)

        # if row_count != 100:

        print(f"DBF 文件 {dbf_file} 中的行数为：{row_count}")
        return row_count
    except Exception as e:
        print(f"读取 DBF 文件时出错：{e}")


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
    list_year = ['2010', '2015', '2020']
    list_sids = read_txt_to_list(file_path=fr"SIDS_37.txt")

    for sid in list_sids:
        for year in list_year:
            dbf_file_path = \
                fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\_kml\{sid}\{sid}_match_{year}.dbf"
            get_dbf_row_count(dbf_file_path)

# ====== 谷歌标准点构建.py ======
import geopandas as gpd
import warnings
import os


def convert_kml_to_shp(kml_file, shp_file):
    """
    将KML文件转换为SHP文件，处理列名和警告。

    参数:
    kml_file (str): 输入的KML文件路径。
    shp_file (str): 输出的SHP文件路径。
    """
    # 关闭警告
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)

    try:
        # 读取KML文件
        gdf = gpd.read_file(kml_file, driver='KML')

        # 可选：修改列名，确保不超过10个字符
        gdf.columns = [col[:10] for col in gdf.columns]

        # 将读取的数据保存为SHP文件
        gdf.to_file(shp_file, driver='ESRI Shapefile')

        print(f"Shapefile saved to {shp_file}")

    except Exception as e:
        print(f"An error occurred: {e}")


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
    year_list = [2010, 2015, 2020]
    list_sids = read_txt_to_list(file_path=fr"SIDS_37.txt")

    for sid in list_sids:
        for year in year_list:
            # 示例使用
            folder_path = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\{sid}"
            kml_file = os.path.join(folder_path, fr"{sid}_{str(year % 100).zfill(2)}.kml")
            # 转样本点
            os.makedirs(os.path.join(folder_path, str(year)), exist_ok=True)
            shp_file = os.path.join(folder_path, fr"{year}\StP_{sid}_{str(year % 100).zfill(2)}.shp")

            convert_kml_to_shp(kml_file, shp_file)

