import xml.etree.ElementTree as ET

year = 15
sid = 'STP'

# KML 文件路径
# kml_file_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\{sid}\{year}\{sid}_{str(year)[-2:]}.kml'
kml_file_path = fr'E:\_OrderingProject\F_IslandsBoundaryChange\b_ArcData\_AccuracyEvaluation\{sid}\{sid}_{str(year)[-2:]}.kml'

# 解析 KML 文件
tree = ET.parse(kml_file_path)
root = tree.getroot()

# 定义命名空间
namespace = {
    'kml': 'http://www.opengis.net/kml/2.2',
    'gx': 'http://www.google.com/kml/ext/2.2',
    'atom': 'http://www.w3.org/2005/Atom'
}

# 查找所有 <name> 标签
name_tags = root.findall('.//kml:name', namespace)

# 打印所有 <name> 标签的内容
i = -1
for name_tag in name_tags:

    print(f"Found <name>:{i}, {name_tag.text}")
    i += 1