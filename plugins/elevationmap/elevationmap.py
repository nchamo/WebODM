#!/usr/bin/env python3

# Doing this to be able to use the code in common
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2, math, argparse
import numpy as np
import rasterio as rio
from geojson import Feature, FeatureCollection, MultiPolygon, dumps
from common import map_coordinates

def main(args):
    # Open dsm
    dsm = rio.open(args.dsm)
    # Read the tiff as an numpy masked array
    dsm_array = dsm.read(1, masked = True)
    # Create a kernel based on the parameter 'noise_filter_size' and the tiff resolution
    kernel = get_kernel(args.noise_filter_size, dsm)
    
    # Check if we want to use the dtm also
    if args.dtm != None:
        # Open the dtm
        dtm = rio.open(args.dtm)
        # Assert that the dtm and dsm have the same bounds and resolution
        assert_same_bounds_and_resolution(dsm, dtm)
        # Calculate the different between the dsm and dtm
        array = calculate_difference(dsm_array, dtm)
    else:
        array = dsm_array    
    
    # Calculate the ranges based on the parameter 'intervals' and the array
    ranges = calculate_ranges(args.intervals, array)   
        
    features = []
    
    for bottom, top in ranges:
        # Binarize the image. Everything in [bottom, top) is white. Everything else is black
        surface_array = np.ma.where((bottom <= array) & (array < top), 255, 0).astype(np.uint8)
        # Apply kernel to reduce noise
        without_noise = cv2.morphologyEx(surface_array, cv2.MORPH_CLOSE, kernel) if kernel is not None else surface_array
        # Find contours
        contours, hierarchy = cv2.findContours(without_noise, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        # Check if we found something
        if len(contours) > 0:
            # Transform contours from pixels to coordinates
            mapped_contours = [map_coordinates.map_pixels_to_coordinates(dsm, args.epsg, to_pixel_format(contour)) for contour in contours]
            # Build the MultiPolygon for based on the contours and their hierarchy
            built_multi_polygon = LevelBuilder(bottom, top, mapped_contours, hierarchy[0]).build_multi_polygon()
            features.append(built_multi_polygon)
    
    # Write the GeoJSON to a file
    dump = dumps(FeatureCollection(features))
    with open(args.output, 'w+') as output:
        output.write(dump)   

def calculate_difference(dsm_array, dtm):
    dtm_array = dtm.read(1, masked = True)
    difference = dsm_array - dtm_array
    difference.data[difference < 0] = 0
    return difference

def assert_same_bounds_and_resolution(dsm, dtm):
    if dtm.bounds != dsm.bounds or dtm.res != dsm.res:
        raise Exception("DTM and DSM have differenct bounds or resolution.")

def to_pixel_format(contour):
    return [(pixel[0][1], pixel[0][0]) for pixel in contour]

def get_kernel(noise_filter_size, dsm):
    if noise_filter_size <= 0:
        return None
    if dsm.crs.linear_units != 'metre':
        noise_filter_size *= 3.2808333333465 # Convert meter to feets
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (round(noise_filter_size / dsm.res[0]), round(noise_filter_size / dsm.res[1])))    

def calculate_ranges(interval_text, array):
    if is_number(interval_text):
        min_elevation = math.floor(np.amin(array))
        max_elevation = math.ceil(np.amax(array))
        interval = float(interval_text)
        return [(floor, floor + interval) for floor in np.arange(min_elevation, max_elevation, interval)]
    else:
        ranges = [validate_and_convert_to_range(range) for range in interval_text.split(',')]
        if len(ranges) == 0:
            raise Exception('Please add a range.')
        elif len(ranges) > 1:
            ranges.sort()
            for i in range(len(ranges) - 1):
                if ranges[i][1] > ranges[i + 1][0]:
                    raise Exception('Please make sure that the ranges don\'t overlap.')        
        return ranges     

def is_number(text):
    try:
        float(text)
        return True
    except ValueError:
        return False
    
def validate_and_convert_to_range(range):
    range = range.strip().split('-')
    if len(range) != 2:
        raise Exception('Ranges must have a beggining and an end.')
    if not is_number(range[0]) or not is_number(range[1]):
        raise Exception('Please make sure that both the beggining and end of the range are numeric.')
    range = (float(range[0]), float(range[1]))    
    if (range[0] >= range[1]):
        raise Exception('The end of the range must be greater than the beggining.')
    return range             

class LevelBuilder:
    def __init__(self, bottom, top, contours, hierarchy):
        self.bottom = bottom
        self.top = top
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
        return Feature(geometry = multi_polygon, properties = { 'bottom': int(self.bottom), 'top': int(self.top) })  

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'This script takes a GeoTIFF file, calculates its heighmap, and outputs it as a GeoJSON')
    parser.add_argument('dsm', type = str, help = 'The path for the dsm file')
    parser.add_argument('intervals', type = str, help = 'The intervals used to generate the diferent elevation levels')
    parser.add_argument('-d', '--dtm', type = str, help = 'The path for the dtm file')
    parser.add_argument('-e', '--epsg', type = int, help = 'The epsg code that will be used for output', default = 4326)
    parser.add_argument('-k', '--noise_filter_size', type = float, help = 'Area in meters where we will clean up noise in the contours', default = 2)
    parser.add_argument('-o', '--output', type = str, help = 'The path for the output file', default = "output.json")
    
    args = parser.parse_args()
    try:
        main(args)
    except Exception as e:
        with open('error.txt', 'w+') as output:
            output.write(str(e))