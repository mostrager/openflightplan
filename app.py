# app.py
import streamlit as st
st.set_page_config(page_title="OpenFlightPlan", page_icon="🛩️", layout="wide")
st.markdown(
    """
    <style>
    /* Hide Streamlit's hamburger & footer */
    #MainMenu, footer {visibility: hidden;}
    /* Disable sidebar completely */
    section[data-testid="stSidebar"] {display: none;}
    </style>
    """,
    unsafe_allow_html=True,
)

from io import BytesIO
from datetime import datetime
from simplekml import Kml
import pandas as pd

from drone_specs import DRONE_SPECS
from flight_calculator import (
    validate_parameters,
    generate_grid_path,
    generate_oblique_path,
    estimate_flight_metrics,
)

# ────────────────────────────────────────────────────────────────────────────────
# UI – input form
# ────────────────────────────────────────────────────────────────────────────────
st.title("OpenFlightPlan Exporter")

with st.form("flight_params", clear_on_submit=False):
    cols = st.columns(3)
    with cols[0]:
        drone_choice = st.selectbox("Drone model", list(DRONE_SPECS.keys()))
    with cols[1]:
        mission_type = st.radio("Mission type", ["Grid", "Oblique"])
    with cols[2]:
        fov = st.number_input("Camera FOV (m)", value=25.0, min_value=1.0)

    center_lat = st.number_input("Center latitude", value=30.0000, format="%.6f")
    center_lon = st.number_input("Center longitude", value=-90.0000, format="%.6f")

    area_width  = st.number_input("Area width (m)",  value=200.0, min_value=5.0)
    area_height = st.number_input("Area height (m)", value=200.0, min_value=5.0)

    overlap = st.slider("Front‑lap (%)", 50, 90, 80)
    sidelap = st.slider("Side‑lap (%)",  50, 90, 70)

    altitude = st.number_input("Altitude (m AGL)", value=80.0, min_value=5.0)
    speed    = st.number_input("Speed (m/s)",       value=10.0, min_value=1.0)

    submitted = st.form_submit_button("Generate flight plan")

if not submitted:
    st.stop()

# ────────────────────────────────────────────────────────────────────────────────
# Validation & path generation
# ────────────────────────────────────────────────────────────────────────────────
drone_specs = DRONE_SPECS[drone_choice]
param_errors = validate_parameters({"altitude": altitude, "speed": speed}, drone_specs)

if param_errors:
    st.error(" 🛑  ".join(param_errors))
    st.stop()

if mission_type == "Grid":
    path = generate_grid_path(
        center_lat, center_lon,
        area_width, area_height,
        overlap, sidelap,
        fov
    )
else:
    path = generate_oblique_path(
        center_lat, center_lon,
        area_width, area_height,
        altitude
    )

# Convert to DataFrame for preview / CSV
df = pd.DataFrame(
    {
        "Latitude":  [lat for _, lat in path],
        "Longitude": [lon for lon, _ in path],
        "Altitude (m)": altitude,
    }
)

dist_km, minutes, batteries = estimate_flight_metrics(path, speed, drone_specs)

with st.expander("Flight‑plan summary", expanded=True):
    st.write(
        f"**Distance:** {dist_km:.2f} km   "
        f"**Flight‑time:** {minutes:.1f} min   "
        f"**Batteries needed:** {batteries}"
    )
    st.dataframe(df, use_container_width=True)

# ────────────────────────────────────────────────────────────────────────────────
# Build in‑memory CSV & KMZ
# ────────────────────────────────────────────────────────────────────────────────
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_name = f"flight_plan_{timestamp}.csv"
kmz_name = f"flight_path_{timestamp}.kmz"

csv_buffer = BytesIO()
df.to_csv(csv_buffer, index=False)
csv_buffer.seek(0)

kml = Kml()
for lon, lat in path:
    kml.newpoint(coords=[(lon, lat)])
kmz_buffer = BytesIO()
kml.savekmz(kmz_buffer)
kmz_buffer.seek(0)

# ────────────────────────────────────────────────────────────────────────────────
# Download buttons
# ────────────────────────────────────────────────────────────────────────────────
st.markdown("### Downloads")
left, right = st.columns(2)

with left:
    st.download_button(
        "⬇️ CSV",
        data=csv_buffer,
        file_name=csv_name,
        mime="text/csv",
    )

with right:
    st.download_button(
        "⬇️ KMZ",
        data=kmz_buffer,
        file_name=kmz_name,
        mime="application/vnd.google-earth.kmz",
    )

st.info(
    "🔍 **Mobile tip** – open the KMZ in **Google Earth Mobile** or **Litchi** "
    "(Android) / **Google Earth** or **ArcGIS Earth** (iOS) for quick previews."
)
