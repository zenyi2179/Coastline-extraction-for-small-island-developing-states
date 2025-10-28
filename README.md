# SIDS Shoreline Variability (SIDS_SV) v1.0  
## Long-term coastline change analysis for 37 Small Island Developing States (SIDS)  
**2010 – 2015 – 2020 | 30 m | 3 epochs | Open-source | One-click workflow**

---

## 0 Quick Facts

| Dimension        | Details                                                                 |
|------------------|-------------------------------------------------------------------------|
| **Coverage**     | All 37 UN-OHRLLS SIDS (Caribbean, Pacific, AIMS).                       |
| **Temporal span**| 2010 → 2015 → 2020 (Landsat-5/7/8, 4–10 month tide-free window).        |
| **Resolution**   | 30 m; sub-pixel water-line extraction + 60 m PAEK smoothing.            |
| **Accuracy**     | Mean RMSE ≤ 17.4 m; completeness ≥ 99 %; ≥ 99 % within 2 pixels.       |
| **Code**         | Pure Python, modular, ≥ 90 % type hints, ≥ 80 % unit-test coverage.     |
| **Outputs**      | Shapefile / Excel / DBF / change-rate maps / QA reports.                |

---

## 1 Motivation

> “SIDS account for <1 % of global land area but >70 % of coastal-disaster losses.” — UN-OHRLLS 2023

| Pain-point        | How global products fail SIDS                                           |
|-------------------|-------------------------------------------------------------------------|
| **Temporal gaps** | GSV, GMSSD, OSM are single-year snapshots – no change metrics.          |
| **Spatial gaps**  | GCL_FCS30 skips hundreds of remote atolls.                              |
| **Accuracy**      | 30 m products ignore sub-pixel positioning; sub-meter sets lack time-series. |
| **Local errors**  | Mixed-port, reef, mangrove scenes: commission error > 20 %.             |

**Our answer – SIDS_SV v1.0**  
- 3 epochs (2010, 2015, 2020)  
- 1 281 Landsat 0.5°×0.5° tiles covering 37 countries  
- MNDWI + morphological filter + sub-pixel contour + PAEK  
- 11 100 Google-Earth reference points  
- Fully open: code, samples, results

---

## 2 Workflow

```mermaid
flowchart TD
    A[Landsat L2 C2] --> B[Cloud-free median composite<br>Apr–Oct low-tide window]
    B --> C[MNDWI = (Green – SWIR1)/(Green + SWIR1)]
    C --> D[Morphological sieve<br>connected pixels ≥ 4]
    D --> E[Sub-pixel shoreline<br>linear interpolation to MNDWI = 0]
    E --> F[PAEK smoothing<br>60 m tolerance]
    F --> G[DSAS transects<br>500 m spacing]
    G --> H[Change rates<br>EPR / LRR]
    H --> I[Accuracy assessment<br>11 100 GE points]
```

---

## 3 Repository Structure

| File                     | Responsibility                              | Key class / function                          | Example call |
|--------------------------|---------------------------------------------|-----------------------------------------------|--------------|
| `config.py`              | Paths, country list, band indices, thresholds | `PathConfig`, `ProcessingConfig`             | `from config import PathConfig as PC` |
| `auth.py`                | GEE login & proxy                           | `initialize_earth_engine()`                   | `initialize_earth_engine(key_file='.ee.json')` |
| `data_extraction.py`     | Tile-based image clipping                   | `DataExtractor.clip_by_grid()`                | `extractor.batch_clip(iso_list)` |
| `raster_processing.py`   | MNDWI, cloud mask, sieve                    | `IndexCalculator.calc_mndwi()`                | `idx.calc_mndwi()` |
| `coastline_processing.py`| Vectorize, smooth, topology check           | `CoastlineExtractor.smooth_pae()`             | `ext.extract_single_tile()` |
| `spatial_analysis.py`    | Geometry metrics & QA                       | `SpatialAnalyzer.calc_length_area()`          | `analyzer.run()` |
| `accuracy_evaluation.py` | Reference-point generator & RMSE            | `BatchAccuracyEvaluator.run_rmse()`           | `eval.run()` |
| `statistics_analysis.py` | EPR / LRR / area change                     | `StatisticsAnalyzer.calc_epr_lrr()`           | `stat.calc_epr()` |
| `data_export.py`         | Multi-format export                         | `DataExporter.to_excel()`                     | `exp.to_excel()` |
| `file_operations.py`     | Batch rename / merge                        | `FileManager.merge_shapefiles()`              | `fm.merge()` |
| `main.py`                | CLI & workflow orchestrator                 | `CoastlineAnalysisWorkflow`                   | `python main.py --workflow --years 2010,2015,2020 --countries ATG,BHS` |

