import arcpy
import os


def main(eez_v12_shp, output_path):
    # Process: 合并 (合并) (management)
    output = output_path
    arcpy.management.Merge(inputs=eez_v12_shp, output=output, add_source="NO_SOURCE_INFO")


if __name__ == '__main__':
    list_eez = []
    path_eez = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\World_EEZ_v12_20231025\eez_v12_dissolve.gdb'
    for i in range(1, 286):
        path_eez_temp = os.path.join(path_eez, fr'eez_{i}')
        list_eez.append(path_eez_temp)

    output_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\World_EEZ_v12_20231025\eez_v12_dissolve.shp'

    # print(list_eez)

    main(eez_v12_shp=list_eez, output_path=output_path)
