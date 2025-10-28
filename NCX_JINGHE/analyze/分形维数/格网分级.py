import os, logging
import geopandas as gpd
import pandas as pd
from shapely.geometry import box

# -------------------- 配置 --------------------
INPUT_GRID = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\Analyze\fractal_dimension\grids\grids_4800m.shp"
OUT_DIR    = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\Analyze\fractal_dimension\grids"
SPLIT_LENGTH = [2400, 300]   # 单位：米

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# -------------------- 工具函数 --------------------
def split_cell(cell_geom, size):
    """把单个 4800 m 格网拆成 size m 的小格网"""
    minx, miny, maxx, maxy = cell_geom.bounds
    cols = int((maxx - minx) / size)
    rows = int((maxy - miny) / size)
    geoms = [box(minx + i*size, miny + j*size,
                 minx + (i+1)*size, miny + (j+1)*size)
             for i in range(cols) for j in range(rows)]
    return gpd.GeoDataFrame(geometry=geoms, crs="EPSG:3857")

# -------------------- 主流程 --------------------
def run_one_length(length):
    logging.info(f"开始拆分 {length} m 格网（仅写出，不做筛选）")
    out_file = os.path.join(OUT_DIR, f"grids_{length}m_all.shp")
    if os.path.exists(out_file):
        logging.info(f"{out_file} 已存在，跳过")
        return

    grid_4800 = gpd.read_file(INPUT_GRID).to_crs("EPSG:3857")

    # 生成所有小格网
    small_grids = []
    for _, row in grid_4800.iterrows():
        small_grids.append(split_cell(row.geometry, length))
    small_grids = pd.concat(small_grids, ignore_index=True)

    small_grids.to_file(out_file)
    logging.info(f"已写出 {out_file}，共 {len(small_grids)} 个小格网")

# -------------------- 入口 --------------------
if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    for L in SPLIT_LENGTH:
        run_one_length(L)
    logging.info("全部完成！")