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
    st.markdown("""
    <style>
    /* Fade-in Animation */
    body {
        animation: fadeInAnimation ease 1.5s;
        animation-iteration-count: 1;
        animation-fill-mode: forwards;
        background-color: #f9fbfd;
    }
    @keyframes fadeInAnimation {
        0% { opacity: 0; transform: translateY(10px); }
        100% { opacity: 1; transform: translateY(0); }
    }

    /* General Button Styling */
    .stButton>button {
        background-color: #3B5BDB; /* Ultramarine Blue */
        color: white;
        border: none;
        padding: 0.5em 1em;
        border-radius: 8px;
        transition: background-color 0.3s ease;
        margin-top: 10px;
    }
    .stButton>button:hover {
        background-color: #1c3faa;
        color: #ffffff;
    }

    /* Title and Header Customization */
    .stTitle {
        color: #1c3faa;
    }
    h2 {
        color: #1c3faa;
    }

    /* Subheader customization */
    .stSubheader {
        color: #444444;
    }

    /* Adjust sidebar and background */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

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

    st.title("\ud83d\udea9 Flight Planner for Orthomosaic and 3D Model Creation")

    if 'flight_paths' not in st.session_state:
        st.session_state.flight_paths = {'north_south': None, 'east_west': None}
    if 'area_bounds' not in st.session_state:
        st.session_state.area_bounds = None

    col1, col2 = st.columns([2,1])

    with col1:
        with st.spinner('Loading Map...'):
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
                                st.success(f"\u2705 AOI Captured - Center: ({st.session_state.area_bounds['center_lat']:.6f}, {st.session_state.area_bounds['center_lon']:.6f})")
                            else:
                                st.error("\u274c Could not calculate area bounds. Please try again.")
                        else:
                            st.warning("Draw an area of interest on the map.")
                else:
                    st.error("Failed to create map. Please refresh the page.")
            except Exception as e:
                logger.error(f"Error handling map: {str(e)}")
                st.error(f"Error: {str(e)}")

    with col2:
        st.subheader("\u2699\ufe0f Flight Parameters")
        altitude_unit = st.selectbox("Altitude Unit", ["meters", "feet"], key="altitude_unit")
        altitude = st.number_input("Altitude", min_value=1, value=50) if altitude_unit == "meters" else feet_to_meters(
            st.number_input("Altitude (ft)", min_value=3, value=164))

        speed_unit = st.selectbox("Speed Unit", ["m/s", "mph"], key="speed_unit")
        speed = st.number_input("Speed", min_value=1, value=5) if speed_unit == "m/s" else mph_to_mps(
            st.number_input("Speed (mph)", min_value=2, value=11))

        overlap = st.slider("Front Overlap (%)", min_value=0.0, max_value=1.0, value=0.8)
        sidelap = st.slider("Side Overlap (%)", min_value=0.0, max_value=1.0, value=0.7)
        interval = st.number_input("Camera Interval (s)", min_value=1, value=2)
        fov = st.number_input("Camera Field of View (\u00b0)", min_value=10, value=85)

        waypoint_action = st.selectbox(
            "Waypoint Action", ["Take Picture", "Start Recording", "Stop Recording"], help="Action at each waypoint"
        )

        direction = st.radio(
            "Flight Path Direction", ('north_south', 'east_west'), format_func=lambda x: "North-South" if x == 'north_south' else "East-West"
        )

        if st.button(f"Generate {direction.replace('_', '-')} Flight Plan"):
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
                    logger.info(f"Generated {direction} flight path")
                    st.success(f"\u2705 {direction.replace('_', '-')} flight plan generated!")
                except Exception as e:
                    logger.error(f"Error: {str(e)}")
                    st.error(f"Error: {str(e)}")
            else:
                st.warning("Please draw an AOI first!")

    if any(path is not None for path in st.session_state.flight_paths.values()):
        st.subheader("\ud83e\uddfd Generated Flight Plans")
        try:
            flight_map = folium.Map(
                location=[
                    st.session_state.area_bounds['center_lat'],
                    st.session_state.area_bounds['center_lon']
                ],
                zoom_start=15,
                tiles="CartoDB positron"
            )

            colors = {'north_south': 'blue', 'east_west': 'red'}
            for direction, path in st.session_state.flight_paths.items():
                if path:
                    points = [[coord[1], coord[0]] for coord in path]
                    folium.PolyLine(points, weight=2, color=colors[direction], opacity=0.8).add_to(flight_map)

            st_folium(flight_map, width=900, height=600)

            for direction, path in st.session_state.flight_paths.items():
                if path:
                    df_flight_plan = pd.DataFrame(path, columns=["Longitude", "Latitude"])
                    st.download_button(
                        label=f"\ud83d\udcc5 Download {direction.replace('_', '-')} Flight Plan (CSV)",
                        data=df_flight_plan.to_csv(index=False),
                        file_name=f"flight_plan_{direction}.csv",
                        mime="text/csv"
                    )

                    params = {'altitude': altitude, 'speed': speed}
                    kmz_file = create_kml_file(path, params)
                    with open(kmz_file, 'rb') as f:
                        st.download_button(
                            label=f"\ud83d\udcc5 Download {direction.replace('_', '-')} Flight Plan (KMZ)",
                            data=f,
                            file_name=kmz_file,
                            mime="application/vnd.google-earth.kmz"
                        )
                    os.remove(kmz_file)
        except Exception as e:
            logger.error(f"Error displaying flight plan: {str(e)}")
            st.error(f"Error displaying flight plan: {str(e)}")

    st.markdown("""
    ---
    <div style='text-align: center'>
    Created by <a href='https://www.linkedin.com/in/michaelostrager' target='_blank'>Michael Ostrager</a>  
    © 2025 • <a href='https://openflightplan.io' target='_blank'>openflightplan.io</a>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
