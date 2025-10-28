import os
import shutil

# 源目录路径
src_folder = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\k_SIDS_Smooth\ABW"
# 目标目录路径
dst_folder = r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_00\ABW"

# 原始文件名前缀
original_prefix = "ABW_00"
# 重命名的新前缀
new_prefix = "ABW_BV_00"

def move_and_rename_files(src_dir: str, dst_dir: str, old_prefix: str, new_prefix: str) -> None:
    """
    查找源目录中以 old_prefix 开头的文件，将其重命名为 new_prefix 并移动到目标目录。
    """
    # 如果目标目录不存在，创建之
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
        print(f"创建目标文件夹: {dst_dir}")

    # 遍历源目录的所有文件
    for filename in os.listdir(src_dir):
        if filename.startswith(old_prefix):
            # 获取文件扩展名
            file_ext = os.path.splitext(filename)[1]
            # 构建新的文件名
            new_filename = f"{new_prefix}{file_ext}"
            # 构建源文件路径和目标文件路径
            src_path = os.path.join(src_dir, filename)
            dst_path = os.path.join(dst_dir, new_filename)

            # 移动并重命名文件
            shutil.move(src_path, dst_path)
            print(f"移动并重命名文件: {filename} -> {new_filename}")

if __name__ == "__main__":
    move_and_rename_files(src_folder, dst_folder, original_prefix, new_prefix)
