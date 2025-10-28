import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import os
import pandas as pd
from shapely.ops import unary_union

# =========================
# 文件路径配置
# =========================
coastline_fp = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\_dataet_SIDS_SV\SIDS_SV_polyline_2010.shp"
grid_files = {
    12000: r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\Analyze\fractal_dimension\grids\grids_12000m.shp",
    4800:  r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\Analyze\fractal_dimension\grids\grids_4800m.shp",
    2400:  r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\Analyze\fractal_dimension\grids\grids_2400m.shp",
    900:   r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\Analyze\fractal_dimension\grids\grids_900m.shp",
    300:   r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\Analyze\fractal_dimension\grids\grids_300m.shp"
}

# =========================
# 读取海岸线数据
# =========================
print("加载海岸线数据...")
coastline = gpd.read_file(coastline_fp)

# 修复无效几何
coastline = coastline[coastline.is_valid].copy()
if not coastline.is_valid.all():
    coastline["geometry"] = coastline.buffer(0)

# 统一 CRS 为米制投影（优先使用海岸线 CRS）
target_crs = coastline.crs
if target_crs is None:
    raise ValueError("海岸线数据没有 CRS，请手动指定投影坐标系！")

# 重新构建空间索引
coastline_sindex = coastline.sindex

# =========================
# 统计函数
# =========================
def count_occupied(grids, coastline, coastline_sindex, batch_size=1000):
    """统计被海岸线占用的格网数量（分块处理）"""
    occupied_count = 0
    for i in tqdm(range(0, len(grids), batch_size), desc="处理格网", leave=False):
        batch = grids.iloc[i:i+batch_size]
        for _, grid in batch.iterrows():
            # 空间索引找候选
            possible_matches_index = list(coastline_sindex.intersection(grid.geometry.bounds))
            possible_matches = coastline.iloc[possible_matches_index]
            # intersects 表示格网与海岸线有任意接触（包括跨越、相交、擦边）
            if possible_matches.intersects(grid.geometry).any():
                occupied_count += 1
    return occupied_count

# =========================
# 遍历不同尺度的格网
# =========================
epsilons = []
counts = []

for res, fp in grid_files.items():
    print(f"\n处理格网: {res}m ({os.path.basename(fp)})")
    grids = gpd.read_file(fp)

    # 修复无效几何
    grids = grids[grids.is_valid].copy()
    if not grids.is_valid.all():
        grids["geometry"] = grids.buffer(0)

    # 统一 CRS
    if grids.crs != target_crs:
        grids = grids.to_crs(target_crs)

    occupied = count_occupied(grids, coastline, coastline_sindex)
    print(f"  占有格网数: {occupied}")

    epsilons.append(res)
    counts.append(occupied)

# =========================
# 分形维数计算
# =========================
eps_arr = np.array(epsilons)
counts_arr = np.array(counts)

# 剔除占有格网数 = 0 的情况，避免 log(0)
mask = counts_arr > 0
eps_arr = eps_arr[mask]
counts_arr = counts_arr[mask]

log_eps = -np.log(eps_arr)
log_counts = np.log(counts_arr)

coef = np.polyfit(log_eps, log_counts, 1)
fractal_dimension = coef[0]

print("\n====== 结果 ======")
for e, c in zip(epsilons, counts):
    print(f"尺度 {e:>6} m : 占有格网数 = {c}")
print(f"\n估计分形维数: {fractal_dimension:.3f}")

# =========================
# 可视化
# =========================
plt.figure()
plt.plot(log_eps, log_counts, 'o-', label="Box-counting")
plt.plot(log_eps, np.polyval(coef, log_eps), 'r--', label=f"拟合 D={fractal_dimension:.3f}")
plt.xlabel("-log(ε)")
plt.ylabel("log(N(ε))")
plt.legend()
plt.show()

# =========================
# 导出结果 CSV
# =========================
df_result = pd.DataFrame({
    "grid_size_m": epsilons,
    "occupied_grids": counts
})
df_result["fractal_dimension"] = fractal_dimension
df_result.to_csv("fractal_dimension_results.csv", index=False, encoding="utf-8-sig")

print("\n结果已保存到 fractal_dimension_results.csv")
