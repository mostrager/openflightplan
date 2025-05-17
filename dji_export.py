# dji_export.py
import os
import zipfile
import pandas as pd
from datetime import datetime

from simplekml import Kml

def create_export_zip(path, params, df, export_format="Both"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_name = f"flight_plan_{timestamp}"
    export_dir = os.path.join("exports", export_name)
    os.makedirs(export_dir, exist_ok=True)

    if export_format in ["CSV", "Both"]:
        csv_path = os.path.join(export_dir, "flight_plan.csv")
        df.to_csv(csv_path, index=False)

    if export_format in ["KMZ", "Both"]:
        kml = Kml()
        for lon, lat in path:
            kml.newpoint(coords=[(lon, lat)])
        kml_path = os.path.join(export_dir, "flight_path.kmz")
        kml.savekmz(kml_path)

    zip_path = f"{export_dir}.zip"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for root, _, files in os.walk(export_dir):
            for file in files:
                full_path = os.path.join(root, file)
                zipf.write(full_path, arcname=os.path.relpath(full_path, export_dir))

    return zip_path
