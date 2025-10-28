from osgeo import gdal
gdal.UseExceptions()   # 或者 gdal.DontUseExceptions()

# 输入和输出路径
input_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\GEE_4_10_neg_mndwi\SIDs_Grid_2020\125E9Srb_ls578_Index.tif"
output_path = r"E:\_GoogleDrive\125E9Srb_ls578_Index.tif"

# 打开原始文件
src_ds = gdal.Open(input_path)
if src_ds is None:
    raise FileNotFoundError(f"无法打开输入文件：{input_path}")

# 设置压缩选项
options = [
    'COMPRESS=LZW',  # 使用 LZW 压缩（无损压缩）
    'TILED=YES',     # 可选：启用瓦片存储，提高读取效率
    'BIGTIFF=IF_NEEDED'
]

# 创建压缩后的输出文件
gdal.Translate(
    destName=output_path,
    srcDS=src_ds,
    options=gdal.TranslateOptions(creationOptions=options)
)

print(f"压缩完成：{output_path}")