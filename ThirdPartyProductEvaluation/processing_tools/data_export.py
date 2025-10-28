#!/usr/bin/env python3
"""
数据导出和格式转换模块
提供 Excel 导出、文本读取等数据格式转换功能
"""

import pandas as pd
from typing import List, Any


class DataExporter:
    """数据导出类"""

    @staticmethod
    def save_to_excel(data: List[List[Any]], file_name: str) -> None:
        """
        将二维列表保存为 Excel 文件

        Args:
            data: 二维列表，其中每一行是一个列表
            file_name: 输出的 Excel 文件名，应包含扩展名（如 .xlsx）

        Raises:
            ValueError: 数据格式不正确
            PermissionError: 文件写入权限不足
        """
        print(f"[INFO]  | 开始导出数据到 Excel: {file_name}")

        # 验证数据格式
        if not data or not isinstance(data, list):
            raise ValueError("数据必须是非空的二维列表")

        if not all(isinstance(row, list) for row in data):
            raise ValueError("数据中的每一行必须是列表")

        try:
            # 将二维列表转换为 DataFrame
            data_frame = pd.DataFrame(data)
            # 保存为 Excel 文件
            data_frame.to_excel(file_name, index=False, header=False)
            print(f"[INFO]  | 数据已成功保存到 {file_name}")
        except Exception as error:
            print(f"[ERROR] | 导出 Excel 失败: {error}")
            raise


class TextFileReader:
    """文本文件读取类"""

    @staticmethod
    def read_txt_to_list(file_path: str, encoding: str = "utf-8") -> List[str]:
        """
        按行读取 txt 文件返回字符串列表

        Args:
            file_path: txt 文件路径
            encoding: 文件编码，默认为 'utf-8'

        Returns:
            包含每行内容的字符串列表（已去除换行符）

        Raises:
            FileNotFoundError: 文件不存在
            UnicodeDecodeError: 编码错误
        """
        print(f"[INFO]  | 开始读取文本文件: {file_path}")

        try:
            with open(file_path, "r", encoding=encoding) as file:
                lines = file.readlines()

            # 去除每行末尾的换行符
            cleaned_lines = [line.strip() for line in lines]
            print(f"[INFO]  | 成功读取 {len(cleaned_lines)} 行数据")
            return cleaned_lines

        except FileNotFoundError:
            print(f"[ERROR] | 文件不存在: {file_path}")
            raise
        except UnicodeDecodeError as decode_error:
            print(f"[ERROR] | 文件编码错误 {file_path}: {decode_error}")
            raise


def main() -> None:
    """主函数示例"""
    exporter = DataExporter()
    reader = TextFileReader()

    # Excel 导出示例
    sample_data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    exporter.save_to_excel(sample_data, "example.xlsx")

    # 文本文件读取示例
    try:
        lines = reader.read_txt_to_list("example.txt")
        print(f"[INFO]  | 读取到的内容: {lines}")
    except FileNotFoundError:
        print(f"[WARN]  | 示例文件不存在，跳过读取测试")


if __name__ == "__main__":
    main()