"""Camera rays for a Google Earth view the operator opened.

The URL is the camera. Read it after the view settles. The viewer rewrites
the requested look-at, and that rewrite is not the photo until the top-photo
corners project onto the same corners in the side photo. If they do not land,
there is no length yet.

A screenshot is not a downloaded tile. A corner marked on the top photo has a
plan position. The same corner marked on a side photo is a ray. Height is
where that ray meets the vertical line through the plan position. Pitch is
that rise over the run from the top photo.
"""

from __future__ import annotations

import math

import numpy as np


def camera_enu(heading_deg: float, tilt_deg: float, distance_m: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Camera position and axes in east, north, up, relative to the look-at point.

    Tilt 0 is straight down. Heading is the direction the camera looks.
    """
    h = math.radians(heading_deg)
    t = math.radians(tilt_deg)
    horiz = distance_m * math.cos(t)
    # camera sits behind the look-at, opposite the look direction
    cam = np.array([-math.sin(h) * horiz, -math.cos(h) * horiz, distance_m * math.sin(t)], dtype=float)
    forward = np.array([math.sin(h) * math.sin(t), math.cos(h) * math.sin(t), -math.cos(t)], dtype=float)
    right = np.array([math.cos(h), -math.sin(h), 0.0], dtype=float)
    up = np.cross(right, forward)
    return cam, forward, right, up


def ray(px: float, py: float, width: int, height: int, cam, forward, right, up, fov_deg: float = 35.0) -> tuple[np.ndarray, np.ndarray]:
    half = math.tan(math.radians(fov_deg / 2.0))
    nx = (px - width / 2.0) / (height / 2.0) * half
    ny = -(py - height / 2.0) / (height / 2.0) * half
    direction = forward + nx * right + ny * up
    direction = direction / np.linalg.norm(direction)
    return cam, direction


def height_at_plan(origin: np.ndarray, direction: np.ndarray, east_m: float, north_m: float) -> float | None:
    """Altitude of the ray where it is closest to the vertical line at east, north.

    Returns meters above the look-at altitude. None if the ray does not pass
    near that column.
    """
    # closest point between the ray and the vertical line (east, north, z)
    # ray: origin + t * direction, t > 0
    # vertical: (east, north, z)
    # minimize |(origin + t*d) - (east, north, z)| 
    dx = origin[0] - east_m
    dy = origin[1] - north_m
    # z is free on the vertical, so ignore z in the horizontal miss
    # horizontal miss of the ray at parameter t
    hx = dx + t_solve(origin, direction, east_m, north_m)
    return hx


def t_solve(origin: np.ndarray, direction: np.ndarray, east_m: float, north_m: float) -> float:
    # horizontal closest approach of the ray to (east, north)
    # d/dt |origin_h + t*dir_h - target|^2 = 0
    target = np.array([east_m, north_m])
    oh = origin[:2]
    dh = direction[:2]
    denom = float(np.dot(dh, dh))
    if denom < 1e-12:
        return 0.0
    return float(np.dot(target - oh, dh) / denom)


def parse_earth_url(url: str) -> dict:
    """The viewer rewrites the requested camera. Use the settled URL, not the request."""
    import re

    match = re.search(
        r"@(-?[\d.]+),(-?[\d.]+),(-?[\d.]+)a,(-?[\d.]+)d,(-?[\d.]+)y,(-?[\d.]+)h,(-?[\d.]+)t",
        url,
    )
    if not match:
        raise ValueError(f"not an Earth camera URL: {url}")
    lat, lng, alt, distance, fov, heading, tilt = (float(part) for part in match.groups())
    return {
        "lat": lat,
        "lng": lng,
        "alt_m": alt,
        "distance_m": distance,
        "fov_deg": fov,
        "heading_deg": heading,
        "tilt_deg": tilt,
    }


def enu_between(lat0: float, lng0: float, alt0: float, lat1: float, lng1: float, alt1: float) -> np.ndarray:
    import roof_math as rm

    m_lat, m_lng = rm.meters_per_degree(lat0)
    return np.array(
        [
            (lng1 - lng0) * m_lng,
            (lat1 - lat0) * m_lat,
            alt1 - alt0,
        ],
        dtype=float,
    )


def project_px(east_m: float, north_m: float, up_m: float, width: int, height: int, camera: dict, origin_shift: np.ndarray) -> tuple[float, float] | None:
    """Project a point in the top-photo origin onto a side photo.

    origin_shift is the side look-at in the top-photo ENU frame.
    """
    cam, forward, right, up = camera_enu(camera["heading_deg"], camera["tilt_deg"], camera["distance_m"])
    point = np.array([east_m, north_m, up_m], dtype=float) - origin_shift
    view = point - cam
    forward_m = float(np.dot(view, forward))
    if forward_m <= 0.2:
        return None
    half = math.tan(math.radians(camera["fov_deg"] / 2.0))
    nx = float(np.dot(view, right)) / forward_m
    ny = float(np.dot(view, up)) / forward_m
    return (
        width / 2.0 + nx / half * (height / 2.0),
        height / 2.0 - ny / half * (height / 2.0),
    )


def corner_height_m(px: float, py: float, east_m: float, north_m: float, width: int, height: int, heading_deg: float, tilt_deg: float, distance_m: float, fov_deg: float = 35.0) -> dict:
    cam, forward, right, up = camera_enu(heading_deg, tilt_deg, distance_m)
    origin, direction = ray(px, py, width, height, cam, forward, right, up, fov_deg)
    t = t_solve(origin, direction, east_m, north_m)
    point = origin + t * direction
    miss = math.hypot(point[0] - east_m, point[1] - north_m)
    return {
        "height_m": float(point[2]),
        "height_ft": float(point[2] * 3.28084),
        "miss_m": miss,
        "t": t,
    }
