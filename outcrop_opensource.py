# -*- coding: utf-8 -*-
"""
Created on Fri Nov 20 19:33:42 2020

@author: Brittany
"""


# Import modules
import numpy as np
import sys,os,pandas,csv,itertools,math #lasmod is the lidar toolset we use

import rasterio
import gdal
import tif_tools


import matplotlib.pyplot as plt
import pandas as pd
import os.path
import re

from osgeo import gdal
from osgeo import gdal_array
from osgeo import osr


#import data
curv_fs = gdal.Open("curv_fs.tif") #curvature range file
slope=gdal.Open("curv_fs.tif") #slope file

curv_np = np.array(curv_fs.GetRasterBand(1).ReadAsArray())
slope_np = np.array(slope.GetRasterBand(1).ReadAsArray())


#determining 95th percentile 
curvfs_95percentile = np.percentile(curv_np, 95)
print "curvfs_95percentile = " +str(curvfs_95percentile)

#Create a boolean where values are the standard devaiation off the mean
slopeb = np.where((slope_np>44),1,0)
curvb =  np.where(((curv_np>=curvfs_95percentile)),1,0)
critb = np.where((slopeb==1)|(curvb==1),1,0)




#tool to get raster to tiff :https://gist.github.com/jkatagi/a1207eee32463efd06fb57676dcf86c8
def array2raster(newRasterfn, dataset, array, dtype):
    """
    save GTiff file from numpy.array
    input:
        newRasterfn: save file name
        dataset : original tif file
        array : numpy.array
        dtype: Byte or Float32.
    """
    cols = array.shape[1]
    rows = array.shape[0]
    originX, pixelWidth, b, originY, d, pixelHeight = dataset.GetGeoTransform() 

    driver = gdal.GetDriverByName('GTiff')

    # set data type to save.
    GDT_dtype = gdal.GDT_Unknown
    if dtype == "Byte": 
        GDT_dtype = gdal.GDT_Byte
    elif dtype == "Float32":
        GDT_dtype = gdal.GDT_Float32
    else:
        print("Not supported data type.")

    # set number of band.
    if array.ndim == 2:
        band_num = 1
    else:
        band_num = array.shape[2]

    outRaster = driver.Create(newRasterfn, cols, rows, band_num, GDT_dtype)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))

    # Loop over all bands.
    for b in range(band_num):
        outband = outRaster.GetRasterBand(b + 1)
        # Read in the band's data into the third dimension of our array
        if band_num == 1:
            outband.WriteArray(array)
        else:
            outband.WriteArray(array[:,:,b])

    # setteing srs from input tif file.
    prj=dataset.GetProjection()
    outRasterSRS = osr.SpatialReference(wkt=prj)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()



#export rock cover
array2raster(rc_raw, curv_fs, critb, Float32)



##Now go into ArcGIS, import the rc_raw raster and run a neighborhood statistics tool on boolean raster
#spatial reference
'''
llpnt = slope.extent.lowerLeft
spref = slope.spatialReference
cellsize = 1

critfc = arcpy.NumPyArrayToRaster(critb.astype(float),llpnt,cellsize,cellsize)
arcpy.DefineProjection_management(critfc,spref) 
neighborhood = arcpy.sa.NbrRectangle(5,5, "CELL")
result_fs1 = arcpy.sa.FocalStatistics(critfc,neighborhood,"Mean")
result_fs1.save('result_fs5')
'''
#Where  mean of each cell is greater than 70% (or 95%) label that as rock cover
result_np =arcpy.RasterToNumPyArray(arcpy.sa.Raster('result_fs5'))
result_70percentile = np.percentile(result_np, 70) 

outCon2 = arcpy.sa.Con(arcpy.Raster('result_fs5') > result_70percentile, 1,0)
outCon2.save(env.workspace+"//"+r"rockcover")
