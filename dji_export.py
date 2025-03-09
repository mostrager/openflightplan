"""
DJI flight path export functionality
Supports export to KMZ format for Google Earth visualization
"""
import csv
import os
from datetime import datetime
import simplekml
import zipfile
import tempfile

def get_action_params(action_type):
    """Convert action type to DJI parameters"""
    action_params = {
        "Take Picture": {"type": 2, "param": 0},  # Take Photo
        "Start Recording": {"type": 3, "param": 0},  # Start Recording
        "Stop Recording": {"type": 4, "param": 0},  # Stop Recording
    }
    return action_params.get(action_type, {"type": 0, "param": 0})

def create_dji_waypoint_file(path_coords, params, drone_model, waypoint_action="Take Picture"):
    """
    Create DJI compatible waypoint CSV file
    Format based on DJI waypoint file specification
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"dji_waypoints_{timestamp}.csv"

    # Get action parameters
    action = get_action_params(waypoint_action)

    # DJI waypoint headers
    headers = [
        "latitude", "longitude", "altitude(m)", 
        "heading(deg)", "curvesize(m)", "rotationdir",
        "gimbalmode", "gimbalpitchangle", "actiontype1",
        "actionparam1", "actiontype2", "actionparam2",
        "altitudemode", "speed(m/s)", "poi_latitude",
        "poi_longitude", "poi_altitude(m)", "poi_altitudemode"
    ]

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()

        for x, y in path_coords:
            waypoint = {
                "latitude": y,  # Assuming y is latitude
                "longitude": x,  # Assuming x is longitude
                "altitude(m)": params['altitude'],
                "heading(deg)": 0,
                "curvesize(m)": 0.2,
                "rotationdir": 0,
                "gimbalmode": 0,
                "gimbalpitchangle": -90,  # Pointing straight down
                "actiontype1": action["type"],
                "actionparam1": action["param"],
                "actiontype2": 0,  # No second action
                "actionparam2": 0,
                "altitudemode": 1,  # Relative altitude
                "speed(m/s)": params['speed'],
                "poi_latitude": 0,
                "poi_longitude": 0,
                "poi_altitude(m)": 0,
                "poi_altitudemode": 0
            }
            writer.writerow(waypoint)

    return filename

def create_kml_file(path_coords, params):
    """
    Create KMZ file for visualization in Google Earth
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_kml = f"flight_path_{timestamp}.kml"
    final_kmz = f"flight_path_{timestamp}.kmz"

    kml = simplekml.Kml()

    # Create flight path line
    linestring = kml.newlinestring(name="Flight Path")
    linestring.coords = [(x, y, params['altitude']) for x, y in path_coords]
    linestring.altitudemode = simplekml.AltitudeMode.relativetoground
    linestring.style.linestyle.width = 4
    linestring.style.linestyle.color = simplekml.Color.blue

    # Add waypoint markers
    for i, (x, y) in enumerate(path_coords):
        point = kml.newpoint(name=f"Waypoint {i+1}")
        point.coords = [(x, y, params['altitude'])]
        point.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'

    # Save as KML first
    kml.save(temp_kml)

    # Convert to KMZ
    with zipfile.ZipFile(final_kmz, 'w') as kmz:
        kmz.write(temp_kml, arcname=os.path.basename(temp_kml))

    # Clean up temporary KML file
    os.remove(temp_kml)

    return final_kmz

def validate_dji_parameters(path_coords, params, drone_model):
    """
    Validate parameters according to DJI specifications
    """
    errors = []

    # Check number of waypoints
    if len(path_coords) > 99:
        errors.append("DJI drones support maximum 99 waypoints per mission")

    # Check minimum distance between waypoints (2 meters minimum)
    for i in range(len(path_coords)-1):
        x1, y1 = path_coords[i]
        x2, y2 = path_coords[i+1]
        distance = ((x2-x1)**2 + (y2-y1)**2)**0.5
        if distance < 2:
            errors.append(f"Waypoints {i+1} and {i+2} are too close (minimum 2m required)")

    return errors