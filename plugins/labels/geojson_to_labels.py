#!/usr/bin/env python3

# Doing this to be able to use the code in common
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import xml.etree.ElementTree as ET
import rasterio as rio
import argparse
from geojson import load
from common import map_coordinates

def main(args):
    # Parse the tiff into objects
    with rio.open(args.geotiff) as tiff:
        objects = parse_json(tiff, args.geojson)
    
    # Build an XML element for each object
    xml_objects = [object.build_xml() for object in objects]
    
    # Open the annotations file, or create one if the isn't any
    file, root, last_id = parse_or_create_annotation(args.annotations)
    
    # For each new object, add an id to it, and append it to the root element in the annotations file 
    for xml_object in xml_objects:
        last_id += 1
        create_subelement(xml_object, 'id', str(last_id))
        root.append(xml_object)
    
    # Write the new file to disk    
    file.write(args.annotations)
    # Give everyone access to read-write it
    os.chmod(args.annotations, 0o666)

def parse_or_create_annotation(annotations_path):
    file = ET.parse(annotations_path) if os.path.exists(annotations_path) else build_default_xml_structure(annotations_path)    
    root = file.getroot()
    object_ids = [int(object.find('id').text) for object in root.findall('object')]
    object_ids.sort()
    last_id = object_ids[-1] if len(object_ids) > 0 else -1
    return file, root, last_id

def create_subelement(parent, tag, value = None):
    subelement = ET.SubElement(parent, tag)
    if value is not None:
        subelement.text = value
    return subelement

def build_default_xml_structure(annotations_path):
    path = annotations_path[annotations_path.index('project'):]
    folder = os.path.dirname(path)
    filename = os.path.splitext(os.path.basename(path))[0] + '.png'
    root = ET.Element('annotation')
    create_subelement(root, 'filename', filename)
    create_subelement(root, 'folder', folder)
    source = create_subelement(root, 'source')
    create_subelement(source, 'sourceImage', 'The MIT-CSAIL database of objects and scenes')
    create_subelement(source, 'sourceAnnotation', 'LabelMe Webtool')
    image_size = create_subelement(root, 'imagesize')
    create_subelement(image_size, 'nrows')
    create_subelement(image_size, 'ncols')
    return ET.ElementTree(root)
    
def parse_json(reference_tiff, geojson_path):
    with open(geojson_path, "r") as content:
        feature_collection = load(content)
    objects = []
    for multi_polygon_feature in feature_collection.features:
        objects += parse_multipolygon(reference_tiff, multi_polygon_feature) 
    return objects
    
def parse_multipolygon(reference_tiff, multi_polygon_feature):
    objects =  [Object(reference_tiff, multi_polygon_feature.properties, polygon) for polygon in multi_polygon_feature.geometry.coordinates]
    return [object for object in objects if len(object.points) >= 3]

class Object:
    def __init__(self, reference_tiff, properties, polygon_coords):
        self.name = "From {} To {}".format(properties['bottom'], properties['top'])
        pixels = map_coordinates.map_coordinates_to_pixels(reference_tiff, 4326, polygon_coords[0]) # Only use the outside of the polygon, ignore the holes
        self.points = [(col, row) for (row, col) in pixels]
    
    def build_xml(self):
        object = ET.Element('object')
        create_subelement(object, 'name', self.name)
        create_subelement(object, 'deleted', '0')
        create_subelement(object, 'verified', '0')
        create_subelement(object, 'occluded', 'no')
        create_subelement(object, 'attributes')
        parts = create_subelement(object, 'parts')
        create_subelement(parts, 'hasparts')
        create_subelement(parts, 'ispartof')
        polygon = create_subelement(object, 'polygon')
        for point in self.points:
            pt = create_subelement(polygon, 'pt')
            create_subelement(pt, 'x', str(point[0]))
            create_subelement(pt, 'y', str(point[1]))
        return object    
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'This script takes a GeoTIFF and GeoJson text and translates the polygons to pixels in the GeoTIFF. The output is an XML file for LabelMe to use')
    parser.add_argument('geotiff', type = str, help = 'The path for the GeoTIFF file')
    parser.add_argument('annotations', type = str, help = 'The path for the annotations file')
    parser.add_argument('geojson', type = str, help = 'The path of the file containing the GeoJson')
    
    args = parser.parse_args()
    main(args)