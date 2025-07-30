# ✈️ Flight Parameters

Understanding each setting helps you produce better imagery. OpenFlightPlan pulls defaults from `drone_specs.py` when you choose your drone model.

---

## Altitude

- Determines ground resolution and coverage area.
- Stay within your drone's limits (max 120 m for DJI models).
- Higher altitude = fewer images but lower detail.

## Speed

- How fast the drone travels along the path.
- Constrained by your drone's capability (up to 21 m/s for a Mavic 3 Pro).
- Slower speeds allow longer exposure times and better overlap.

## Front Overlap

- Percentage each image overlaps the previous one along the flight direction.
- Typical orthomosaics use **70%+**.

## Sidelap

- Overlap between adjacent flight lines.
- Aim for **60–70%** for mapping to avoid gaps.

## Interval

- Time between photo triggers.
- Minimum of **0.5 s** based on DJI specs.

## FOV

- Camera field of view in degrees (about **82°** on most DJI models).
- A wider FOV covers more ground but increases distortion near edges.

---

## Orthomosaic Tips

- Fly **nadir** (camera pointing straight down).
- Use higher overlap and sidelap for photogrammetry.
- Moderate altitude (60–100 m) balances detail and coverage.

## Oblique Mission Tips

- Tilt the camera and fly concentric circles for 3D models.
- Use several layers at different altitudes.
- Reduce speed to maintain blur‑free images.

