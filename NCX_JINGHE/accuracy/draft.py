import pandas as pd

# 定义输入和输出文件路径
input_file = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\Statistics\第三方数据长度汇总.xlsx"
output_file = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1_compile\Statistics\第三方数据长度汇总_制图表.xlsx"

# 读取Excel文件的所有子表
xls = pd.ExcelFile(input_file)

# 创建一个空的DataFrame，用于存储汇总结果
summary_df = pd.DataFrame(columns=["Sheet Name", "Leng_Geo Sum"])

# 遍历每个子表
for sheet_name in xls.sheet_names:
    # 读取当前子表
    df = pd.read_excel(xls, sheet_name=sheet_name)

    # 检查是否有"Leng_Geo"列
    if "Leng_Geo" in df.columns:
        # 计算"Leng_Geo"列的总和
        leng_geo_sum = df["Leng_Geo"].sum()

        # 将结果添加到汇总DataFrame中
        new_row = pd.DataFrame({"Sheet Name": [sheet_name], "Leng_Geo Sum": [leng_geo_sum]})
        summary_df = pd.concat([summary_df, new_row], ignore_index=True)
    else:
        print(f"警告：子表 '{sheet_name}' 中没有找到 'Leng_Geo' 列。")

# 将汇总结果保存到新的Excel文件
summary_df.to_excel(output_file, index=False, engine="openpyxl")

print(f"汇总结果已保存到 {output_file}")