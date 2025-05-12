import streamlit as st
from drone_specs import DRONE_SPECS
from flight_calculator import generate_grid_path, validate_parameters
import pandas as pd
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
from io import StringIO
from datetime import datetime
from dji_export import create_kml_file

st.set_page_config(page_title="openflightplan.io", layout="wide")
st.title("openflightplan.io")

# --- sidebar inputs ---
st.sidebar.header("🛠️ flight settings")
drone_model = st.sidebar.selectbox("drone model", list(DRONE_SPECS.keys()))
drone_specs = DRONE_SPECS[drone_model]

altitude = st.sidebar.number_input("altitude (m)", min_value=1, value=50)
speed = st.sidebar.number_input("speed (m/s)", min_value=1, value=5)
interval = st.sidebar.number_input("capture interval (s)", min_value=1, value=2)
overlap = st.sidebar.slider("front overlap (%)", min_value=0, max_value=95, value=75)
sidelap = st.sidebar.slider("side overlap (%)", min_value=0, max_value=95, value=70)
fov = st.sidebar.slider("camera field of view (°)", min_value=30, max_value=120, value=84)
direction = st.sidebar.radio("flight direction", ["north_south", "east_west"])
rotation_deg = st.sidebar.slider("grid rotation (°)", min_value=-90, max_value=90, value=0)

# --- main map section ---
st.subheader("📐 define area of interest")
with st.expander("map & area selection", expanded=True):
    m = folium.Map(location=[37.7749, -122.4194], zoom_start=13)
    draw = Draw(
        draw_options={
            'polyline': False,
            'circle': False,
            'marker': False,
            'circlemarker': False
        },
        edit_options={"edit": False}
    )
    draw.add_to(m)
    st_data = st_folium(m, width=700, height=500)

# --- generate plan ---
st.subheader("🛫 generate flight plan")
if st.button("generate"):
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M")
    filename_base = f"{timestamp}_flightplan"
    center_lat, center_lon = 37.7749, -122.4194
    area_width = 300  # meters
    area_height = 200  # meters

    params = {
        'altitude': altitude,
        'speed': speed,
        'interval': interval,
        'overlap': overlap,
        'sidelap': sidelap
    }

    errors = validate_parameters(params, drone_specs)
    if errors:
        for e in errors:
            st.error(e)
    else:
        path = generate_grid_path(
            area_width=area_width,
            area_height=area_height,
            overlap=overlap,
            sidelap=sidelap,
            altitude=altitude,
            speed=speed,
            interval=interval,
            fov=fov,
            center_lat=center_lat,
            center_lon=center_lon,
            direction=direction,
            rotation_deg=rotation_deg
        )

        st.success(f"generated {len(path)} waypoints.")
        df = pd.DataFrame(path, columns=["longitude", "latitude"])
        st.dataframe(df)

        path_map = folium.Map(location=[center_lat, center_lon], zoom_start=16)
        latlon_path = [(lat, lon) for lon, lat in path]
        folium.PolyLine(locations=latlon_path, color="blue").add_to(path_map)
        folium.Marker(location=latlon_path[0], popup="start", icon=folium.Icon(color="green")).add_to(path_map)
        folium.Marker(location=latlon_path[-1], popup="end", icon=folium.Icon(color="red")).add_to(path_map)
        st_folium(path_map, width=700, height=500)

        # --- export options ---
        if path and df is not None:
            csv_data = df.to_csv(index=False)
            st.download_button("📥 csv", data=csv_data, file_name=f"{filename_base}.csv", mime="text/csv")

            kmz_file = create_kml_file(path, params)
            with open(kmz_file, "rb") as f:
                st.download_button("📥 kmz", data=f.read(), file_name=kmz_file, mime="application/vnd.google-earth.kmz")
