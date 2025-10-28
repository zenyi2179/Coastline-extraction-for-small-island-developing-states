def determine_map_position(longitude, latitude, if_print=1):
    """
    根据给定的经度和纬度确定地图上的位置，并返回一个格式化的字符串。

    参数:
    - longitude (float): 经度值
    - latitude (float): 纬度值
    - if_print (int): 是否打印结果，默认为1（打印）

    返回:
    - str: 格式化的地图位置字符串

    示例:
    - determine_map_position(-73.997826, 40.744754)
    coordinate [-73.997826, 40.744754] translate to: 74W40Nr.
    """

    # 初始化经度的整数部分
    abs_var_lon = int(abs(longitude - 1)) if longitude < 0 else int(abs(longitude))
    var_lon = -abs_var_lon if longitude < 0 else abs_var_lon

    # 初始化纬度的整数部分
    abs_var_lat = int(abs(latitude - 1)) if latitude < 0 else int(abs(latitude))
    var_lat = -abs_var_lat if latitude < 0 else abs_var_lat

    # 确定东西方向标识符
    var_WE = 'W' if longitude < 0 else 'E'

    # 确定南北方向标识符
    var_NS = 'N' if latitude > 0 else 'S'

    # 根据输入值和整数部分计算左右方向标识符
    var_lr = 'l' if longitude < var_lon + 0.5 else 'r'

    # 根据输入值和整数部分计算上下方向标识符
    var_ub = 'b' if latitude < var_lat + 0.5 else 'u'

    # 格式化输出为所需的字符串格式
    map_position = fr'{abs_var_lon}{var_WE}{abs_var_lat}{var_NS}{var_lr}{var_ub}'

    # 如果 if_print 为 1，则打印结果
    if if_print:
        print(fr"coordinate [{longitude}, {latitude}] translate to: {map_position}.")

    return map_position


def main():
    pass


if __name__ == '__main__':
    main()
