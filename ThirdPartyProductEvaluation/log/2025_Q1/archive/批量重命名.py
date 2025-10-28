import os


def rename_matching_files(folder_path: str, old_prefix: str, new_prefix: str, extensions: list = None):
    """
    批量重命名指定文件夹下匹配特定前缀（和可选扩展名）的文件。

    :param folder_path: 要处理的目标文件夹路径
    :param old_prefix: 原文件名前缀，例如 '_ATG_merge'
    :param new_prefix: 新文件名前缀，例如 '_ATG_merge_CL'
    :param extensions: 可选参数：要处理的扩展名列表，例如 ['.cpg', '.shp.xml']；默认为 None，表示处理所有扩展名
    """
    for filename in os.listdir(folder_path):
        # 获取完整路径
        file_path = os.path.join(folder_path, filename)

        # 确保是文件
        if not os.path.isfile(file_path):
            continue

        # 拆分文件名为 name 和 extension
        name, ext = os.path.splitext(filename)

        # 判断是否匹配命名前缀
        if filename.startswith(old_prefix):
            # 如果指定扩展名列表，则判断当前扩展是否在列表中（注意 .shp.xml 特例）
            if extensions is not None:
                # 如果文件是复合扩展名（如 .shp.xml）
                if filename[len(old_prefix):] in extensions:
                    suffix = filename[len(old_prefix):]
                else:
                    continue  # 不处理该文件
            else:
                # 默认保留所有旧前缀之后的内容
                suffix = filename[len(old_prefix):]

            # 构造新文件名
            new_filename = new_prefix + suffix
            new_file_path = os.path.join(folder_path, new_filename)

            try:
                os.rename(file_path, new_file_path)
                print(f"重命名成功: {filename} → {new_filename}")
            except Exception as e:
                print(f"重命名失败: {filename}，错误信息: {e}")


# ========== 主程序入口 ==========
if __name__ == '__main__':
    boun_list = ["BLZ",
                 "DOM",
                 "GNB",
                 "GUY",
                 "HTI",
                 "PNG",
                 "SUR",
                 "TLS",
                 ]
    # Set local variables
    for boun in boun_list:
        for year in [2010, 2020]:
            # 设置路径和前后缀
            folder = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_{str(year)[-2:]}\{boun}"
            old_prefix = fr"{boun}_BV_{str(year)[-2:]}"
            new_prefix = fr"{boun}_BV_{str(year)[-2:]}_"

            # ✅ 选项 1：默认处理所有以 old_prefix 开头的文件
            rename_matching_files(folder, old_prefix, new_prefix)

            # ✅ 选项 2：只处理指定扩展名
            # rename_matching_files(folder, old_prefix, new_prefix, extensions=[".cpg", ".shp.xml"])
