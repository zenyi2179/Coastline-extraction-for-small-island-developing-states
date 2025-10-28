def read_txt_to_list(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    # 去除每行末尾的换行符
    lines = [line.strip() for line in lines]
    return lines

# 示例用法
file_path = 'example.txt'  # 替换为你的txt文件路径
result = read_txt_to_list(file_path)
print(result)