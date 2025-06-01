# app.py
import os, time, uuid, hashlib
from datetime import datetime
from io import BytesIO

import streamlit as st
import pandas as pd
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium
from simplekml import Kml
import streamlit.components.v1 as components

from drone_specs import DRONE_SPECS
from flight_calculator import (
    generate_grid_path,
    validate_parameters,
    estimate_flight_metrics,
    generate_oblique_path,
)

# ──────────────────────────────  Page config & CSS  ─────────────────────────────
st.set_page_config(page_title="openflightplan.io", layout="wide")
st.markdown(
    """
    <style>
    #MainMenu, footer {visibility: hidden;}
    @media only screen and (max-width: 768px) {
      .block-container {padding-left:0.5rem;padding-right:0.5rem;}
      iframe {height:300px !important;}
    }
    section[data-testid="stSidebar"] {display:none;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────  Session state  ──────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.update(
        {
            "session_id": str(uuid.uuid4()),
            "flight_path": [],
            "flight_ready": False,
            "param_hash": None,
            "map_center": [0, 0],
            "tour_step": 0,
            "ux_mode": None,
            "map_data": {},
        }
    )

# ──────────────────────────────  Quick‑tour banner  ─────────────────────────────
TOUR_DISMISS = ".tour-dismissed"
if os.path.exists(TOUR_DISMISS):
    st.session_state.tour_step = 1
if st.session_state.tour_step == 0:
    with st.expander("❓ Quick guide (tap to expand)", expanded=True):
        st.markdown("1. **Select drone + settings**")
        st.markdown("2. **Draw AOI** on the map")
        st.markdown("3. Tap 🛫 **Generate Flight Plan**")
        st.markdown("4. Tap ✅ **Export** to download")
        if st.button("✅ Got it! Hide this"):
            with open(TOUR_DISMISS, "w"):
                pass
            st.session_state.tour_step = 1

# ──────────────────────────────  First‑run UX choice  ──────────────────────────
if st.session_state.ux_mode is None:
    st.markdown("### ✈️ Welcome to openflightplan.io")
# ──────────────────────────────  Get user location (optional)  ──────────────────
components.html(
    """
    <script>
    navigator.geolocation.getCurrentPosition(
      function (pos) {
        const coords=[pos.coords.latitude,pos.coords.longitude];
        window.parent.postMessage({type:'USER_LOCATION',coords:coords},'*');
      },
      function (_){
        window.parent.postMessage({type:'USER_LOCATION_DENIED'},'*');
      });
    </script>
    """,
    height=0,
)

# ──────────────────────────────  Layout – settings & map  ──────────────────────
left, right = st.columns([1, 2], gap="large")

# ---------------------------  Settings panel  ----------------------------------
with left:
    with st.expander("🛠️ Flight Settings", expanded=True):
        drone_model = st.selectbox(
            "drone model",
            list(DRONE_SPECS.keys()),
            help="Used for endurance & battery calc",
        )
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

# ---------------------------  AOI drawing map  ---------------------------------
with right:
    st.subheader("📐 Define AOI")
    m = folium.Map(location=st.session_state.map_center or [0, 0], zoom_start=3)
    Draw(
        draw_options={
            "polygon": True,
            "rectangle": True,
            "circle": True,
            "marker": False,
        }
    ).add_to(m)
    map_output = st_folium(m, height=400, returned_objects=["last_active_drawing"])

    # -----------------------  Generate button  ---------------------------------
    if st.button("🛫 Generate Flight Plan"):
        # -------------------  Validate parameters  -----------------------------
        errors = validate_parameters(
            {
                "altitude": altitude,
                "speed": speed,
                "interval": interval,
                "overlap": overlap,
                "sidelap": sidelap,
                "fov": fov,
            },
            specs,
        )
        if errors:
            for e in errors:
                st.error(e)
            st.stop()

        # -------------------  Extract AOI geometry  ---------------------------
        if "last_active_drawing" not in map_output or not map_output["last_active_drawing"]:
            st.warning("Please draw a shape first.")
            st.stop()

        shape = map_output["last_active_drawing"]["geometry"]["coordinates"]
        coords = shape[0] if isinstance(shape[0], list) else [shape]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]

        clat, clon = sum(lats) / len(lats), sum(lons) / len(lons)
        w = (max(lons) - min(lons)) * 111000  # width [m]
        h = (max(lats) - min(lats)) * 111000  # height [m]
        st.session_state.map_center = [clat, clon]

        # -------------------  Build flight path  ------------------------------
        path = []
        if mission_type in ["Nadir", "Both"]:
            path += generate_grid_path(
                w,
                h,
                overlap,
                sidelap,
                altitude,
                speed,
                interval,
                fov,
                clat,
                clon,
                direction,
                rotation_deg,
            )
        if mission_type in ["Oblique", "Both"]:
            path += generate_oblique_path(
                clat, clon, w, h, altitude, oblique_angle, oblique_layers
            )

        # Store result
        st.session_state.flight_path = path
        st.session_state.flight_ready = bool(path)

# ──────────────────────────────  If a plan is ready …  ──────────────────────────
if st.session_state.flight_ready and st.session_state.flight_path:
    path = st.session_state.flight_path
    df = pd.DataFrame(path, columns=["longitude", "latitude"])

    st.success(f"✅ Generated {len(path)} waypoints")
    st.dataframe(df, use_container_width=True)

    # Metrics
    dist_km, minutes, batteries = estimate_flight_metrics(path, speed, specs)
    st.info(f"🧭 **Distance:** {dist_km:.2f} km   ⏱ **Duration:** {minutes:.1f} min   🔋 **Batteries:** {batteries}")

    # Live preview map
    preview = folium.Map(location=st.session_state.map_center, zoom_start=16)
    folium.PolyLine([(lat, lon) for lon, lat in path], color="blue").add_to(preview)
    st.subheader("🛰️ Preview Flight Path")
    st.session_state["map_data"] = st_folium(preview, height=400)

    # ───────────────────  Build CSV & KMZ in memory  ────────────────────
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

    # ───────────────────  Download buttons  ────────────────────────────
    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        st.download_button("⬇️ CSV", data=csv_buff, file_name=csv_name, mime="text/csv")
    with dl_col2:
        st.download_button(
            "⬇️ KMZ",
            data=kmz_buff,
            file_name=kmz_name,
            mime="application/vnd.google-earth.kmz",
        )

    # ───────────────────  Optional export log  ─────────────────────────
    os.makedirs("logs", exist_ok=True)
    with open("logs/exports.csv", "a") as logf:
        logf.write(
            f"{datetime.now()},{drone_model},{mission_type},{minutes:.1f},{dist_km:.2f},{batteries}\n"
        )
