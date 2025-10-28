# -*- coding:utf-8 -*-
"""
作者：23242
日期：2024年11月27日
"""
import sys

sys.path.append(r"E:\_OrderingProject\F_IslandsBoundaryChange\f_Python")
from GEE_SIDs import _tools


def main():
    # 参数if_print设置为0表示不打印记录列表  [[140268, 'UID_140268', 113.75, 7.25], [140986, 'UID_140986', 112.75, 7.75],
    records_list = _tools.read_dbf_to_list(
        dbf_path=fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\d_SIDS_Boundary\SIDS_Grids\_glo_sids_grids.dbf',
        if_print=0)
    # 逐一运行
    # for i in records_list:
    #     print(i[0])
    for record in records_list:
        # 初始化地理要素
        longitude = record[1]  # 记录中的经度值
        latitude = record[2]  # 记录中的纬度值

        # 确定格网范围
        lb_lon, lb_lat = _tools.get_grid_coordinates(longitude, latitude)  # 获取网格的左下角坐标
        rt_lon = lb_lon + 0.5
        rt_lat = lb_lat + 0.5
        # 构建表示网格边界的列表
        boundary_grid = [lb_lon, lb_lat, rt_lon, rt_lat]

        # 确定格网名称
        position = _tools.determine_map_position(longitude=longitude, latitude=latitude, if_print=0)  # 84W17Nlb
        print(position)


if __name__ == '__main__':
    main()
