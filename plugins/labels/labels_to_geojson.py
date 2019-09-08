#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import argparse, rasterio
from geojson import Feature, FeatureCollection, Polygon, dumps
import map_coordinates

def main(args):
    objects = parse_annotation(args.annotations)
    
    features = []
    with rasterio.open(args.geotiff) as tiff:
        features = [object.build_feature(tiff, args.epsg) for object in objects]

    dump = dumps(FeatureCollection(features))
    with open(args.output, 'w+') as output:
        output.write(dump)

def parse_annotation(xml_path):
    root = ET.parse(xml_path).getroot()
    return [Object(xml_object) for xml_object in root.findall('object') if xml_object.find('verified').text == '1' and xml_object.find('deleted').text == '0'] 

class Object:
    def __init__(self, xml_object):
        self.name = xml_object.find('name').text
        attributes = xml_object.find('attributes').text
        self.attributes = "" if not attributes else attributes
        self.points = [(float(point.find('y').text), float(point.find('x').text)) for point in xml_object.findall('polygon/pt')]
    
    def build_feature(self, tiff, epsg_code):
        coordinates = map_coordinates.map_pixels_to_coordinates(tiff, epsg_code, self.points)
        polygon = Polygon([coordinates])
        return Feature(geometry = polygon, properties = { 'name': self.name, 'attributes': self.attributes })

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'This script takes a GeoTIFF file and a LabelMe annotations file, and transforms the labels to GeoJSON')
    parser.add_argument('geotiff', type = str, help = 'The path for the GeoTIFF file')
    parser.add_argument('annotations', type = str, help = 'The path for the annotations file')
    parser.add_argument('-e', '--epsg', type = int, help = 'The epsg code that will be used for output', default = 4326)
    parser.add_argument('-o', '--output', type = str, help = 'The path for the output file', default = "output.json")
    
    args = parser.parse_args()
    main(args)