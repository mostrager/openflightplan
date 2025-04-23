import streamlit as st

st.set_page_config(page_title="Documentation", layout="wide")

st.title("📚 OpenFlightPlan Docs")

st.markdown("""
This section includes **technical documentation** on how OpenFlightPlan works, so developers and advanced users can understand or extend the system.

---

### 🧩 App Structure

- **Frontend**: Streamlit-based, optimized for mobile use
- **Backend**: Coming soon (Flask/DB for saving flight plans)
- **File Support**:
  - Export `.KMZ` and `.CSV` files
  - Future support for `.LAS`, `.OBJ`, `.TIF`

---

### 📦 Core Modules

- `flight_calculator.py`: Calculates waypoints and flight time
- `map_utils.py`: Handles drawing, basemaps, and geometry
- `drone_specs.py`: Houses default drone specs
- `utils.py`: Helper functions

---

### 📡 Integration Plans

- ✅ Mobile-first UI
- ✅ Nginx + HTTPS on Linode
- 🔜 Database + Auth
- 🔜 API for uploading post-processed data
""")
