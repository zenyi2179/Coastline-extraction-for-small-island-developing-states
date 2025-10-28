# 海岸线变化分析系统

一个用于处理和分析小岛屿发展中国家海岸线变化的完整系统。

## 文件概览

| 文件名                    | 作用                   | 快速使用                                   | 入口函数/命令行示例                                          |
| ------------------------- | ---------------------- | ------------------------------------------ | ------------------------------------------------------------ |
| `config.py`               | 配置和常量定义         | 定义项目路径、国家列表、处理参数等全局配置 | `from config import ProjectConfig, PathConfig`               |
| `utils.py`                | 通用工具函数           | 提供时间跟踪、坐标转换、文件操作等通用功能 | `from utils import TimeTracker, FileUtils`                   |
| `data_extraction.py`      | 数据提取和筛选功能     | 按位置选择、掩膜裁剪等数据提取功能         | `from data_extraction import DataExtractor`                  |
| `file_operations.py`      | 文件管理和清理操作     | 文件管理、批量处理、数据清理等操作         | `from file_operations import FileManager, BatchProcessor`    |
| `spatial_analysis.py`     | 空间分析和几何计算     | 几何计算、统计分析、数据合并等空间分析     | `from spatial_analysis import SpatialAnalyzer, GeometryProcessor` |
| `coastline_processing.py` | 海岸线处理专用功能     | 海岸线提取、验证、转换等专用处理           | `from coastline_processing import CoastlineProcessor, CoastlineValidator` |
| `data_export.py`          | 数据导出和格式转换     | DBF读取、Excel导出、格式转换等功能         | `from data_export import DataExporter, FormatConverter`      |
| `statistics_analysis.py`  | 统计分析和报告生成     | 数据统计、比较分析、报告生成等功能         | `from statistics_analysis import StatisticsAnalyzer, ReportGenerator` |
| `main.py`                 | 主程序入口和工作流协调 | 完整的工作流协调和命令行接口               | `python main.py --workflow --years 2015,2020 --countries ATG,BHS` |

## 快速开始

### 安装依赖

```bash
pip install geopandas rasterio xarray rioxarray shapely fiona pyproj scipy dbfread pandas openpyxl arcpy dea-tools
```

## 具体使用方法

### 基本使用

1. **运行完整工作流**：

bash

```
python main.py --workflow --years 2015 --countries ATG,BHS,BLZ
```



1. **处理特定年份**：

bash

```
python main.py --year 2015
```



1. **处理特定国家**：

bash

```
python main.py --country ATG
```



1. **自定义年份和国家**：

bash

```
python main.py --workflow --years 2010,2015,2020 --countries ATG,BHS,BLZ,BRB
```



### 模块化使用

python

```
from coastline_analysis_system import CoastlineAnalysisWorkflow

# 创建工作流实例
workflow = CoastlineAnalysisWorkflow()

# 运行完整分析
workflow.run_full_workflow(years=[2015, 2020], countries=["ATG", "BHS"])

# 运行特定年份
workflow.run_specific_year(2015)

# 运行特定国家
workflow.run_specific_country("ATG")
```



## 功能特性

### 数据处理

- 按位置数据提取
- 掩膜裁剪处理
- 多数据源整合
- 批量文件处理

### 海岸线处理

- 海岸线几何提取
- 内陆线识别
- 几何验证检查
- 多年份批量处理

### 空间分析

- 几何属性计算
- 数据合并融合
- 空间统计分析
- 质量检查评估

### 数据导出

- DBF格式读取
- Excel报告生成
- 多格式转换
- 综合数据导出

### 统计分析

- 最大值最小值分析
- 数据质量检查
- 比较分析报告
- 统计摘要生成

## 配置说明

系统支持以下配置：

- **37个小岛屿发展中国家**
- **多个处理年份**（2000、2010、2015、2020）
- **可调的处理参数**（阈值、搜索半径、距离单位等）
- **灵活的路径配置**

## 输出结果

系统生成以下输出：

1. **处理后的海岸线数据**（Shapefile格式）
2. **几何统计信息**（DBF格式）
3. **综合分析报告**（Excel格式）
4. **比较分析结果**（Excel格式）
5. **质量检查报告**（控制台输出）