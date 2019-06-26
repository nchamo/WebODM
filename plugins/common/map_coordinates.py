from rasterio import warp, transform
import rasterio as rio

def map_pixels_to_coordinates(reference_tiff, dst_epsg, pixels):
    """We are assuming that the pixels are a list of tuples. For example: [(row1, col1), (row2, col2)]"""
    rows = [row for (row, _) in pixels]
    cols = [col for (_, col) in pixels]
    xs, ys = transform.xy(reference_tiff.transform, rows, cols)
    dst_crs = rio.crs.CRS.from_epsg(dst_epsg)
    return map_to_new_crs(reference_tiff.crs, dst_crs, xs, ys)
    
def map_coordinates_to_pixels(reference_tiff, src_epsg, coordinates):
    src_crs = rio.crs.CRS.from_epsg(src_epsg)
    coordinates = map_to_new_crs_with_coordinates(src_crs, reference_tiff.crs, coordinates)
    return [reference_tiff.index(x, y) for (x, y) in coordinates]

def map_to_new_crs_with_coordinates(src_crs, target_crs, coordinates):
    xs = [x for (x, _) in coordinates]
    ys = [y for (_, y) in coordinates]
    return map_to_new_crs(src_crs, target_crs, xs, ys)

def map_to_new_crs(src_crs, target_crs, xs, ys):
    transformed = warp.transform(src_crs, target_crs, xs, ys)
    return [(x, y) for x, y in zip(transformed[0], transformed[1])]    