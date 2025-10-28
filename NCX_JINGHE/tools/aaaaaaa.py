import os
import time

def rename_files(directory):
    """
    遍历指定目录及其子目录中的文件，将文件名中的 "_fixed_" 替换为 "_polygon_"。

    :param directory: 要遍历的目录路径
    """
    start_time = time.time()  # 开始时间
    print(f"[INFO]  | 任务启动，开始遍历目录：{directory}")

    # 遍历目录及其子目录
    for root, dirs, files in os.walk(directory):
        for file in files:
            # 检查文件名中是否包含 "_fixed_"
            if "_fixed_" in file:
                old_file_path = os.path.join(root, file)  # 原文件路径
                new_file_name = file.replace("_fixed_", "_polygon_")  # 新文件名
                new_file_path = os.path.join(root, new_file_name)  # 新文件路径

                # 重命名文件
                os.rename(old_file_path, new_file_path)
                print(f"[INFO]  | 文件重命名成功：{old_file_path} -> {new_file_path}")

    end_time = time.time()  # 结束时间
    elapsed_time = end_time - start_time  # 计算耗时
    hours, remainder = divmod(elapsed_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"[TIME]  | 总耗时: {int(hours):02d}h{int(minutes):02d}m{int(seconds):02d}s")


if __name__ == '__main__':
    # 指定目录路径
    target_directory = r"E:\_OrderingProject\F_IslandsBoundaryChange\SIDS_SV\SIDS_SV_v1"
    rename_files(target_directory)