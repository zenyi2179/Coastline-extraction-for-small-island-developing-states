# -*- coding:utf-8 -*-
"""
作者：23242
日期：2024年09月10日
"""
import os
import ee
import time

# 构架网络代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:4780'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:4780'
# 设置环境变量以解决 OpenSSL 3.0 的兼容性问题
os.environ['CRYPTOGRAPHY_OPENSSL_NO_LEGACY'] = '1'
# 授权 Earth Engine 账户及Earth Engine API
ee.Authenticate()
ee.Initialize(project='ee-nicexian0011')

def cancel_active_tasks():
    """
    取消所有正在运行的任务。
    """
    tasks = ee.batch.Task.list()
    for task in tasks:
        status = task.status()
        if status['state'] in ['READY', 'RUNNING']:
            task.cancel()
            print(f"Cancelled task {status['description']} with state {status['state']}.")

def delete_completed_tasks():
    """
    删除所有已完成的任务。
    """
    tasks = ee.batch.Task.list()
    for task in tasks:
        status = task.status()
        if status['state'] in ['COMPLETED', 'FAILED', 'CANCELLED']:
            task_id = status['id']
            ee.data.deleteTask(task_id)
            print(f"Deleted task {status['description']} with state {status['state']}.")

def clear_tasks():
    """
    清除所有任务，包括取消正在运行的任务和删除已完成的任务。
    """
    cancel_active_tasks()
    delete_completed_tasks()

def main():
    # 清除任务列表
    clear_tasks()

if __name__ == '__main__':
    main()