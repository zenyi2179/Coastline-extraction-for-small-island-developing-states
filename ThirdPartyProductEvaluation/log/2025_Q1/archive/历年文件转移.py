import os
import shutil

import os
import shutil

def copy_and_rename_files(src_dir: str, dst_dir: str, old_prefix: str, new_prefix: str) -> None:
    """
    查找源目录中以 old_prefix 开头的文件，复制并重命名为 new_prefix+原文件后缀，复制到目标目录。
    """
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
        print(f"创建目标文件夹: {dst_dir}")

    for filename in os.listdir(src_dir):
        if filename.startswith(old_prefix):
            # 构建新的文件名：仅替换前缀，不修改后缀结构
            new_filename = filename.replace(old_prefix, new_prefix, 1)

            src_path = os.path.join(src_dir, filename)
            dst_path = os.path.join(dst_dir, new_filename)

            shutil.copy2(src_path, dst_path)
            print(f"复制并重命名文件: {filename} -> {new_filename}")

if __name__ == "__main__":
    # boundary_origin_list = [
    #     "ABW",
    #     "AIA",
    #     "ASM",
    #     "ATG",
    #     "BHS",
    #     "BMU",
    #     "BRB",
    #     "COK",
    #     "COM",
    #     "CPV",
    #     "CUB",
    #     "CUW",
    #     "CYM",
    #     "DMA",
    #     "FJI",
    #     "FSM",
    #     "GLP",
    #     "GRD",
    #     "GUM",
    #     "JAM",
    #     "KIR",
    #     "KNA",
    #     "LCA",
    #     "MDV",
    #     "MHL",
    #     "MNP",
    #     "MSR",
    #     "MTQ",
    #     "MUS",
    #     "NCL",
    #     "NIU",
    #     "NRU",
    #     "PLW",
    #     "PRI",
    #     "PYF",
    #     "SGP",
    #     "SLB",
    #     "STP",
    #     "SYC",
    #     "TCA",
    #     "TON",
    #     "TTO",
    #     "TUV",
    #     "VCT",
    #     "VGB",
    #     "VIR",
    #     "VUT",
    #     "WSM",
    # ]
    # year_list = [2000, 2010, 2020]

    # 37国家中 29 个可以直接转移的国家
    boundary_origin_list = [
        "ATG",
        "BHS",
        "BRB",
        "COM",
        "CPV",
        "CUB",
        "DMA",
        "FJI",
        "FSM",
        "GRD",
        "JAM",
        "KIR",
        "KNA",
        "LCA",
        "MDV",
        "MHL",
        "MUS",
        "NRU",
        "PLW",
        "SGP",
        "SLB",
        "STP",
        "SYC",
        "TON",
        "TTO",
        "TUV",
        "VCT",
        "VUT",
        "WSM",
    ]
    year_list = [2015]
    for sids in boundary_origin_list:
        for year in year_list:
            # 源目录路径
            src_folder = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\f_SIDS_Optimize\{sids}"
            # 目标目录路径
            dst_folder = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_{str(year)[-2:]}\{sids}"

            # 原始文件名前缀
            original_prefix = fr"{sids}_{str(year)[-2:]}"
            # 重命名的新前缀
            new_prefix = fr"{sids}_BV_{str(year)[-2:]}"

            copy_and_rename_files(src_folder, dst_folder, original_prefix, new_prefix)
