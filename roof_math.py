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
