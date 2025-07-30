import os, time, uuid, hashlib, json
from datetime import datetime
from io import BytesIO
from pathlib import Path

import streamlit as st
import pandas as pd
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
from simplekml import Kml
import streamlit.components.v1 as components
from dotenv import load_dotenv

from drone_specs import DRONE_SPECS
from flight_calculator import (
    generate_grid_path,
    validate_parameters,
    estimate_flight_metrics,
    generate_oblique_path,
)
from contact_section import render_contact_form

load_dotenv()

st.set_page_config(page_title="openflightplan.io", layout="wide")
st.markdown("""
<style>
html, body {
    font-size: 150%;
}
body {
    font-family: 'Segoe UI', sans-serif;
    background-color: #0e1117;
    color: #f2f4f8;
}
.block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 1rem !important;
}
.stButton>button {
    background-color: #4c8bf5;
    color: white;
    border-radius: 8px;
    border: none;
    font-weight: 600;
}
.stButton>button:hover {
    background-color: #1a73e8;
}
h1, h2, h3, h4 {
    color: #f8f9fa;
}
.stDataFrame {
    border-radius: 8px;
    overflow: hidden;
}
.stMarkdown p {
    color: #d2d6dc;
}
#MainMenu {visibility: hidden;}
footer {visibility: visible; text-align: center; padding: 1rem 0; color: #8899a6; font-size: 0.9rem;}
footer a { color: #4c8bf5; text-decoration: none; margin-left: 5px; }
footer a:hover { text-decoration: underline; }
@media only screen and (max-width: 768px) {
  .block-container {padding-left:0.5rem;padding-right:0.5rem;}
  iframe {height:300px !important;}
}
section[data-testid="stSidebar"] {display:none;}
</style>
<footer>
Built by Michael · 👾 <a href="https://github.com/openflightplan" target="_blank">GitHub</a>
</footer>
""", unsafe_allow_html=True)

if "session_id" not in st.session_state:
    st.session_state.update({
        "session_id": str(uuid.uuid4()),
        "flight_path": [],
        "flight_ready": False,
        "param_hash": None,
        "map_center": None,
        "tour_step": 0,
        "ux_mode": None,
        "map_data": {},
        "user_loc_set": False,
        "user_marker": None,
    })

# Inject JS to fetch geolocation and call Streamlit callback
components.html("""
<script>
  window.addEventListener("message", (event) => {
    if (event.data.type === "USER_LOCATION") {
      const loc = event.data.coords;
      const streamlitEvent = new CustomEvent("streamlit:setComponentValue", {
        detail: { id: "userLocation", value: loc, type: "json" }
      });
      window.dispatchEvent(streamlitEvent);
    }
  });
  navigator.geolocation.getCurrentPosition(
    function (pos) {
      const coords = [pos.coords.latitude, pos.coords.longitude];
      window.parent.postMessage({type:'USER_LOCATION', coords: coords},'*');
    },
    function (err) {
      console.log("Geolocation error:", err);
    }
  );
</script>
""", height=0)

# Location input
loc = st.query_params.get("userLocation")
if loc:
    try:
        coords = json.loads(loc[0])
        st.session_state.map_center = coords
        st.session_state.user_marker = coords
    except:
        pass
if not st.session_state.map_center:
    st.session_state.map_center = [37.7749, -122.4194]  # fallback default


with st.expander("ℹ️ Learn how to configure your mission", expanded=False):
    st.markdown("""
    - **Altitude (AGL):** Controls image resolution and coverage area. Higher altitude = larger area, but less detail.
    - **Speed:** Affects battery usage and image blur.
    - **Overlap & Sidelap:** Ensure sufficient coverage for stitching.
    - **FOV:** Based on your drone's camera.
    - **Oblique:** Ideal for 3D modeling and vertical features.
    """)

planner_tab, contact_tab, about_tab, code_tab = st.tabs([
    "📍 Flight Planner",
    "📬 Contact Us",
    "👤 About the Creator",
    "📘 Codebase Overview"
])

