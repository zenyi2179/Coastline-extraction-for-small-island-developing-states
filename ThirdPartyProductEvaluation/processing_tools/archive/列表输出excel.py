import pandas as pd

def save_to_excel(data, file_name):
    """
    将二维列表保存为Excel文件

    参数:
        data (list of lists): 二维列表，其中每一行是一个列表
        file_name (str): 输出的Excel文件名，应包含扩展名（如.xlsx）
    """
    # 将二维列表转换为DataFrame
    df = pd.DataFrame(data)
    # 保存为Excel文件
    df.to_excel(file_name, index=False, header=False)
    print(f"数据已成功保存到 {file_name}")

# 示例用法
data = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]
save_to_excel(data, "example.xlsx")