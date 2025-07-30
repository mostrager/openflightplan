## Overview

OpenFlightPlan is a **free**, **mobile-first** mission planning tool for creating 2D orthomosaics and 3D modeling flight grids — right from your browser.

> ✅ No logins required  
> ✅ Mobile optimized  
> ✅ Export to CSV or KMZ  

---

## Codebase Summary

```text
app.py                   → main Streamlit interface  
flight_calculator.py     → grid/oblique path generation & metrics  
map_utils.py             → Folium mapping helpers with drawing tools  
drone_specs.py           → DJI drone-specific specs (speed, altitude, FOV)  
dji_export.py            → Optional ZIP export with CSV/KMZ files  
utils.py                 → Plotly-based flight‑path visualization support  
pages/                   → Streamlit subpages (tutorials, docs, about)  
docs/                    → MkDocs documentation sources  
site/                    → Published static documentation  
logs/exports.csv         → Export history record  

Key Features
1. 🎛 Interactive Flight Planner

Sidebar flight settings and Folium map drawing tools allow users to:

    Set drone model, altitude, speed, FOV

    Choose mission type: Nadir, Oblique, Both

    Draw AOI using polygon/rectangle/circle

    Click 🛫 Generate Flight Plan to calculate paths

if st.button("🛫 Generate Flight Plan"):
    ...
    path = []
    if mission_type in ["Nadir", "Both"]:
        path += generate_grid_path(...)
    if mission_type in ["Oblique", "Both"]:
        path += generate_oblique_path(...)
    st.session_state.flight_path = path

Downloads available as:

st.download_button("⬇️ CSV", data=csv_buff, file_name=csv_name)
st.download_button("⬇️ KMZ", data=kmz_buff, file_name=kmz_name)

2. 📐 Flight Calculations

    Checks parameters against drone limits:

if params['altitude'] > drone_specs.get("max_altitude", 120):
    errors.append("Altitude exceeds drone's max altitude.")

    Grid path spacing uses FOV, overlap, sidelap.

    Oblique paths are concentric loops around the center.

3. 🗺 Mapping Tools

In map_utils.py:

    Geolocation via ipinfo.io or Nominatim

    Basemap switcher (Google, Bing, Esri, etc.)

    Drawing plugins: rectangle, polygon, circle

4. 🚁 Drone Specs

Defined in drone_specs.py:

"DJI Mavic 3 Pro": {
    "max_speed": 21.0,
    "min_altitude": 2,
    "max_altitude": 120,
    "camera_fov": 82.0,
    "min_interval": 0.5
}

Learning & Next Steps

    Read docs/getting-started.md, docs/mobile.md, etc.

    Learn Streamlit session state and layout components

    Understand geospatial math (Haversine, FOV spacing)

    Improve DJI exports in dji_export.py

🛠 Setup Instructions

git clone https://github.com/mostrager/mobile-flight-planner.git
cd mobile-flight-planner
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py

Built for developers, pilots, and aerial surveyors 🌍✈️
