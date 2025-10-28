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
