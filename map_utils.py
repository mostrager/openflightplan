import folium
from folium.plugins import Draw, Geocoder
import streamlit as st
import requests
import numpy as np
import os
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

def search_location(query):
    """Search for a location using Nominatim geocoding service"""
    try:
        geolocator = Nominatim(user_agent="uav_flight_planner", timeout=5)
        location = geolocator.geocode(query)
        if location:
            return location.latitude, location.longitude
        return None, None
    except (GeocoderTimedOut, Exception) as e:
        st.warning(f"Location search error: {str(e)}. Using default map location.")
        return None, None

def get_user_location():
    """Prompt user for location access and return coordinates if granted."""
    user_location = st.checkbox("Allow Location Access")
    if user_location:
        try:
            response = requests.get("https://ipinfo.io/json")
            if response.status_code == 200:
                data = response.json()
                lat, lon = map(float, data["loc"].split(","))
                return lat, lon
        except Exception as e:
            st.error(f"Failed to retrieve location: {e}")
    return None, None

def create_map():
    """Create a Folium map with drawing controls and selectable basemaps."""
    try:
        # Add location search
        location_query = st.text_input("Search Location", "")
        search_lat, search_lon = None, None
        if location_query:
            search_lat, search_lon = search_location(location_query)
            if search_lat and search_lon:
                st.success(f"Location found: {location_query}")

        # Streamlit select box for basemap selection
        basemap_options = {
            "OpenStreetMap": "OpenStreetMap",
            "Esri World Imagery": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "Esri Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "Google Satellite": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            "Bing Aerial": "https://ecn.t3.tiles.virtualearth.net/tiles/a{q}.jpeg?g=1"
        }

        basemap_choice = st.selectbox("Select Basemap", list(basemap_options.keys()))

        # Get user location if permission is granted
        user_lat, user_lon = get_user_location()

        # Set initial map center and zoom
        if search_lat and search_lon:
            center = [search_lat, search_lon]
            zoom = 13
        elif user_lat and user_lon:
            center = [user_lat, user_lon]
            zoom = 13
        else:
            center = [20.0, 0.0]
            zoom = 2

        # Create Folium map
        m = folium.Map(location=center, zoom_start=zoom, tiles=None)

        # Add the selected basemap
        folium.TileLayer(
            basemap_options[basemap_choice],
            attr="Basemap provided by respective service",
            name=basemap_choice
        ).add_to(m)

        # Add drawing controls
        draw = Draw(
            draw_options={
                'polyline': False,
                'rectangle': True,
                'polygon': True,
                'circle': True,
                'marker': False,
                'circlemarker': False
            },
            edit_options={'edit': False}
        )
        m.add_child(draw)

        # Add layer control to switch basemaps
        folium.LayerControl().add_to(m)

        return m

    except Exception as e:
        st.error(f"An error occurred while creating the map: {e}")
        # Return a simple default map instead of None
        default_map = folium.Map(location=[20.0, 0.0], zoom_start=2)
        draw = Draw(
            draw_options={
                'polyline': False,
                'rectangle': True,
                'polygon': True,
                'circle': True,
                'marker': False,
                'circlemarker': False
            },
            edit_options={'edit': False}
        )
        default_map.add_child(draw)
        return default_map

def calculate_area_bounds(geometry):
    """Calculate the bounds and center of the drawn area"""
    try:
        if geometry['type'] == 'Polygon':
            coordinates = geometry['coordinates'][
                0]  # First ring of coordinates
            lats = [coord[1] for coord in coordinates]
            lons = [coord[0] for coord in coordinates]

            min_lat, max_lat = min(lats), max(lats)
            min_lon, max_lon = min(lons), max(lons)

            # Calculate center
            center_lat = (min_lat + max_lat) / 2
            center_lon = (min_lon + max_lon) / 2

            # Calculate width and height in meters (approximate)
            width = haversine_distance(min_lat, min_lon, min_lat, max_lon)
            height = haversine_distance(min_lat, min_lon, max_lat, min_lon)

            return {
                'min_lat': min_lat,
                'max_lat': max_lat,
                'min_lon': min_lon,
                'max_lon': max_lon,
                'center_lat': center_lat,
                'center_lon': center_lon,
                'width': width,
                'height': height
            }

        # Handle circle drawing
        elif geometry['type'] == 'Point' and 'radius' in geometry:
            lat = geometry['coordinates'][1]
            lon = geometry['coordinates'][0]
            radius_meters = geometry['radius']

            # Convert radius from meters to approximate degrees
            radius_lat = radius_meters / 111000  # Approximate degree conversion
            radius_lon = radius_meters / (111000 * np.cos(np.radians(lat)))

            return {
                'min_lat': lat - radius_lat,
                'max_lat': lat + radius_lat,
                'min_lon': lon - radius_lon,
                'max_lon': lon + radius_lon,
                'center_lat': lat,
                'center_lon': lon,
                'width': radius_meters * 2,
                'height': radius_meters * 2
            }

        return None
    except Exception as e:
        st.error(f"Error calculating area bounds: {e}")
        return None


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371000  # Radius of earth in meters
    return c * r