import math

def validate_parameters(params, drone_specs):
    errors = []
    if params['altitude'] > drone_specs.get("max_altitude", 120):
        errors.append("Altitude exceeds drone's max altitude.")
    if params['speed'] > drone_specs.get("max_speed", 15):
        errors.append("Speed exceeds drone's max speed.")
    return errors

def generate_grid_path(area_width, area_height, overlap, sidelap, altitude, speed, interval, fov, center_lat, center_lon, direction, rotation_deg):
    path = []
    spacing_x = fov * (1 - sidelap / 100)
    spacing_y = fov * (1 - overlap / 100)
    cols = max(1, int(area_width / spacing_x))
    rows = max(1, int(area_height / spacing_y))

    offset_x = (cols - 1) / 2 * spacing_x
    offset_y = (rows - 1) / 2 * spacing_y

    for row in range(rows):
        row_points = []
        for col in range(cols):
            x = -offset_x + col * spacing_x
            y = -offset_y + row * spacing_y
            lat = center_lat + (y / 111000)
            lon = center_lon + (x / (111000 * math.cos(math.radians(center_lat))))
            row_points.append((lon, lat))
        if row % 2 == 1:
            row_points.reverse()
        path.extend(row_points)

    return path

def generate_oblique_path(center_lat, center_lon, area_width, area_height, altitude, tilt, layers):
    path = []
    radius = max(area_width, area_height) / 2
    if radius < 5:
        radius = 100  # fallback minimum radius in meters

    for layer in range(layers):
        r = radius * (1 - 0.1 * layer)
        for angle in range(0, 360, 15):
            theta = math.radians(angle)
            dx = r * math.cos(theta)
            dy = r * math.sin(theta)
            lat = center_lat + (dy / 111000)
            lon = center_lon + (dx / (111000 * math.cos(math.radians(center_lat))))
            path.append((lon, lat))
    return path

def estimate_flight_metrics(path, speed, drone_specs):
    def haversine(p1, p2):
        from math import radians, sin, cos, sqrt, atan2
        R = 6371
        lat1, lon1 = radians(p1[1]), radians(p1[0])
        lat2, lon2 = radians(p2[1]), radians(p2[0])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
        return 2 * R * atan2(sqrt(a), sqrt(1 - a))

    dist_km = sum(haversine(path[i], path[i+1]) for i in range(len(path)-1))
    minutes = (dist_km * 1000) / speed / 60
    battery_time = drone_specs.get("battery_minutes", 20)
    batteries = max(1, math.ceil(minutes / battery_time))
    return dist_km, minutes, batteries
