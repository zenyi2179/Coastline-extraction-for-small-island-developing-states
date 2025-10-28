# -*- coding:utf-8 -*-
"""
作者：23242
日期：2024年11月02日
"""
import math


def get_grid_coordinates(longitude, latitude):
    # 计算经度的网格左下角坐标
    grid_longitude = math.floor(longitude * 2) / 2
    # 计算纬度的网格左下角坐标
    grid_latitude = math.floor(latitude * 2) / 2

    return grid_longitude, grid_latitude



if __name__ == '__main__':
    # 给定的经纬度
    longitude = 110.25
    latitude = 18.25

    # 获取网格的左下角坐标
    lb_lon, lb_lat = get_grid_coordinates(longitude, latitude)
    print(fr"The coordinate of the start corner of the 0.5° grid: {lb_lon}, {lb_lat}")

    rt_lon = lb_lon + 0.5
    rt_lat = lb_lat + 0.5
    boundary_grid = [lb_lon, lb_lat, rt_lon, rt_lat]
    print(boundary_grid)  # [113.5, 7.0, 114.0, 7.5]