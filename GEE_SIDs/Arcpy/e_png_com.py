import os
from PIL import Image

def merge_images(input_dirs, output_dir):
    """
    合并多个文件夹中同名的 PNG 图片，将它们从左到右拼接，并保存到输出目录。

    参数:
    - input_dirs (list): 包含三个输入文件夹路径的列表。
    - output_dir (str): 输出文件夹路径。
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 获取第一个目录的文件名列表（假定所有目录文件名相同）
    file_names = set(os.listdir(input_dirs[0]))
    for folder in input_dirs[1:]:
        file_names &= set(os.listdir(folder))  # 取所有目录中共同存在的文件

    # 过滤出 PNG 文件
    file_names = [f for f in file_names if f.endswith('.png')]

    for file_name in file_names:
        images = []
        for folder in input_dirs:
            img_path = os.path.join(folder, file_name)
            img = Image.open(img_path)
            images.append(img)

        # 计算合并后图片的宽度和高度
        total_width = sum(img.width for img in images)
        max_height = max(img.height for img in images)

        # 创建合并后的图片
        merged_image = Image.new("RGB", (total_width, max_height))

        # 按顺序粘贴图片
        x_offset = 0
        for img in images:
            merged_image.paste(img, (x_offset, 0))
            x_offset += img.width

        # 保存合并后的图片
        output_path = os.path.join(output_dir, file_name)
        merged_image.save(output_path)
        print(f"Saved merged image: {output_path}")

if __name__ == "__main__":
    # 输入文件夹路径
    input_dirs = [
        r"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\Tif_Thumbnail_check\2000_5",
        r"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\Tif_Thumbnail_check\2010_5",
        r"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\Tif_Thumbnail_check\2020_70"
    ]
    # 输出文件夹路径
    output_dir = r"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\Tif_Thumbnail_check\threshold_5_5_70"

    # 合并图片
    merge_images(input_dirs, output_dir)
