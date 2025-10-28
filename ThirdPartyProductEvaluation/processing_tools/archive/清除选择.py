# -*- coding:utf-8 -*-
"""
作者：23242
日期：2025年06月29日
"""
import arcpy

selected = arcpy.management.SelectLayerByLocation(
    in_layer=[valid_pixel_shp],
    overlap_type="INTERSECT",
    select_features=country_shp,
    search_distance="300 Meters",
    selection_type="NEW_SELECTION"
)
arcpy.management.SelectLayerByAttribute(selected, "CLEAR_SELECTION")