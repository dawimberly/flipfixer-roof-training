"""Pitch multipliers, shoelace area, waste. Stdlib only."""

import math

PITCH_MULTIPLIERS = {
    "0/12": 1.000,
    "1/12": 1.003,
    "2/12": 1.014,
    "3/12": 1.031,
    "4/12": 1.054,
    "5/12": 1.083,
    "6/12": 1.118,
    "7/12": 1.158,
    "8/12": 1.202,
    "9/12": 1.250,
    "10/12": 1.302,
    "11/12": 1.357,
    "12/12": 1.414,
}


def gsd_ft_per_pixel(lat_degrees: float, zoom: int, image_width_px: int = 640) -> float:
    meters_per_px = 156543.03392 * math.cos(math.radians(lat_degrees)) / (2 ** zoom)
    return meters_per_px * 3.28084


def polygon_area_px(polygon_px: list[tuple[float, float]]) -> float:
    if len(polygon_px) < 3:
        return 0.0
    area = 0.0
    n = len(polygon_px)
    for i in range(n):
        x1, y1 = polygon_px[i]
        x2, y2 = polygon_px[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


def flat_area_sqft(polygon_px: list[tuple[float, float]], gsd_ft_per_px: float) -> float:
    return polygon_area_px(polygon_px) * (gsd_ft_per_px ** 2)


def sloped_area_sqft(flat_sqft: float, pitch: str) -> float:
    return flat_sqft * PITCH_MULTIPLIERS.get(pitch, 1.0)


def apply_waste_factor(sqft: float, waste_pct: float = 12.0) -> float:
    return round(sqft * (1 + waste_pct / 100), 1)


def rectangle_perimeter_ft(area_sqft: float, aspect: float = 1.9) -> float:
    """Perimeter of a rectangle with this floor area. Ranch roofs are ~1.8–2.0:1."""
    if area_sqft <= 0 or aspect <= 0:
        return 0.0
    length = math.sqrt(area_sqft * aspect)
    width = area_sqft / length
    return 2.0 * (length + width)


def one_story_expected_squares(
    living_sqft: float,
    garage_sqft: float = 0.0,
    pitch: str = "4/12",
    overhang_ft: float = 1.5,
    waste_pct: float = 0.0,
    aspect: float = 1.9,
) -> float:
    """
    Ballpark squares for a simple 1-story house + attached garage.
    Footprint plus a drip-edge band, then pitch. Not a bid.
    """
    footprint = max(living_sqft, 0.0) + max(garage_sqft, 0.0)
    peri = rectangle_perimeter_ft(footprint, aspect)
    plan = footprint + peri * max(overhang_ft, 0.0)
    sloped = sloped_area_sqft(plan, pitch)
    if waste_pct:
        sloped = sloped * (1 + waste_pct / 100)
    return round(sloped / 100.0, 2)


def trace_sanity(
    measured_squares: float,
    living_sqft: float,
    garage_sqft: float = 0.0,
    stories: float = 1.0,
    pitch: str = "4/12",
) -> str:
    """
    Flag a trace that is way off the building footprint.

    Compares squares to (living/stories + garage). A 1-story ranch usually
    lands around 1.15–1.35× that footprint after overhangs and pitch.
    Returns "low", "ok", or "high".
    """
    if measured_squares <= 0 or living_sqft <= 0:
        return "ok"
    stories = stories if stories and stories > 0 else 1.0
    footprint = living_sqft / stories + max(garage_sqft, 0.0)
    if footprint <= 0:
        return "ok"
    ratio = measured_squares * 100.0 / footprint
    # Pitch still has to land near the footprint. 12/12 is only 1.41× plan.
    _ = pitch
    # Below ~footprint usually means the garage (or a wing) was dropped.
    if ratio < 0.90:
        return "low"
    # 1.55× still covers 6/12 + 2 ft overhang + 12% waste. 39 on a
    # 2,300 sq ft ranch is ~1.7× and should fail.
    if ratio > 1.55:
        return "high"
    return "ok"
