# 海岸线变化分析系统

一个用于处理和分析小岛屿发展中国家海岸线变化的完整系统。

## 文件概览

| 文件名 | 作用 | 快速使用 | 入口函数/命令行示例 |
|--------|------|----------|-------------------|
| `config.py` | 配置和常量定义 | 定义项目路径、国家列表、处理参数等全局配置 | `from config import ProjectConfig, ProcessingConfig` |
| `auth.py` | Earth Engine 认证和初始化 | 处理 GEE 认证和会话管理 | `from auth import initialize_earth_engine` |
| `file_utils.py` | 文件操作和路径处理 | 提供文件转换、批量操作等功能 | `from file_utils import FileOperations, ShapefileToGeoJSONConverter` |
| `gee_operations.py` | Google Earth Engine 数据操作 | 处理数据上传、下载、资产管理 | `from gee_operations import GEEAssetManager, GEEImageProcessor` |
| `raster_processing.py` | 栅格数据处理和分析 | 提供插值、指数计算、PCA 等功能 | `from raster_processing import BandInterpolator, IndexCalculator` |
| `coastline_processing.py` | 海岸线提取和处理 | 海岸线提取、验证、转换等专用处理 | `from coastline_processing import CoastlineExtractor, CoastlineValidator` |
| `spatial_analysis.py` | 空间分析和几何计算 | 几何属性计算、质量检查、数据导出 | `from spatial_analysis import SpatialAnalyzer, QualityChecker` |
| `main.py` | 主程序入口和工作流协调 | 完整工作流协调和命令行接口 | `python main.py --workflow --years 2015,2020 --countries ATG,BHS` |

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
from main import CoastlineAnalysisWorkflow

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

- Shapefile格式导出
- GeoJSON格式转换
- 统计报告生成
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
2. **几何统计信息**（CSV格式）
3. **综合分析报告**（文本格式）
4. **比较分析结果**（控制台输出）
5. **质量检查报告**（控制台输出）