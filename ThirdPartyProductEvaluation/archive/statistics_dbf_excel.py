import pandas as pd

# 读取Excel文件
file_path = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\三方数据统计.xlsx"
df = pd.read_excel(file_path)

# 定义需要处理的列（假设这些是需要比较的列）
# columns_to_compare = ['SIDS_CL_00', 'SIDS_CL_10', 'SIDS_CL_20', 'GSV', 'GMSSD_2015', 'OSM']
columns_to_compare = ['SIDS_CL_10', 'SIDS_CL_15', 'SIDS_CL_20', 'GSV', 'GMSSD_2015']

# 遍历每一行，找到最大值和最小值对应的列名
results = []
for index, row in df.iterrows():
    # 获取当前行的指定列数据
    row_data = row[columns_to_compare]

    # 找到最大值和最小值对应的列名
    max_column = row_data.idxmax()
    min_column = row_data.idxmin()

    # 将结果存储到列表中
    results.append({
        'ID': row['ID'],
        'GID': row['GID'],
        'Max_Value_Column': max_column,
        'Min_Value_Column': min_column
    })

# 将结果转换为DataFrame
result_df = pd.DataFrame(results)

# 输出结果
print(result_df)

# 如果需要，可以将结果保存到新的Excel文件
result_df.to_excel('max_min_columns.xlsx', index=False)