"""
Drone specifications for different DJI models
"""

DRONE_SPECS = {
    "DJI Mavic 3 Pro": {
        "max_speed": 21.0,  # m/s
        "min_altitude": 2,  # meters
        "max_altitude": 120,  # meters
        "camera_fov": 82.0,  # degrees
        "min_interval": 0.5  # seconds
    },
    "DJI Mini 4 Pro": {
        "max_speed": 16.0,
        "min_altitude": 2,
        "max_altitude": 120,
        "camera_fov": 82.0,
        "min_interval": 0.5
    },
    "DJI Mini 3 Pro": {
        "max_speed": 16.0,
        "min_altitude": 2,
        "max_altitude": 120,
        "camera_fov": 82.0,
        "min_interval": 0.5
    },
    "DJI Mini 3": {
        "max_speed": 16.0,
        "min_altitude": 2,
        "max_altitude": 120,
        "camera_fov": 82.0,
        "min_interval": 0.5
    },
    "DJI Air 3": {
        "max_speed": 19.0,
        "min_altitude": 2,
        "max_altitude": 120,
        "camera_fov": 82.0,
        "min_interval": 0.5
    },
    "DJI Air 3S": {
        "max_speed": 19.0,
        "min_altitude": 2,
        "max_altitude": 120,
        "camera_fov": 82.0,
        "min_interval": 0.5
    }
}
