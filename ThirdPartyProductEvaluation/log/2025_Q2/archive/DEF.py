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
