import numpy as np
from math import tan, radians, cos, sin
import logging
from geopy.distance import geodesic

def calculate_ground_coverage(altitude, fov):
    """Calculate the ground coverage width based on altitude and field of view"""
    width = 2 * altitude * tan(radians(fov / 2))
    return width

def rotate_point(x, y, cx, cy, angle_deg):
    """Rotate a point around a center (cx, cy) by angle_deg degrees"""
    angle_rad = radians(angle_deg)
    cos_a = cos(angle_rad)
    sin_a = sin(angle_rad)
    dx = x - cx
    dy = y - cy
    new_x = cx + (dx * cos_a - dy * sin_a)
    new_y = cy + (dx * sin_a + dy * cos_a)
    return new_x, new_y

def generate_grid_path(area_width, area_height, overlap, sidelap, altitude, speed, interval, fov, center_lat=None, center_lon=None, direction='north_south', rotation_deg=0):
    """Generate grid path coordinates based on input parameters"""
    if center_lat is None or center_lon is None:
        raise ValueError("Center coordinates must be provided")

    logging.info(f"Generating {direction} grid path with: width={area_width}m, height={area_height}m, center=({center_lat}, {center_lon})")

    # Calculate number of flight lines based on overlap
    ground_coverage = calculate_ground_coverage(altitude, fov)
    line_spacing = ground_coverage * (1 - sidelap / 100)

    # For east-west direction, swap width and height for line calculations
    if direction == 'east_west':
        area_width, area_height = area_height, area_width

    num_lines = max(2, int(np.ceil(area_width / line_spacing)))
    photo_spacing = ground_coverage * (1 - overlap / 100)
    points_per_line = max(2, int(np.ceil(area_height / photo_spacing)))

    logging.info(f"Calculated {num_lines} flight lines with {points_per_line} points per line")

    # Calculate coordinates using geopy for accurate distance calculations
    width_offset = area_width / 2
    height_offset = area_height / 2

    if direction == 'north_south':
        top_left = geodesic(kilometers=width_offset / 1000).destination(point=(center_lat, center_lon), bearing=270)
        top_left = geodesic(kilometers=height_offset / 1000).destination(point=top_left, bearing=0)
    else:
        top_left = geodesic(kilometers=width_offset / 1000).destination(point=(center_lat, center_lon), bearing=0)
        top_left = geodesic(kilometers=height_offset / 1000).destination(point=top_left, bearing=270)

    meters_per_lat = 111320
    meters_per_lon = meters_per_lat * np.cos(np.radians(center_lat))

    if direction == 'north_south':
        lon_step = line_spacing / meters_per_lon
        lat_step = photo_spacing / meters_per_lat
    else:
        lon_step = photo_spacing / meters_per_lon
        lat_step = line_spacing / meters_per_lat

    path_coords = []
    for i in range(num_lines):
        if direction == 'north_south':
            current_lon = top_left[1] + (i * lon_step)
            for j in range(points_per_line) if i % 2 == 0 else range(points_per_line - 1, -1, -1):
                current_lat = top_left[0] - (j * lat_step)
                path_coords.append((current_lon, current_lat))
        else:
            current_lat = top_left[0] - (i * lat_step)
            for j in range(points_per_line) if i % 2 == 0 else range(points_per_line - 1, -1, -1):
                current_lon = top_left[1] + (j * lon_step)
                path_coords.append((current_lon, current_lat))

    logging.info(f"Generated {len(path_coords)} waypoints")

    # Rotate coordinates around center if needed
    if rotation_deg != 0:
        rotated_coords = []
        for lon, lat in path_coords:
            rotated_lon, rotated_lat = rotate_point(lon, lat, center_lon, center_lat, rotation_deg)
            rotated_coords.append((rotated_lon, rotated_lat))
        path_coords = rotated_coords

    return path_coords

def validate_parameters(params, drone_specs):
    """Validate flight parameters against drone specifications"""
    errors = []

    if params['altitude'] < drone_specs['min_altitude']:
        errors.append(f"Altitude must be at least {drone_specs['min_altitude']}m")
    if params['altitude'] > drone_specs['max_altitude']:
        errors.append(f"Altitude cannot exceed {drone_specs['max_altitude']}m")

    if params['speed'] > drone_specs['max_speed']:
        errors.append(f"Speed cannot exceed {drone_specs['max_speed']}m/s")

    if params['interval'] < drone_specs['min_interval']:
        errors.append(f"Interval cannot be less than {drone_specs['min_interval']}s")

    if not (0 <= params['overlap'] <= 95):
        errors.append("Overlap must be between 0% and 95%")

    if not (0 <= params['sidelap'] <= 95):
        errors.append("Sidelap must be between 0% and 95%")

    return errors
