import streamlit as st

st.set_page_config(page_title="Tutorials", layout="centered")

st.title("📘 Tutorials")
st.markdown("""
Welcome to the **OpenFlightPlan Tutorials** section!

Here you’ll find walk-throughs for how to:

- 🗺️ Draw mission areas using polygons and circles
- ✈️ Configure flight parameters for orthomosaic and 3D
- 🧾 Export .KMZ/.CSV flight plans
- 📱 Use the app from a mobile phone in the field
- 🛰️ Understand mission planning for photogrammetry

---

### 🧪 Example: Creating a Simple Grid Plan

1. Open the app from your phone
2. Tap “Draw Polygon”
3. Define your area
4. Set altitude and overlap
5. Click **Generate Flight Plan**

✅ You’ll see waypoints and time estimates before export.

---

We’ll keep adding step-by-step video and visual tutorials here soon!
""")
