# 海岸线变化分析系统

一个用于处理和分析小岛屿发展中国家海岸线变化的完整系统。

## 文件结构

| 文件名                    | 作用             | 快速使用                                     | 入口函数/命令行示例                                          |
| ------------------------- | ---------------- | -------------------------------------------- | ------------------------------------------------------------ |
| `config.py`               | 配置和常量定义   | 定义项目路径、国家列表、处理参数等全局配置   | `from config import ProjectConfig, PathConfig`               |
| `utils.py`                | 通用工具函数     | 提供时间跟踪、坐标转换、文件操作等通用功能   | `from utils import TimeTracker, FileUtils`                   |
| `data_processing.py`      | 数据处理核心功能 | 数据格式转换、子像素提取、平滑处理、栅格化等 | `from data_processing import DataFormatConverter, SubpixelExtractor` |
| `file_operations.py`      | 文件操作相关     | 文件管理、批量处理、数据迁移、空间文件操作   | `from file_operations import FileManager, BatchProcessor`    |
| `spatial_analysis.py`     | 空间分析功能     | 几何计算、统计分析、合并计算等空间分析功能   | `from spatial_analysis import SpatialAnalyzer, StatisticsCalculator` |
| `coastline_extraction.py` | 海岸线提取       | 海岸线提取、图幅处理、阈值提取等功能         | `from coastline_extraction import CoastlineExtractor, ThresholdExtractor` |
| `accuracy_evaluation.py`  | 精度评估         | 精度统计、误差计算、样本点生成等评估功能     | `from accuracy_evaluation import AccuracyEvaluator, BatchAccuracyEvaluator` |
| `main.py`                 | 主程序入口       | 完整的海岸线变化分析工作流和命令行接口       | `python main.py --workflow --years 2015,2020 --countries ATG,BHS` |

## 快速开始

### 安装依赖

```bash
pip install geopandas rasterio xarray rioxarray shapely fiona pyproj scipy dbfread pandas openpyxl arcpy dea-tools
```

## 具体使用方法

### 基本使用

1. **运行完整工作流**：

```bash
python main.py --workflow --years 2015 --countries ATG,BHS,BLZ
```

2. **处理特定年份**：

```bash
python main.py --year 2015
```

3. **处理特定国家**：

```bash
python main.py --country ATG
```

4. **自定义年份和国家**：

```bash
python main.py --workflow --years 2010,2015,2020 --countries ATG,BHS,BLZ,BRB
```

### 模块化使用

```python
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

- GeoJSON 到 Shapefile 转换
- 线要素到面要素转换
- 面要素平滑处理
- 矢量到栅格转换

### 海岸线提取

- 子像素等高线提取
- 零值边界处理
- 多线串几何修复
- 图幅批量处理

### 空间分析

- 几何属性计算
- 空间查询和选择
- 样本点生成
- 距离统计分析

### 精度评估

- 多数据集精度比较
- 误差统计计算
- 批量评估导出
- 可视化报告生成

## 配置说明

系统支持以下配置：

- **37个小岛屿发展中国家**
- **多个处理年份**（2000、2010、2015、2020）
- **可调的处理参数**（阈值、平滑度、搜索半径等）
- **灵活的路径配置**

## 输出结果

系统生成以下输出：

1. **处理后的海岸线数据**（Shapefile 格式）
2. **精度评估报告**（Excel 格式）
3. **统计信息文件**（DBF 格式）
4. **可视化图表**（可选）

## 技术总结

这个重构后的系统具有以下特点：

1. **模块化设计** - 每个功能模块独立，便于维护和扩展
2. **类型注解** - 完整的类型提示，提高代码可读性
3. **错误处理** - 完善的异常处理和日志记录
4. **配置驱动** - 所有参数通过配置文件管理
5. **批量处理** - 支持多国家多年份的批量处理
6. **命令行接口** - 提供灵活的命令行参数
7. **代码规范** - 完全符合 PEP 8 和其他代码规范要求

系统可以处理 37 个小岛屿发展中国家的海岸线变化分析，支持多个年份的数据处理和质量评估。

---
**注意**：以上内容为系统说明文档，实际使用时请根据具体环境和需求调整配置参数。