#!/usr/bin/env python3
"""
文件操作相关功能模块
提供文件合并、重命名、移动等操作功能
"""

import os
import shutil
from typing import List, Optional


class FileMerger:
    """文件合并操作类"""

    @staticmethod
    def merge_files_from_folders_with_prefix(
        src_root: str, folder_prefix: str, dst_folder: str
    ) -> None:
        """
        将所有以指定前缀开头的文件夹中的文件合并复制到目标文件夹

        Args:
            src_root: 源文件夹的根目录，例如 'E:/_GoogleDrive'
            folder_prefix: 文件夹的公共前缀，例如 'SIDs_Grid_Y15'
            dst_folder: 目标文件夹路径

        Raises:
            FileNotFoundError: 源文件夹不存在
            PermissionError: 文件操作权限不足
        """
        print(f"[INFO]  | 开始合并文件，源目录: {src_root}，目标目录: {dst_folder}")

        # 确保目标文件夹存在
        os.makedirs(dst_folder, exist_ok=True)

        # 检查源目录是否存在
        if not os.path.exists(src_root):
            raise FileNotFoundError(f"源目录不存在: {src_root}")

        # 遍历根目录下的所有文件夹
        for folder_name in os.listdir(src_root):
            folder_path = os.path.join(src_root, folder_name)

            # 判断是否是目录且名称以指定前缀开头
            if os.path.isdir(folder_path) and folder_name.startswith(folder_prefix):
                print(f"[INFO]  | 处理文件夹: {folder_path}")

                # 遍历文件夹中的文件
                for file_name in os.listdir(folder_path):
                    src_file = os.path.join(folder_path, file_name)
                    dst_file = os.path.join(dst_folder, file_name)

                    try:
                        shutil.copy2(src_file, dst_file)
                        print(f"[INFO]  | 已复制文件: {src_file} → {dst_file}")
                    except Exception as error:
                        print(f"[ERROR] | 复制文件失败 {src_file}: {error}")


class FileMover:
    """文件移动和重命名操作类"""

    @staticmethod
    def move_and_rename_files(
        src_dir: str,
        dst_dir: str,
        old_prefix: str,
        new_prefix: str,
    ) -> None:
        """
        查找源目录中以 old_prefix 开头的文件，将其重命名为 new_prefix 并移动到目标目录

        Args:
            src_dir: 源目录路径
            dst_dir: 目标目录路径
            old_prefix: 原始文件名前缀
            new_prefix: 新文件名前缀

        Raises:
            FileNotFoundError: 源目录不存在
            PermissionError: 文件操作权限不足
        """
        print(f"[INFO]  | 开始移动和重命名文件，源目录: {src_dir}")

        # 检查源目录是否存在
        if not os.path.exists(src_dir):
            raise FileNotFoundError(f"源目录不存在: {src_dir}")

        # 如果目标目录不存在，创建之
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
            print(f"[INFO]  | 创建目标文件夹: {dst_dir}")

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

                try:
                    shutil.move(src_path, dst_path)
                    print(f"[INFO]  | 移动并重命名文件: {filename} -> {new_filename}")
                except Exception as error:
                    print(f"[ERROR] | 移动文件失败 {filename}: {error}")

    @staticmethod
    def rename_matching_files(
        folder_path: str,
        old_prefix: str,
        new_prefix: str,
        extensions: Optional[List[str]] = None,
    ) -> None:
        """
        批量重命名指定文件夹下匹配特定前缀（和可选扩展名）的文件

        Args:
            folder_path: 要处理的目标文件夹路径
            old_prefix: 原文件名前缀，例如 '_ATG_merge'
            new_prefix: 新文件名前缀，例如 '_ATG_merge_CL'
            extensions: 可选参数：要处理的扩展名列表，例如 ['.cpg', '.shp.xml']；
                        默认为 None，表示处理所有扩展名

        Raises:
            FileNotFoundError: 目标文件夹不存在
            PermissionError: 文件重命名权限不足
        """
        print(f"[INFO]  | 开始重命名文件，目录: {folder_path}")

        # 检查目录是否存在
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"目标文件夹不存在: {folder_path}")

        for filename in os.listdir(folder_path):
            # 获取完整路径
            file_path = os.path.join(folder_path, filename)

            # 确保是文件
            if not os.path.isfile(file_path):
                continue

            # 判断是否匹配命名前缀
            if filename.startswith(old_prefix):
                # 如果指定扩展名列表，则判断当前扩展是否在列表中
                if extensions is not None:
                    # 检查文件后缀是否在指定列表中
                    if not any(filename.endswith(ext) for ext in extensions):
                        continue

                # 构造新文件名：保留旧前缀之后的内容
                suffix = filename[len(old_prefix) :]
                new_filename = new_prefix + suffix
                new_file_path = os.path.join(folder_path, new_filename)

                try:
                    os.rename(file_path, new_file_path)
                    print(f"[INFO]  | 重命名成功: {filename} → {new_filename}")
                except Exception as error:
                    print(f"[ERROR] | 重命名失败 {filename}: {error}")


def main() -> None:
    """主函数示例"""
    # 示例用法
    merger = FileMerger()
    mover = FileMover()

    # 文件合并示例
    merger.merge_files_from_folders_with_prefix(
        src_root="E:/_GoogleDrive",
        folder_prefix="SIDs_Grid_Y15",
        dst_folder="E:/_OrderingProject/F_IslandsBoundaryChange/c_GeeData/SIDs_Grid_Y15",
    )

    # 文件移动和重命名示例
    mover.move_and_rename_files(
        src_dir=r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\k_SIDS_Smooth\ABW",
        dst_dir=r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_ThirdProductEvaluation\SIDS_CL_00\ABW",
        old_prefix="ABW_00",
        new_prefix="ABW_BV_00",
    )

    # 文件重命名示例
    mover.rename_matching_files(
        folder_path=r"C:\Users\23242\Desktop\ATG",
        old_prefix="_ATG_merge",
        new_prefix="_ATG_merge_CL",
    )


if __name__ == "__main__":
    main()