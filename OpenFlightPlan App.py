import streamlit as st
st.set_page_config(page_title="OpenFlightPlan", page_icon="🚁️", layout="wide")

import numpy as np
import pandas as pd
import folium
import os
import logging
import sys
import io
import simplekml
from streamlit_folium import st_folium
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from drone_specs import DRONE_SPECS
from flight_calculator import generate_grid_path, validate_parameters
from utils import create_flight_path_plot
from map_utils import calculate_area_bounds
from dji_export import create_kml_file

# New create_map function with search bar
def create_map():
    import folium
    from folium.plugins import Draw, Geocoder

    base_map = folium.Map(
        location=[40.7128, -74.0060],  # Default center (New York City)
        zoom_start=12,
        control_scale=True
    )

    draw = Draw(
        export=True,
        filename='my-draw.geojson',
        draw_options={
            'polyline': False,
            'polygon': True,
            'circle': False,
            'marker': False,
            'circlemarker': False,
            'rectangle': True
        },
        edit_options={'edit': True}
    )
    draw.add_to(base_map)

    # Add Geocoder search
    geocoder = Geocoder(collapsed=False, add_marker=True)
    geocoder.add_to(base_map)

    return base_map

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def meters_to_feet(meters):
    return meters * 3.28084

def feet_to_meters(feet):
    return feet / 3.28084

def mps_to_mph(mps):
    return mps * 2.23694

def mph_to_mps(mph):
    return mph / 2.23694

def main():
    st.markdown("""
        <style>
        body {
            animation: fadeInAnimation ease 1.5s;
            animation-iteration-count: 1;
            animation-fill-mode: forwards;
        }
        @keyframes fadeInAnimation {
            0% {
                opacity: 0;
                transform: translateY(10px);
            }
            100% {
                opacity: 1;
                transform: translateY(0);
            }
        }
        </style>
    """, unsafe_allow_html=True)

    # Header bar layout
    col_logo, col_title, col_docs = st.columns([1,6,1])

    with col_logo:
        st.image("generated-icon.png", width=60)

    with col_title:
        st.markdown("""
        <div class='header-animated'>
            <h2 style='margin-bottom: 0;'>OpenFlightPlan</h2>
            <p style='color: gray; margin-top: 0;'>Mobile-first mission planning</p>
        </div>
        """, unsafe_allow_html=True)

    with col_docs:
        st.markdown("[\ud83d\udcda Docs](https://docs.openflightplan.io)", unsafe_allow_html=True)

    st.title("\ud83d\ude81\ufe0f Flight Planner for Orthomosaic and 3D Model Creation")

    # Initialize session states
    if 'flight_paths' not in st.session_state:
        st.session_state.flight_paths = {'north_south': None, 'east_west': None}
    if 'area_bounds' not in st.session_state:
        st.session_state.area_bounds = None

    col1, col2 = st.columns([2, 1])

    with col1:
        try:
            map_instance = create_map()
            if map_instance:
                map_data = st_folium(map_instance, width=900, height=600)

                if st.button("\ud83d\uddd1\ufe0f Clear Drawn Area"):
                    st.session_state.area_bounds = None
                    st.experimental_rerun()

                if map_data and 'last_active_drawing' in map_data:
                    geometry = map_data['last_active_drawing']
                    if geometry and isinstance(geometry, dict) and 'geometry' in geometry:
                        logger.info(f"Received AOI geometry: {geometry}")
                        st.session_state.area_bounds = calculate_area_bounds(geometry['geometry'])

                        if st.session_state.area_bounds:
                            logger.info(f"Calculated area bounds: {st.session_state.area_bounds}")
                            st.success(
                                f"\u2705 AOI Captured - Center: ({st.session_state.area_bounds['center_lat']:.6f}, "
                                f"{st.session_state.area_bounds['center_lon']:.6f})\n"
                                f"Area: {st.session_state.area_bounds['width']:.1f}m × "
                                f"{st.session_state.area_bounds['height']:.1f}m"
                            )
                        else:
                            st.error("\u274c Could not calculate area bounds. Please try drawing the area again.")
                    else:
                        st.warning("Please draw an area of interest on the map.")
            else:
                st.error("Failed to create map. Please refresh the page and try again.")
        except Exception as e:
            logger.error(f"Error handling map: {str(e)}")
            st.error(f"Error handling map: {str(e)}. Please try refreshing the page.")

# Call main()
if __name__ == "__main__":
    main()
