## Description: This script translates the XML produced by Agisoft into a format that WebODM can understand

import xml.etree.ElementTree as ET
from collections import defaultdict
from pyproj import CRS, Proj, transform
import os, argparse

FILE_OUT_NAME = 'gcp_list.txt'
OUTPUT_EPSG = '32633'

def main(args):
    root = ET.parse(args.input_path).getroot()
    markers_coordinates = build_coordinates_map(root)
    pixel_locations_per_marker = build_pixel_locations_per_marker_map(root)
    mapped_marker_coordinates = map_coordinates_to_wgs84(root, markers_coordinates)
    proj4 = CRS.from_epsg(OUTPUT_EPSG).to_proj4()
    write_to_file(os.path.dirname(args.input_path), proj4, mapped_marker_coordinates, pixel_locations_per_marker)
    print('Done! A file called \'{}\' has been created in the same folder as the input file.'.format(FILE_OUT_NAME))

def transform_coordinates(input_proj, output_proj, coordinates):
    x, y, z = coordinates
    x2, y2 = transform(input_proj, output_proj, x, y)
    return (x2, y2, z)

def map_coordinates_to_wgs84(root, markers_coordinates):
    input_proj = get_proj_from_file(root)
    output_proj = Proj(init='epsg:' + OUTPUT_EPSG)
    return { marker_id: transform_coordinates(input_proj, output_proj, coordinates) for marker_id, coordinates in markers_coordinates.items() }
    
def get_proj_from_file(root):
    reference = root.find('chunk/reference').text
    crs = CRS.from_string(reference)
    proj4 = crs.to_proj4()
    return Proj(proj4)

def write_to_file(dir, proj4, markers_coordinates, pixel_locations_per_marker):
    with open(dir + '/' + FILE_OUT_NAME, 'w+') as file:
        file.write(proj4 + '\n')
        for marker_id in markers_coordinates:
            x, y, z = markers_coordinates[marker_id]
            for pixel_location in pixel_locations_per_marker[marker_id]:
                image_name, pixel_x, pixel_y = pixel_location
                file.write('{} {} {} {} {} {}.JPG\n'.format(x, y, z, pixel_x, pixel_y, image_name))

def build_pixel_locations_per_marker_map(root):
    camera_id_to_image_name = build_camera_id_to_image_map(root)
    locations_per_marker = defaultdict(set)
    for marker in root.findall('chunk/frames/frame/markers/marker'):
        id = marker.get('marker_id')
        for location in marker.findall('location'):
            image_name = camera_id_to_image_name[location.get('camera_id')]
            pixel_x, pixel_y = location.get('x'), location.get('y')
            locations_per_marker[id].add((image_name, pixel_x, pixel_y))
    return locations_per_marker

def build_camera_id_to_image_map(root):
     return dict([(camera.get('id'), camera.get('label')) for camera in root.findall('chunk/cameras/camera')])

def build_coordinates_map(root):
    markers_coordinates = { }
    for marker in root.findall('chunk/markers/marker'):
        id = marker.get('id')
        ref = marker.find('reference')
        x, y, z = ref.get('x'), ref.get('y'), ref.get('z')
        markers_coordinates[id] = (x, y, z)
    return markers_coordinates

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'This parser reads an XML with GCP (Ground Control Points) information, and produces a new file called {} with the appropriate format for WebODM'.format(FILE_OUT_NAME))
    parser.add_argument('-i', '--input_path', type = str, required = True, help = 'The path for the input file')
    args = parser.parse_args()
    main(args)
