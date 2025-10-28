# -*- coding:utf-8 -*-
"""
作者：23242
日期：2024年11月20日
说明：计算任务运行时间并以格式化的 "HH:MM:SS" 格式输出。
"""

import time  # 导入时间模块，用于记录任务执行的时间点


def consume_time_formatted(start_s, end_s=time.time()):
    """
    计算并输出任务运行时间的格式化结果。

    参数：
        start_s (float): 任务开始时间，时间戳格式。
        end_s (float): 任务结束时间，时间戳格式（默认为当前时间）。

    返回值：
        float: 任务结束时间（时间戳格式）。

    输出：
        以 "HH:MM:SS" 格式打印任务运行的总时间。
    """
    # 计算任务运行的总秒数（取绝对值以避免顺序问题）
    seconds = abs(end_s - start_s)

    # 计算运行时间的小时、分钟和秒数部分
    hours = int(seconds // 3600)  # 小时部分
    minutes = int((seconds % 3600) // 60)  # 分钟部分
    seconds = int(seconds % 60)  # 秒数部分

    # 格式化输出字符串，确保小时、分钟和秒数均为两位数字
    time_print = f"{hours:02}:{minutes:02}:{seconds:02}"
    print(f"Task completed in: {time_print}")  # 打印任务运行时间

    return end_s  # 返回结束时间戳，供进一步分析或记录


if __name__ == '__main__':
    """
    主函数：
    模拟任务运行，并调用 consume_time_formatted() 函数输出运行时间。
    """
    # 记录任务的开始时间
    start_time = time.time()

    # 模拟任务运行的延迟（5秒）
    time.sleep(5)

    # 计算并打印任务的运行时间
    first = consume_time_formatted(start_s=start_time, end_s=time.time())
