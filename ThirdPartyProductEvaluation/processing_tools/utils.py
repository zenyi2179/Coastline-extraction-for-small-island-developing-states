#!/usr/bin/env python3
"""
通用工具函数模块
提供文件路径处理、目录操作等通用功能
"""

import os
from typing import List, Optional


class FileUtils:
    """文件工具类"""

    @staticmethod
    def get_files_absolute_paths(
        folder_path: str, suffix: Optional[str] = None
    ) -> List[str]:
        """
        获取指定文件夹下所有指定后缀的文件的绝对路径名称

        Args:
            folder_path: 指定文件夹的路径
            suffix: 文件后缀（可选），如 '.shp'。如果不指定，则获取所有文件的路径

        Returns:
            指定后缀的文件的绝对路径名称列表

        Raises:
            FileNotFoundError: 文件夹不存在
        """
        print(f"[INFO]  | 开始获取文件路径，目录: {folder_path}，后缀: {suffix}")

        # 检查文件夹是否存在
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"文件夹不存在: {folder_path}")

        files_paths: List[str] = []

        # 遍历指定文件夹
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                # 如果指定了后缀，则判断文件后缀是否匹配
                if suffix is None or file.endswith(suffix):
                    # 获取文件的绝对路径并添加到列表中
                    absolute_path = os.path.abspath(os.path.join(root, file))
                    files_paths.append(absolute_path)

        print(f"[INFO]  | 找到 {len(files_paths)} 个匹配文件")
        return files_paths

    @staticmethod
    def ensure_directory_exists(directory_path: str) -> None:
        """
        确保目录存在，如果不存在则创建

        Args:
            directory_path: 目录路径

        Raises:
            PermissionError: 目录创建权限不足
        """
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            print(f"[INFO]  | 创建目录: {directory_path}")
        else:
            print(f"[INFO]  | 目录已存在: {directory_path}")

    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """
        获取文件扩展名

        Args:
            file_path: 文件路径

        Returns:
            文件扩展名（小写，包含点号）
        """
        _, extension = os.path.splitext(file_path)
        return extension.lower()


class PathValidator:
    """路径验证类"""

    @staticmethod
    def validate_directory_path(directory_path: str) -> bool:
        """
        验证目录路径是否存在且可访问

        Args:
            directory_path: 目录路径

        Returns:
            路径是否有效
        """
        return os.path.exists(directory_path) and os.path.isdir(directory_path)

    @staticmethod
    def validate_file_path(file_path: str) -> bool:
        """
        验证文件路径是否存在且可访问

        Args:
            file_path: 文件路径

        Returns:
            路径是否有效
        """
        return os.path.exists(file_path) and os.path.isfile(file_path)


def main() -> None:
    """主函数示例"""
    file_utils = FileUtils()
    path_validator = PathValidator()

    # 获取文件路径示例
    try:
        shapefile_paths = file_utils.get_files_absolute_paths(
            folder_path=r"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\e_SIDS_Shp\ATG\2015",
            suffix=".shp",
        )

        for path in shapefile_paths:
            print(f"[INFO]  | 找到 Shapefile: {path}")

    except FileNotFoundError as error:
        print(f"[ERROR] | 目录不存在: {error}")

    # 路径验证示例
    test_path = r"E:\_OrderingProject\F_IslandsBoundaryChange"
    is_valid = path_validator.validate_directory_path(test_path)
    print(f"[INFO]  | 路径验证结果: {test_path} -> {'有效' if is_valid else '无效'}")


if __name__ == "__main__":
    main()