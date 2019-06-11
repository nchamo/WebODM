from rasterio import warp, transform
import rasterio as rio

def map_pixels_to_coordinates(reference_tiff, dst_epsg, pixels):
    """We are assuming that the pixels are a list of tuples. For example: [(row1, col1), (row2, col2)]"""
    coordinates = [reference_tiff.xy(row, col) for (row, col) in pixels]
    dst_crs = rio.crs.CRS.from_epsg(dst_epsg)
    return map_to_new_crs(reference_tiff.crs, dst_crs, coordinates)
    
def map_coordinates_to_pixels(reference_tiff, src_epsg, coordinates):
    src_crs = rio.crs.CRS.from_epsg(src_epsg)
    coordinates = map_to_new_crs(src_crs, reference_tiff.crs, coordinates)
    return [reference_tiff.index(x, y) for (x, y) in coordinates]

def map_to_new_crs(src_crs, target_crs, coordinates):
    xs = [x for (x, _) in coordinates]
    ys = [y for (_, y) in coordinates]
    transformed = warp.transform(src_crs, target_crs, xs, ys)
    return [(x, y) for x, y in zip(transformed[0], transformed[1])]