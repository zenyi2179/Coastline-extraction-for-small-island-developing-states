import os
import numpy as np
import matplotlib.pyplot as plt
from osgeo import gdal


def process_and_display_raster(year, input_file, output_png=None):
    """
    Process a raster file to extract pixels with values > 5 and display the result.

    Args:
        input_file (str): Path to the input raster file.
        output_png (str, optional): Path to save the processed image as a PNG file. Default is None.
    """
    # Open the raster file
    dataset = gdal.Open(input_file)
    if dataset is None:
        print(f"Failed to open file: {input_file}")
        return

    # Read the first band (assuming single band)
    band = dataset.GetRasterBand(1)
    raster_data = band.ReadAsArray()

    value = 5
    if year == 2020:
        value = 10
    if 'db' in input_file :
        value = 70

    # Apply the threshold (values > 5)
    thresholded_data = np.where(raster_data > value, raster_data, np.nan)

    # Display the processed image
    plt.figure(figsize=(10, 8))
    plt.imshow(thresholded_data, cmap="viridis", interpolation="nearest")
    plt.colorbar(label="Pixel Value")
    plt.title("Processed Image: Values > 5")
    plt.axis("off")
    plt.show()

    # Save to PNG if output path is provided
    if output_png:
        plt.imsave(output_png, thresholded_data, cmap="viridis")
        print(f"Image saved as: {output_png}")


# Input raster file and optional output PNG path
tif_task = '149E10Srb'
# tif_task = '170W20Slu'
year = 2020

tif_name = fr'{tif_task}_ls578_Index'
# input_raster = fr"E:\_GoogleDrive\SG_Check_Y{(year%100):02}\{tif_name}.tif"
input_raster = fr"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\SIDs_Grid_Y{(year%100):02}\{tif_name}.tif"
# input_raster = fr"E:\_OrderingProject\F_IslandsBoundaryChange\c_GeeData\SIDs_Grid_Y{(year%100):02}_db\{tif_name}.tif"

# output_png = r"E:\_GoogleDrive\SG_Check_Y00\Processed_Image.png"
# Process and display the raster
process_and_display_raster(year, input_raster, output_png=None)
