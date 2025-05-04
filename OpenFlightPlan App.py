import streamlit as st
import numpy as np
import pandas as pd
import folium
import os
import logging
import sys
import io
import simplekml
from streamlit_folium import st_folium
from folium.plugins import Draw, Geocoder

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from drone_specs import DRONE_SPECS
from flight_calculator import generate_grid_path, validate_parameters
from utils import create_flight_path_plot
from map_utils import calculate_area_bounds
from dji_export import create_kml_file

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

def create_map():
    base_map = folium.Map(
        location=[40.7128, -74.0060],
        zoom_start=12,
        control_scale=True,
        tiles="CartoDB positron"
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

    Geocoder(collapsed=False, add_marker=True).add_to(base_map)

    return base_map

def main():
    st.set_page_config(page_title="OpenFlightPlan", page_icon="🛩️", layout="wide")

    st.markdown("""
        <style>
        body {
            animation: fadeInAnimation ease 1s;
            animation-iteration-count: 1;
            animation-fill-mode: forwards;
        }
        @keyframes fadeInAnimation {
            0% { opacity: 0; transform: translateY(10px); }
            100% { opacity: 1; transform: translateY(0); }
        }
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 0 10px 0;
            border-bottom: 2px solid #5B2C6F;
        }
        .header-title {
            font-size: 2em;
            font-weight: bold;
            color: #5B2C6F;
        }
        .header-subtitle {
            color: #7D3C98;
            font-size: 1em;
        }
        .stButton>button {
            background-color: #5B2C6F;
            color: white;
            border-radius: 5px;
            border: none;
            padding: 0.5em 1em;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #7D3C98;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(
        """
        <div class="header">
            <div>
                <div class="header-title">🛩️ OpenFlightPlan</div>
                <div class="header-subtitle">Mobile-first mission planning</div>
            </div>
            <div>
                <a href="https://docs.openflightplan.io" target="_blank">
                    <button style="background-color:#5B2C6F;color:white;padding:8px 16px;border:none;border-radius:5px;">📚 Docs</button>
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True
    )

    if 'flight_paths' not in st.session_state:
        st.session_state.flight_paths = {'north_south': None, 'east_west': None}
    if 'area_bounds' not in st.session_state:
        st.session_state.area_bounds = None

    col1, col2 = st.columns([2, 1])

    with col1:
        with st.spinner('Loading map...'):
            try:
                map_instance = create_map()
                if map_instance:
                    map_data = st_folium(map_instance, width=900, height=600)

                    if st.button("🗑️ Clear Drawn Area"):
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
                                    f"✅ AOI Captured - Center: ({st.session_state.area_bounds['center_lat']:.6f}, "
                                    f"{st.session_state.area_bounds['center_lon']:.6f})\n"
                                    f"Area: {st.session_state.area_bounds['width']:.1f}m × "
                                    f"{st.session_state.area_bounds['height']:.1f}m"
                                )
                        else:
                            st.warning("Please draw an area of interest on the map.")
                else:
                    st.error("Failed to create map. Please refresh.")
            except Exception as e:
                logger.error(f"Error loading map: {str(e)}")
                st.error(f"Error loading map: {str(e)}")

    with col2:
        st.subheader("⚙️ Flight Parameters")

        altitude_unit = st.selectbox("Altitude Unit", ["meters", "feet"], key="altitude_unit")
        altitude = st.number_input("Altitude", min_value=1, value=50) if altitude_unit == "meters" else feet_to_meters(
            st.number_input("Altitude (ft)", min_value=3, value=164))

        speed_unit = st.selectbox("Speed Unit", ["m/s", "mph"], key="speed_unit")
        speed = st.number_input("Speed", min_value=1, value=5) if speed_unit == "m/s" else mph_to_mps(
            st.number_input("Speed (mph)", min_value=2, value=11))

        overlap = st.slider("Front Overlap (%)", 0.0, 1.0, 0.8)
        sidelap = st.slider("Side Overlap (%)", 0.0, 1.0, 0.7)
        interval = st.number_input("Camera Interval (s)", min_value=1, value=2)
        fov = st.number_input("Camera Field of View (°)", min_value=10, value=85)

        waypoint_action = st.selectbox(
            "Waypoint Action",
            ["Take Picture", "Start Recording", "Stop Recording"],
            help="Action performed at each waypoint"
        )

        direction = st.radio(
            "Flight Path Direction",
            ('north_south', 'east_west'),
            format_func=lambda x: "North-South" if x == 'north_south' else "East-West"
        )

        if st.button(f"🚀 Generate {direction.replace('_', '-')} Flight Plan"):
            if st.session_state.area_bounds:
                try:
                    path = generate_grid_path(
                        area_width=st.session_state.area_bounds['width'],
                        area_height=st.session_state.area_bounds['height'],
                        overlap=overlap,
                        sidelap=sidelap,
                        altitude=altitude,
                        speed=speed,
                        interval=interval,
                        fov=fov,
                        center_lat=st.session_state.area_bounds['center_lat'],
                        center_lon=st.session_state.area_bounds['center_lon'],
                        direction=direction
                    )
                    st.session_state.flight_paths[direction] = path
                    logger.info(f"Generated {direction} flight path with {len(path)} waypoints")
                    st.success(f"✅ {direction.replace('_', '-')} flight plan generated successfully!")
                except Exception as e:
                    logger.error(f"Error generating flight path: {str(e)}")
                    st.error(f"❌ Error generating flight plan: {str(e)}")
            else:
                st.warning("Please draw an Area of Interest first.")

    st.markdown("""
    ---
    <div style='text-align: center'>
    Created by <a href='https://www.linkedin.com/in/michaelostrager' target='_blank'>Michael Ostrager</a>  
    © 2025 • <a href='https://openflightplan.io' target='_blank'>openflightplan.io</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