with planner_tab:
    left, right = st.columns([1, 2], gap="large")
    with left:
        with st.expander("🛠️ Flight Settings", expanded=True):
            drone_model = st.selectbox("drone model", list(DRONE_SPECS.keys()))
            specs = DRONE_SPECS[drone_model]

            altitude = st.number_input("altitude (m AGL)", 5, 500, 50)
            speed = st.number_input("speed (m/s)", 1, 30, 5)
            interval = st.number_input("interval (s)", 1, 20, 2)

            overlap = st.slider("front overlap (%)", 0, 95, 75)
            sidelap = st.slider("side overlap (%)", 0, 95, 70)
            fov = st.slider("camera FOV (°)", 30, 120, 84)

            direction = st.radio("flight direction", ["north_south", "east_west"])
            rotation_deg = st.slider("rotation (°)", -90, 90, 0)

            mission_type = st.selectbox("📷 Mission type", ["Nadir", "Oblique", "Both"])
            if mission_type in ["Oblique", "Both"]:
                oblique_angle = st.slider("oblique tilt (°)", 5, 85, 45)
                oblique_layers = st.slider("# oblique layers", 1, 5, 2)
            else:
                oblique_angle, oblique_layers = 0, 0

    with right:
        st.subheader("📐 Define AOI")
        m = folium.Map(location=st.session_state.map_center, zoom_start=16)
        Draw(draw_options={"polygon": True, "rectangle": True, "circle": True, "marker": False}).add_to(m)
        if st.session_state.user_marker:
            folium.Marker(location=st.session_state.user_marker, tooltip="📍 You are here").add_to(m)

        map_output = st_folium(m, height=500, returned_objects=["last_active_drawing"])

        if st.button("🛫 Generate Flight Plan"):
            errors = validate_parameters({
                "altitude": altitude,
                "speed": speed,
                "interval": interval,
                "overlap": overlap,
                "sidelap": sidelap,
                "fov": fov,
            }, specs)
            if errors:
                for e in errors:
                    st.error(e)
                st.stop()

            if "last_active_drawing" not in map_output or not map_output["last_active_drawing"]:
                st.warning("Please draw a shape first.")
                st.stop()

            shape = map_output["last_active_drawing"]["geometry"]["coordinates"]
            coords = shape[0] if isinstance(shape[0], list) else [shape]
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]

            clat, clon = sum(lats) / len(lats), sum(lons) / len(lons)
            w = (max(lons) - min(lons)) * 111000
            h = (max(lats) - min(lats)) * 111000
            st.session_state.map_center = [clat, clon]

            path = []
            if mission_type in ["Nadir", "Both"]:
                path += generate_grid_path(w, h, overlap, sidelap, altitude, speed, interval, fov, clat, clon, direction, rotation_deg)
            if mission_type in ["Oblique", "Both"]:
                path += generate_oblique_path(clat, clon, w, h, altitude, oblique_angle, oblique_layers)

            st.session_state.flight_path = path
            st.session_state.flight_ready = bool(path)

    if st.session_state.flight_ready and st.session_state.flight_path:
        path = st.session_state.flight_path
        df = pd.DataFrame(path, columns=["longitude", "latitude"])

        st.success(f"✅ Generated {len(path)} waypoints")
        st.dataframe(df, use_container_width=True)

        dist_km, minutes, batteries = estimate_flight_metrics(path, speed, specs)
        st.info(f"🧭 Distance: {dist_km:.2f} km   ⏱ Duration: {minutes:.1f} min   🔋 Batteries: {batteries}")

        preview = folium.Map(location=st.session_state.map_center, zoom_start=16)
        folium.PolyLine([(lat, lon) for lon, lat in path], color="blue").add_to(preview)
        st.subheader("🛰️ Preview Flight Path")
        st.session_state.map_data = st_folium(preview, height=400)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_name = f"flight_plan_{ts}.csv"
        kmz_name = f"flight_path_{ts}.kmz"

        csv_buff = BytesIO()
        df.to_csv(csv_buff, index=False)
        csv_buff.seek(0)

        kml = Kml()
        for lon, lat in path:
            kml.newpoint(coords=[(lon, lat)])
        kmz_buff = BytesIO()
        kml.savekmz(kmz_buff)
        kmz_buff.seek(0)

        dl1, dl2 = st.columns(2)
        with dl1:
            st.download_button("⬇️ CSV", data=csv_buff, file_name=csv_name, mime="text/csv")
        with dl2:
            st.download_button("⬇️ KMZ", data=kmz_buff, file_name=kmz_name, mime="application/vnd.google-earth.kmz")

        os.makedirs("logs", exist_ok=True)
        with open("logs/exports.csv", "a") as logf:
            logf.write(f"{datetime.now()},{drone_model},{mission_type},{minutes:.1f},{dist_km:.2f},{batteries}\n")

with contact_tab:
    render_contact_form()

with code_tab:
    st.title("📝 Codebase Overview")
    code_md = Path("docs/codebase_overview.md").read_text(encoding="utf-8")
    st.markdown(code_md)

with about_tab:
    st.header("👨‍💻 About the Creator")
    st.markdown("""
    Hi, I'm **Michael**, the creator of OpenFlightPlan.

    I'm passionate about making mission planning intuitive, accurate, and accessible for pilots, researchers, and aerial mappers.

    - ✈️ Commercial UAV operator
    - 🧠 Background in geospatial analysis
    - 🌐 Created this tool to bridge usability + automation

    Feel free to reach out via the Contact tab or [GitHub](https://github.com/openflightplan)!
    """)
