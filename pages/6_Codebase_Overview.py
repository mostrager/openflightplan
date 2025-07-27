import streamlit as st

st.set_page_config(page_title="Codebase Overview", layout="wide")

st.title("📝 Codebase Overview")

st.markdown("""
**Overview**

- The project delivers a free, mobile‑first mission planner for drone mapping. The docs introduce it succinctly:

```
OpenFlightPlan is a **free**, **mobile-first** mission planning tool designed for creating 2D orthomosaics and 3D modeling flight grids — right from your browser.
```

Key benefits include mobile optimization and CSV/KMZ downloads with no user accounts required.

- The codebase centers on a Streamlit app (`app.py`) that hosts the interactive UI. It imports modules for map drawing, flight-path generation, and exporting results:

```
import streamlit as st
...
from drone_specs import DRONE_SPECS
from flight_calculator import (
    generate_grid_path,
    validate_parameters,
    estimate_flight_metrics,
    generate_oblique_path,
)
```

- The documentation highlights the lightweight tech stack:

```
## 🧱 Tech Stack
- **Frontend**: Streamlit + Folium
- **Backend**: Python
- **Exports**: simplekml (KMZ) + pandas (CSV)
```

**Project Structure**

```
app.py                   -> main Streamlit interface
flight_calculator.py     -> grid/oblique path generation & metrics
map_utils.py             -> helper functions for Folium map creation
drone_specs.py           -> per-drone speed/altitude defaults
dji_export.py            -> optional export to ZIP with CSV/KMZ
utils.py                 -> Plotly flight-path plotting
pages/                   -> Streamlit subpages (tutorials, docs, about)
docs/                    -> MkDocs documentation
site/                    -> prebuilt static documentation
logs/exports.csv         -> history of export events
```

**Key Features**

1. **Interactive planning UI**
   `app.py` creates a sidebar of flight settings (altitude, speed, overlaps, etc.) and a Folium map for drawing the area of interest. When the user clicks “Generate Flight Plan,” parameters are validated and paths are generated. Preview and download options appear once a path is ready:

```
if st.button("🛫 Generate Flight Plan"):
    ...
    path = []
    if mission_type in ["Nadir", "Both"]:
        path += generate_grid_path(...)
    if mission_type in ["Oblique", "Both"]:
        path += generate_oblique_path(...)
    st.session_state.flight_path = path
    st.session_state.flight_ready = bool(path)
```

   The resulting waypoints are shown in a table, and CSV/KMZ downloads are offered:

```
st.download_button("⬇️ CSV", data=csv_buff, file_name=csv_name, mime="text/csv")
st.download_button("⬇️ KMZ", data=kmz_buff, file_name=kmz_name, mime="application/vnd.google-earth.kmz")
```

2. **Flight calculations**
   `flight_calculator.py` validates input against per‑drone specs, computes grid paths, can optionally generate circular oblique paths, and estimates flight distance and battery usage. The logic is straightforward:

```
def validate_parameters(params, drone_specs):
    errors = []
    if params['altitude'] > drone_specs.get("max_altitude", 120):
        errors.append("Altitude exceeds drone's max altitude.")
    if params['speed'] > drone_specs.get("max_speed", 15):
        errors.append("Speed exceeds drone's max speed.")
    return errors
```

3. **Mapping utilities**
   `map_utils.py` provides location search and basemap selection, then returns a Folium map with drawing tools enabled:

```
basemap_choice = st.selectbox("Select Basemap", list(basemap_options.keys()))
...
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
```

4. **Drone specifications**
   `drone_specs.py` defines maximum speed and altitude limits for supported DJI models. These are referenced when validating parameters:

```
DRONE_SPECS = {
    "DJI Mavic 3 Pro": {"max_speed": 21.0, "min_altitude": 2, "max_altitude": 120, "camera_fov": 82.0, "min_interval": 0.5},
    ...
}
```

**Learning and Next Steps**

- **Read the docs:** The site’s documentation includes tutorials, usage tips, and developer instructions. `docs/getting-started.md`, `docs/using-the-app.md`, and `docs/mobile.md` provide short overviews of drawing areas, adjusting parameters, and using the app on mobile devices.

- **Explore Streamlit:** Understanding Streamlit’s layout, session state, and component interactions will help you modify the user interface or add new features. The `st` elements in `app.py` demonstrate typical usage.

- **Dive into Folium and geospatial math:** `map_utils.py` and `flight_calculator.py` show how geographic coordinates are manipulated. Learning about geodesy and Folium’s drawing plugins will help you extend path-planning options or integrate with other mapping APIs.

- **Check `dji_export.py`** if you want to integrate with DJI formats or produce zipped exports. It already builds CSV and KMZ files; you could adapt it for additional formats or automated uploads.

- **Consider contributions:** The docs encourage contributions and outline a simple workflow:

```
git clone https://github.com/mostrager/mobile-flight-planner.git
cd mobile-flight-planner
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run OpenFlightPlan\ App.py
```

Overall, the repository is compact and approachable—good for experimenting with Streamlit, Folium, and simple geospatial calculations. Start by running `app.py` and exploring how the pieces interact, then build on the modules as needed.
""")
