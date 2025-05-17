import streamlit as st
import pandas as pd
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
from datetime import datetime
from drone_specs import DRONE_SPECS
from flight_calculator import (
    generate_grid_path,
    validate_parameters,
    estimate_flight_metrics,
    generate_oblique_path
)
from dji_export import create_export_zip
import streamlit.components.v1 as components
import time, os
import hashlib, uuid
import json

st.set_page_config(page_title="openflightplan.io", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@media only screen and (max-width: 768px) {
  .block-container { padding-left: 0.5rem; padding-right: 0.5rem; }
  iframe { height: 300px !important; }
}
/* Hide sidebar toggle and sidebar */
section[data-testid="stSidebar"] { display: none !important; }
button[kind="icon"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.flight_path = []
    st.session_state.flight_ready = False
    st.session_state.param_hash = None
    st.session_state.map_center = [0, 0]
    st.session_state.tour_step = 0

# Display welcome banner and Docs
st.markdown("## ✈️ Welcome to openflightplan.io")
col1 = st.container()
with col1:
    st.markdown("""
<div style='text-align: center; margin-top: 1.5rem; margin-bottom: 1.5rem;'>
  <a href='https://docs.openflightplan.io' target='_blank'><button style='padding: 0.5rem 1rem;'>📄 Docs</button></a>
  <a href='https://github.com/mostrager/openflightplan' target='_blank'><button style='padding: 0.5rem 1rem;'>🔗 GitHub</button></a>
  <a href='mailto:support@openflightplan.io'><button style='padding: 0.5rem 1rem;'>💬 Support</button></a>
</div>
""", unsafe_allow_html=True)

# Handle browser geolocation messages
geo_data = st.query_params.get("geo")
if geo_data:
    try:
        coords = json.loads(geo_data[0])
        if coords and st.session_state.map_center == [0, 0]:
            st.session_state.map_center = coords
    except Exception:
        pass

components.html("""
<script>
navigator.geolocation.getCurrentPosition(
  function (pos) {
    const coords = [pos.coords.latitude, pos.coords.longitude];
    const query = new URLSearchParams(window.location.search);
    query.set('geo', JSON.stringify(coords));
    window.location.search = query.toString();
  },
  function (_) {
    console.log("Geolocation denied");
  });
</script>
""", height=0)

TOUR_DISMISS = ".tour-dismissed"
if os.path.exists(TOUR_DISMISS):
    st.session_state.tour_step = 1
if st.session_state.tour_step == 0:
    with st.expander("❓ Quick guide (tap to expand)", expanded=True):
        st.markdown("1. **Select drone + settings**")
        st.markdown("2. **Draw AOI** on the map")
        st.markdown("3. Tap 🛫 **Generate Flight Plan**")
        st.markdown("4. Tap ✅ **Export** to download plan")
        if st.button("✅ Got it! Hide this"):
            with open(TOUR_DISMISS, "w") as f:
                f.write("1")
            st.session_state.tour_step = 1

os.makedirs("logs", exist_ok=True)
os.makedirs("exports", exist_ok=True)
if not os.path.exists("logs/exports.csv"):
    with open("logs/exports.csv", "w") as f:
        f.write("timestamp,drone,mission_type,flight_minutes,flight_km,batteries\n")




left, right = st.columns([1, 2])

with left:
    with st.expander("🛠️ Flight Settings", expanded=True):
        drone_model = st.selectbox("drone model", list(DRONE_SPECS.keys()), help="Used for endurance & battery calc")
        specs = DRONE_SPECS[drone_model]
        altitude = st.number_input("altitude (m)", 5, 500, 50, help="AGL height")
        speed = st.number_input("speed (m/s)", 1, 30, 5, help="Cruise speed")
        interval = st.number_input("interval (s)", 1, 20, 2, help="Capture interval")
        overlap = st.slider("front overlap (%)", 0, 95, 75, help="Image forward overlap")
        sidelap = st.slider("side overlap (%)", 0, 95, 70, help="Image lateral overlap")
        fov = st.slider("camera field of view (°)", 30, 120, 84, help="Camera FOV in degrees")
        direction = st.radio("flight direction", ["north_south", "east_west"])
        rotation_deg = st.slider("rotation (°)", -90, 90, 0)
        mission_type = st.selectbox("📷 Mission type", ["Nadir", "Oblique", "Both"])
        if mission_type in ["Oblique", "Both"]:
            oblique_angle = st.slider("oblique tilt (°)", 5, 85, 45)
            oblique_layers = st.slider("# oblique layers", 1, 5, 2)
        else:
            oblique_angle, oblique_layers = 0, 0

with right:
    st.subheader("📐 Define AOI")
    m = folium.Map(location=st.session_state.map_center or [0, 0], zoom_start=3)
    Draw(draw_options={"polygon": True, "rectangle": True, "circle": True, "marker": False}).add_to(m)
    map_output = st_folium(m, height=400)

    if st.button("🛫 Generate Flight Plan"):
        errors = validate_parameters(dict(
            altitude=altitude, speed=speed, interval=interval, overlap=overlap,
            sidelap=sidelap, fov=fov, direction=direction, rotation_deg=rotation_deg,
            oblique_angle=oblique_angle, oblique_layers=oblique_layers, mission_type=mission_type
        ), specs)
        if errors:
            for e in errors:
                st.error(e)
            st.stop()
        path = []
        if "last_active_drawing" in map_output:
            shape = map_output["last_active_drawing"]["geometry"]["coordinates"]
            coords = shape[0] if isinstance(shape[0], list) else [shape]
            lons = [c[0] for c in coords]
            lats = [c[1] for c in coords]
            clat, clon = sum(lats)/len(lats), sum(lons)/len(lons)
            w = (max(lons) - min(lons)) * 111000
            h = (max(lats) - min(lats)) * 111000
            st.session_state.map_center = [clat, clon]
        else:
            st.warning("Please draw a shape.")
            st.stop()
        if mission_type in ["Nadir", "Both"]:
            path += generate_grid_path(w, h, overlap, sidelap, altitude, speed, interval, fov,
                                       clat, clon, direction, rotation_deg)
        if mission_type in ["Oblique", "Both"]:
            path += generate_oblique_path(clat, clon, w, h, altitude, oblique_angle, oblique_layers)
        st.session_state.flight_path = path
        st.session_state.flight_ready = True

if st.session_state.flight_ready and st.session_state.flight_path:
    path = st.session_state.flight_path
    df = pd.DataFrame(path, columns=["longitude", "latitude"])
    st.success(f"✅ Generated {len(path)} waypoints")
    st.dataframe(df, use_container_width=True)

    dist_km, minutes, batteries = estimate_flight_metrics(path, speed, specs)
    st.info(f"🧭 Distance: {dist_km:.2f} km")
    st.info(f"⏱ Duration: {minutes:.1f} min")
    st.info(f"🔋 Batteries needed: {batteries}")

    preview = folium.Map(location=st.session_state.map_center, zoom_start=16)
    folium.PolyLine([(lat, lon) for lon, lat in path], color="blue").add_to(preview)
    st.subheader("🛰️ Preview Flight Path")
    st.session_state.map_data = st_folium(preview, height=400)

    export_format = st.radio("Export format", ["CSV", "KMZ", "Both"])
    if st.button("✅ Confirm & Export"):
        zip_path = create_export_zip(path, dict(
            altitude=altitude, speed=speed, interval=interval, overlap=overlap,
            sidelap=sidelap, fov=fov, direction=direction, rotation_deg=rotation_deg,
            oblique_angle=oblique_angle, oblique_layers=oblique_layers, mission_type=mission_type
        ), df, export_format)

        with open(zip_path, "rb") as f:
            st.download_button("📦 Download flight plan (.zip)", data=f.read(),
                               file_name=os.path.basename(zip_path), mime="application/zip")

        with open("logs/exports.csv", "a") as logf:
            logf.write(f"{datetime.now()},{drone_model},{mission_type},{minutes:.1f},{dist_km:.2f},{batteries}\n")

        now = time.time()
        for f in os.listdir("exports"):
            full_path = os.path.join("exports", f)
            if os.path.isfile(full_path) and now - os.path.getmtime(full_path) > 86400:
                os.remove(full_path)
