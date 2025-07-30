# OpenFlightPlan

OpenFlightPlan is a **mobile-first** mission planning tool for creating flight grids for orthomosaics and 3D modeling. The app runs in the browser using Streamlit so you can plan missions directly from your phone.

## Features

- Draw polygons or circles to define your mission area
- Configure altitude, overlap, speed and other flight parameters
- Export flight plans as CSV and KMZ files
- No user accounts required
- Completely open source

## Local setup

```bash
git clone https://github.com/mostrager/mobile-flight-planner.git
cd mobile-flight-planner
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

For more details see the [documentation](https://docs.openflightplan.io/).

Licensed under the MIT License.
