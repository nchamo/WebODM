#!/usr/bin/env python

import cv2, math, argparse
import numpy as np
from osgeo import gdal, osr
from geojson import Feature, FeatureCollection, MultiPolygon, dumps

# CONSTANTS
NO_ELEVATION = -9999

def main(args):
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (args.kernel_size, args.kernel_size))
    tiff = gdal.Open(args.geotiff)
    tiff_array = np.array(tiff.GetRasterBand(1).ReadAsArray())
    min_elevation = math.floor(np.amin(tiff_array[tiff_array != NO_ELEVATION]))
    max_elevation = math.ceil(tiff_array.max())
    contour_transform = ContourTransform(tiff, args.epsg)

    features = []

    for level in np.arange(min_elevation, max_elevation, args.interval):
        # Binarize the image. Everything in [level, level + args.interval) is white. Everything else is black
        surface_array = np.where((level <= tiff_array) & (tiff_array < level + args.interval), 255, 0).astype(np.uint8)
        # Apply kernel to reduce noise
        closing = cv2.morphologyEx(surface_array, cv2.MORPH_CLOSE, kernel)
        # Find contours
        contours, hierarchy = cv2.findContours(closing, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        # Transform contours from pixels to coordinates
        mapped_contours = list(map(contour_transform.transform_contour, contours))
        # Build the MultiPolygon for based on the contours and their hierarchy
        built_multi_polygon = LevelBuilder(level, mapped_contours, hierarchy[0]).build_multi_polygon()
        features.append(built_multi_polygon)

    dump = dumps(FeatureCollection(features))
    with open(args.output, 'w+') as output:
        output.write(dump)

class LevelBuilder:
    def __init__(self, level, contours, hierarchy):
        self.level = level
        self.contours = contours
        self.hierarchy = hierarchy

    def build_polygon(self, idx):
        polygon_contours = [self.contours[idx]]
        [_, _, child, _] = self.hierarchy[idx]
        while child >= 0:
            polygon_contours.append(self.contours[child])
            next, _, _, _ = self.hierarchy[child]
            child = next
        return polygon_contours

    def build_multi_polygon(self):
        polygons = []
        idx = 0
        while idx >= 0:
            polygons.append(self.build_polygon(idx))
            [next, _, _, _] = self.hierarchy[idx]
            idx = next
        multi_polygon = MultiPolygon(polygons)
        return Feature(geometry = multi_polygon, properties = { 'level': int(self.level) })  

class ContourTransform:
    def __init__(self, tiff, output_epsg):
        self.pixel_transform = self.get_pixel_transform(tiff, output_epsg)
        
    def transform_contour(self, contour):
        contour_in_pixel_format = list(map(lambda x: (x[0][0], x[0][1]), contour))
        return list(map(self.pixel_transform, contour_in_pixel_format))  

    def get_pixel_transform(self, tiff, output_epsg):
        xoffset, px_w, rot1, yoffset, rot2, px_h  = tiff.GetGeoTransform()
        # get CRS from dataset 
        crs = osr.SpatialReference()
        crs.ImportFromWkt(tiff.GetProjectionRef())
        # create lat/long crs with WGS84 datum
        crsGeo = osr.SpatialReference()
        crsGeo.ImportFromEPSG(output_epsg) # 4326 is the EPSG id of lat/long crs 
        transformation = osr.CoordinateTransformation(crs, crsGeo)
        def pixel_to_long_lan(pixel):
            (x, y) = pixel
            posX = px_w * x + rot1 * y + xoffset + px_w / 2.0
            posY = rot2 * x + px_h * y + yoffset + px_h / 2.0
            (lon, lan, z) = transformation.TransformPoint(posX, posY)
            return (lon, lan)
        
        return pixel_to_long_lan

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'This script takes a GeoTIFF file, calculates its heighmap, and outputs it as a GeoJSON')
    parser.add_argument('geotiff', type = str, help = 'The path for the input file')
    parser.add_argument('interval', type = float, help = 'The interval used to generate the diferent levels')
    parser.add_argument('-e', '--epsg', type = int, help = 'The epsg code that will be used for output', default = 4326)
    parser.add_argument('-k', '--kernel_size', type = int, help = 'The size of the kernel that will be used to clean up the contours', default = 5)
    parser.add_argument('-o', '--output', type = str, help = 'The path for the output file', default = "output.json")
    
    args = parser.parse_args()
    main(args)