---

## 4 Validation

| Product     | Epoch | Resolution | Mean bias | ≤ 1 pix (30 m) | ≤ 2 pix (60 m) | Completeness |
|-------------|-------|------------|-----------|----------------|----------------|--------------|
| **SIDS_SV** | 2010  | 30 m       | 16.54 m   | 86.78 %        | 99.03 %        | 99.2 %       |
| GCL_FCS30   | 2010  | 30 m       | 23.94 m   | 70.31 %        | 93.94 %        | 27.8 %       |
| **SIDS_SV** | 2015  | 30 m       | 15.68 m   | 88.46 %        | 99.27 %        | 99.2 %       |
| GMSSD       | 2015  | < 1 m      | 10.90 m   | 92.75 %        | 98.40 %        | 96.5 %       |
| **SIDS_SV** | 2020  | 30 m       | 13.60 m   | 92.92 %        | 99.54 %        | 99.2 %       |
| OSM         | 2020  | < 1 m      | 10.25 m   | 93.69 %        | 98.73 %        | 70.3 %       |

> In the 30 m long-term niche, SIDS_SV shows the lowest error and highest coverage; gap to sub-meter sets is < 5 m while providing full temporal continuity for every islet.

---

## 5 Change Signals 2010–2020

- **Whole SIDS**: net land loss 0.37 %; mean shoreline progradation **+0.89 m/yr** (EPR).  
- **Hot-spot erosion**: Bahamas **‑8.46 %** (‑947 km²).  
- **Hot-spot accretion**: Maldives **+9.51 %** (+20.8 km²) from reclamation.  
- **Regional ranking**: Caribbean > Pacific > AIMS (Atlantic-Indian-Med).

---

## 6 One-line Reproducibility

```bash
# ① Clone (repo goes public upon paper acceptance)
git clone https://github.com/YourOrg/SIDS-Coastline.git
cd SIDS-Coastline

# ② Install (conda or venv)
pip install -r requirements.txt
# OR  conda env create -f environment.yml && conda activate sids

# ③ Run
python main.py \
       --workflow \
       --years 2010,2015,2020 \
       --countries ATG,BHS,BLZ,BRB,CUB \
       --output ./results
```

Output tree (auto-generated)

```
results/
├── ATG_2010_coastline.shp
├── ATG_2015_coastline.shp
├── ATG_2020_coastline.shp
├── ATG_change_stats.dbf
├── ATG_epr_lrr.xlsx
├── QA_report_ATG.pdf
└── …
```

---

## 7 Programmatic API

```python
from main import CoastlineAnalysisWorkflow
w = CoastlineAnalysisWorkflow(config='my_config.yaml')
w.run_full_workflow(years=[2015, 2020], countries=['ATG', 'BHS'])
df = w.get_change_stats()      # pandas.DataFrame
w.to_excel('summary.xlsx')
```

---

## 8 Configuration Snippet

```yaml
# config/user.yaml
years: [2010, 2015, 2020]
countries: *all_37          # or ['ATG', 'BHS']
mndwi_threshold: 0.0
paek_tolerance: 60          # metres
dsas_spacing: 500           # metres
gee_project: 'your-project'
output_crs: 'EPSG:4326'
```

---

## 9 Paper-to-Code Map

| Paper section | Code location |
|---------------|---------------|
| §3.1 Pre-processing | `raster_processing.py::cloud_mask`, `temporal_median()` |
| §3.2 MNDWI | `IndexCalculator::calc_mndwi()` |
| §3.3 Sub-pixel extraction | `BandInterpolator::find_contours_subpixel()` |
| §3.4 PAEK smoothing | `CoastlineExtractor::smooth_pae()` |
| §4.2 Accuracy | `accuracy_evaluation.py::BatchAccuracyEvaluator` |
| §4.3 DSAS rates | `statistics_analysis.py::calc_epr_lrr()` |

> All figures/tables in the manuscript can be regenerated with  
> `python main.py --reproduce-paper` (script released together with repo).

---

## 10 Limitations & Outlook

| Current gap | Next step |
|-------------|-----------|
| 30 m only | Fuse Sentinel-2 10 m + Sentinel-1 SAR |
| No tide correction | Assimilate tide gauges & FES2014 model |
| Weak on artificial shores | CNN with edge-aware loss |
| Sparse GPS validation | 2025 field campaign with Pacific Community (SPC) |

---

**Citation (pre-print)**  
> Your Name et al., 2024. "Three-decadal shoreline variability for 37 Small Island Developing States at 30 m resolution." *Earth System Science Data Discussions*. [doi:10.5194/essd-2024-xxx]
