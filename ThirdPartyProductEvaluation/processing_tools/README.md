# 海岸线变化分析系统

一个用于处理和分析小岛屿发展中国家海岸线变化的完整系统。

## 文件结构

| 文件名                 | 作用                | 快速使用                         | 入口函数/命令行示例                                    |
| ---------------------- | ------------------- | -------------------------------- | ------------------------------------------------------ |
| `file_operations.py`   | 文件操作相关功能    | 文件合并、重命名、移动等操作     | `from file_operations import FileMerger, FileMover`    |
| `arcgis_operations.py` | ArcGIS 空间分析操作 | 裁剪、融合、要素转换等空间分析   | `from arcgis_operations import ArcGISOperations`       |
| `data_export.py`       | 数据导出和格式转换  | Excel 导出、文本读取等数据转换   | `from data_export import DataExporter, TextFileReader` |
| `utils.py`             | 通用工具函数        | 文件路径处理、目录操作等通用功能 | `from utils import FileUtils, PathValidator`           |

## 快速开始

### 安装依赖

```bash
pip install geopandas rasterio xarray rioxarray shapely fiona pyproj scipy dbfread pandas openpyxl arcpy dea-tools
```

## 具体使用方法

### 基本使用

1. **文件合并操作**:

```python
from file_operations import FileMerger

merger = FileMerger()
merger.merge_files_from_folders_with_prefix(
    src_root="E:/_GoogleDrive",
    folder_prefix="SIDs_Grid_Y15",
    dst_folder="E:/output/SIDs_Grid_Y15"
)
```

2. **空间分析操作**:

```python
from arcgis_operations import ArcGISOperations

arc_ops = ArcGISOperations()
arc_ops.clip_features(
    in_features="input.shp",
    clip_features="clip_boundary.shp",
    out_feature_class="output_clipped.shp"
)
```

3. **数据导出操作**:

```python
from data_export import DataExporter

exporter = DataExporter()
data = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
exporter.save_to_excel(data, "output.xlsx")
```

4. **文件工具操作**:

```python
from utils import FileUtils

file_utils = FileUtils()
shapefiles = file_utils.get_files_absolute_paths(
    folder_path="E:/project/data",
    suffix=".shp"
)
```

## 功能特性

### 文件操作

- 批量文件合并和复制
- 文件移动和重命名
- 前缀匹配文件处理
- 多扩展名文件管理

### 空间分析

- 要素裁剪和融合
- 要素格式转换（线转面、面转线）
- 空间数据导出
- 选择集管理

### 数据导出

- Excel 格式数据导出
- 文本文件读取处理
- 二维数据格式转换
- 编码自动处理

### 工具函数

- 文件路径批量获取
- 目录存在性验证
- 文件扩展名提取
- 路径有效性检查

## 配置说明

系统支持以下配置：

- **灵活的文件路径配置**
- **多种文件格式支持**（Shapefile、Excel、文本等）
- **可定制的文件匹配规则**
- **错误处理和日志记录**

## 输出结果

系统生成以下输出：

1. **合并后的文件集合**
2. **处理后的空间数据**（Shapefile 格式）
3. **导出数据文件**（Excel 格式）
4. **处理日志和错误报告**
