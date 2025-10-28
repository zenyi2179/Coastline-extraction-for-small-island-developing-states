import arcpy
from sys import argv


def create_random_points(
        work_folder: str = "E:\\_OrderingProject\\F_IslandsBoundaryChange\\b_ArcData\\_AccuracyEvaluation\\2000\\NRU",
        sample_lines: str = "E:\\_OrderingProject\\F_IslandsBoundaryChange\\b_ArcData\\_AccuracyEvaluation\\2000\\NRU\\sample_lines.shp",
        out_name: str = "sample_points.shp",
        num_points: int = 150) -> str:
    """
    创建随机点

    :param out_name: 样本点名称
    :param work_folder: 工作文件夹路径
    :param sample_lines: 样本线要素类路径
    :param num_points: 随机点数量
    :return: 创建的随机点要素类路径
    """
    # 允许覆盖输出
    arcpy.env.overwriteOutput = True

    # 创建随机点
    sample_points_shp = arcpy.management.CreateRandomPoints(
        out_path=work_folder,
        out_name=out_name,
        constraining_feature_class=sample_lines,
        number_of_points_or_field=str(num_points),
        minimum_allowed_distance="150 Meters",
        create_multipoint_output="POINT")[0]

    print(fr"{work_folder} successful.")

    return sample_points_shp


if __name__ == '__main__':
    # 全局环境设置
    year_list = [2000, 2010, 2020]
    sids_cou_list = ['DMA',
                     'GUM',
                     'NIU',
                     'SGP',
                     'VCT',
                     ]
    # year_list = [2020]
    # sids_list = ['BRB',]
    for sid in sids_cou_list:
        for year in year_list:
            work_folder = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\{sid}\{year}"
            sample_lines = fr"E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\{sid}\{year}\SL_{sid}_{str(year)[-2:]}.shp"
            out_name = fr"SP_{sid}_{str(year)[-2:]}.shp"
            num_points = 300
            create_random_points(work_folder, sample_lines, out_name, num_points)
