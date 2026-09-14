"""Pitch multipliers, shoelace area, waste. Stdlib only."""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

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

FT_PER_M = 3.28084
SQFT_PER_SQM = FT_PER_M ** 2
DEFAULT_WASTE_PCT = 12.0
DEFAULT_ZOOM = 20


def gsd_ft_per_pixel(lat_degrees: float, zoom: int, image_width_px: int = 640) -> float:
    meters_per_px = 156543.03392 * math.cos(math.radians(lat_degrees)) / (2 ** zoom)
    return meters_per_px * FT_PER_M


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


def pitch_rise_per_run(pitch: str | None) -> float:
    """Inches of rise per inch of run. 8/12 -> 8/12."""
    key = str(pitch or "").replace(" ", "")
    if "/" not in key:
        return 0.0
    rise, run = key.split("/", 1)
    try:
        run_n = float(run)
        if run_n == 0:
            return 0.0
        return float(rise) / run_n
    except ValueError:
        return 0.0


def apply_waste_factor(sqft: float, waste_pct: float = DEFAULT_WASTE_PCT) -> float:
    return round(sqft * (1 + waste_pct / 100), 1)


def pitch_multiplier(pitch: str | None) -> float:
    if not pitch:
        return 1.0
    key = str(pitch).replace(" ", "")
    return PITCH_MULTIPLIERS.get(key, 1.0)


def expected_flat_sqft(ev_area_sqft: float | None, pitch: str | None) -> float | None:
    if ev_area_sqft is None:
        return None
    return float(ev_area_sqft) / pitch_multiplier(pitch)


def meters_per_degree(lat_degrees: float) -> tuple[float, float]:
    lat = math.radians(lat_degrees)
    m_per_deg_lat = 111132.92 - 559.82 * math.cos(2 * lat) + 1.175 * math.cos(4 * lat)
    m_per_deg_lng = 111412.84 * math.cos(lat) - 93.5 * math.cos(3 * lat)
    return m_per_deg_lat, m_per_deg_lng


def _close_ring(latlngs: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if len(latlngs) < 2:
        return list(latlngs)
    if latlngs[0] == latlngs[-1]:
        return list(latlngs)
    return list(latlngs) + [latlngs[0]]


def geodesic_ring_area_sqft(latlngs: list[tuple[float, float]]) -> float:
    """Shoelace on local meters. Each point is (lat, lng)."""
    ring = _close_ring(latlngs)
    if len(ring) < 4:
        return 0.0
    lat0 = sum(pt[0] for pt in ring[:-1]) / (len(ring) - 1)
    m_lat, m_lng = meters_per_degree(lat0)
    area_m2 = 0.0
    for i in range(len(ring) - 1):
        lat1, lng1 = ring[i]
        lat2, lng2 = ring[i + 1]
        x1, y1 = lng1 * m_lng, lat1 * m_lat
        x2, y2 = lng2 * m_lng, lat2 * m_lat
        area_m2 += x1 * y2 - x2 * y1
    return abs(area_m2) / 2.0 * SQFT_PER_SQM


def geodesic_ring_perimeter_ft(latlngs: list[tuple[float, float]]) -> float:
    ring = _close_ring(latlngs)
    if len(ring) < 2:
        return 0.0
    lat0 = ring[0][0]
    m_lat, m_lng = meters_per_degree(lat0)
    total_m = 0.0
    for i in range(len(ring) - 1):
        lat1, lng1 = ring[i]
        lat2, lng2 = ring[i + 1]
        dx = (lng2 - lng1) * m_lng
        dy = (lat2 - lat1) * m_lat
        total_m += math.hypot(dx, dy)
    return total_m * FT_PER_M


def latlng_to_world_px(lat: float, lng: float, zoom: int) -> tuple[float, float]:
    scale = 256 * (2 ** zoom)
    x = (lng + 180.0) / 360.0 * scale
    siny = min(max(math.sin(math.radians(lat)), -0.9999), 0.9999)
    y = (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi)) * scale
    return x, y


def polygon_px_from_latlngs(
    latlngs: list[tuple[float, float]],
    zoom: int,
    origin: tuple[float, float] | None = None,
) -> list[tuple[float, float]]:
    pts = [latlng_to_world_px(lat, lng, zoom) for lat, lng in latlngs]
    if origin is None:
        min_x = min(p[0] for p in pts)
        min_y = min(p[1] for p in pts)
        origin = (min_x, min_y)
    ox, oy = origin
    return [(x - ox, y - oy) for x, y in pts]


def _ring_points(latlngs: list) -> list[tuple[float, float]]:
    pts = [(float(pt[0]), float(pt[1])) for pt in latlngs or []]
    if len(pts) >= 2 and pts[0] == pts[-1]:
        pts = pts[:-1]
    return pts


def _to_local_ft(latlngs: list[tuple[float, float]], lat0: float) -> list[tuple[float, float]]:
    m_lat, m_lng = meters_per_degree(lat0)
    return [
        (lng * m_lng * FT_PER_M, lat * m_lat * FT_PER_M)
        for lat, lng in latlngs
    ]


def _descent_en(slope_deg: float) -> tuple[float, float]:
    """Unit vector water runs, in (east, north). 0 is north, 90 is east."""
    rad = math.radians(float(slope_deg))
    return math.sin(rad), math.cos(rad)


def _snap_pt(pt: tuple[float, float], snap_ft: float) -> tuple[int, int]:
    return (round(pt[0] / snap_ft), round(pt[1] / snap_ft))


def classify_edges(facets: list[dict], gsd_scale: float = 1.0, snap_ft: float = 2.0) -> dict:
    """Name each side of the triangles and measure it once.

    A facet needs a plan ring, a pitch, and slope_deg (the compass bearing
    water drains, 0 north, 90 east). A ridge and an eave are level, so the
    length is the plan length. A rake, hip, or valley is the hypotenuse of
    that triangle: sqrt(plan^2 + rise^2). A hip is not plan times the pitch
    factor. Shared sides are counted once. Corners within snap_ft are the
    same point.
    """
    empty = {
        "classified": False,
        "eaves_ft": None,
        "rakes_ft": None,
        "ridges_ft": None,
        "hips_ft": None,
        "valleys_ft": None,
        "steps_ft": None,
        "ridges_hips_ft": None,
        "drip_ft": None,
        "shared_edges": 0,
        "edges": [],
    }
    prepared = []
    for facet in facets:
        pts = _ring_points(facet.get("latlngs"))
        if len(pts) < 3:
            continue
        prepared.append(facet)
    if not prepared:
        return empty
    if not any(facet.get("slope_deg") is not None for facet in prepared):
        return empty

    lats = [pt[0] for facet in prepared for pt in _ring_points(facet.get("latlngs"))]
    lat0 = sum(lats) / len(lats)
    groups: dict[tuple, dict] = {}

    for facet in prepared:
        pts = _ring_points(facet.get("latlngs"))
        local = [(x * gsd_scale, y * gsd_scale) for x, y in _to_local_ft(pts, lat0)]
        signed = 0.0
        for i, (x1, y1) in enumerate(local):
            x2, y2 = local[(i + 1) % len(local)]
            signed += x1 * y2 - x2 * y1
        ccw = signed > 0
        slope = facet.get("slope_deg")
        rise_per = pitch_rise_per_run(facet.get("pitch"))
        descent = None if slope is None else _descent_en(slope)
        upslope = None if descent is None else (-descent[0], -descent[1])
        origin = local[0]
        n = len(local)
        for i in range(n):
            p1 = local[i]
            p2 = local[(i + 1) % n]
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            plan = math.hypot(dx, dy)
            if plan < 0.05:
                continue
            key = tuple(sorted((_snap_pt(p1, snap_ft), _snap_pt(p2, snap_ft))))
            if key[0] == key[1]:
                continue
            rise = None
            drains = None
            if upslope is not None:
                h1 = rise_per * ((p1[0] - origin[0]) * upslope[0] + (p1[1] - origin[1]) * upslope[1])
                h2 = rise_per * ((p2[0] - origin[0]) * upslope[0] + (p2[1] - origin[1]) * upslope[1])
                rise = abs(h2 - h1)
                left = (-dy / plan, dx / plan)
                inward = left if ccw else (-left[0], -left[1])
                dot = descent[0] * inward[0] + descent[1] * inward[1]
                if abs(dot) < 0.30:
                    drains = "along"
                elif dot < 0:
                    drains = "toward"
                else:
                    drains = "away"
            slot = groups.setdefault(key, {"sides": [], "plans": [], "rises": [], "ends": {}})
            slot["sides"].append({"drains": drains, "rise": rise})
            slot["plans"].append(plan)
            if rise is not None:
                slot["rises"].append(rise)
            for snap, latlng in (
                (_snap_pt(p1, snap_ft), pts[i]),
                (_snap_pt(p2, snap_ft), pts[(i + 1) % n]),
            ):
                slot["ends"].setdefault(snap, []).append(latlng)

    edges = []
    for slot in groups.values():
        plan = sum(slot["plans"]) / len(slot["plans"])
        rises = slot["rises"]
        rise = sum(rises) / len(rises) if rises else 0.0
        level = rise <= max(0.4, 0.03 * plan)
        length = plan if level else math.hypot(plan, rise)
        drains = [side["drains"] for side in slot["sides"]]
        kind = "unclassified"
        if drains and all(item is not None for item in drains):
            if len(drains) == 1:
                if drains[0] == "away" and level:
                    kind = "ridge"
                elif drains[0] == "toward" and level:
                    kind = "eave"
                else:
                    kind = "rake"
            elif len(drains) == 2:
                pair = set(drains)
                if pair == {"toward"} or pair == {"toward", "along"}:
                    kind = "valley"
                elif pair == {"away"} and level:
                    kind = "ridge"
                elif pair == {"away"} or pair == {"away", "along"}:
                    kind = "hip"
                else:
                    kind = "step"
        ends = []
        for samples in slot["ends"].values():
            ends.append([
                round(sum(pt[0] for pt in samples) / len(samples), 7),
                round(sum(pt[1] for pt in samples) / len(samples), 7),
            ])
        edges.append({
            "kind": kind,
            "length_ft": round(length, 1),
            "plan_ft": round(plan, 1),
            "rise_ft": round(rise, 2),
            "level": level,
            "latlngs": ends[:2],
        })

    def total(kind: str) -> float:
        return round(sum(edge["length_ft"] for edge in edges if edge["kind"] == kind), 1)

    eaves = total("eave")
    rakes = total("rake")
    ridges = total("ridge")
    hips = total("hip")
    valleys = total("valley")
    named = any(edge["kind"] != "unclassified" for edge in edges)
    return {
        "classified": named,
        "eaves_ft": eaves,
        "rakes_ft": rakes,
        "ridges_ft": ridges,
        "hips_ft": hips,
        "valleys_ft": valleys,
        "steps_ft": total("step"),
        "ridges_hips_ft": round(ridges + hips, 1),
        "drip_ft": round(eaves + rakes, 1),
        "shared_edges": sum(1 for slot in groups.values() if len(slot["sides"]) >= 2),
        "edges": edges,
    }


def error_pct(traced: float | None, truth: float | None) -> float | None:
    if traced is None or truth is None or truth == 0:
        return None
    return 100.0 * (float(traced) - float(truth)) / float(truth)


def summarize_facets(
    facets: list[dict],
    waste_pct: float = DEFAULT_WASTE_PCT,
    gsd_scale: float = 1.0,
) -> dict:
    flat = 0.0
    sloped = 0.0
    perimeter = 0.0
    for facet in facets:
        latlngs = [(float(pt[0]), float(pt[1])) for pt in facet.get("latlngs") or []]
        if len(latlngs) < 3:
            continue
        facet_flat = geodesic_ring_area_sqft(latlngs) * (gsd_scale ** 2)
        pitch = facet.get("pitch") or "6/12"
        facet["flat_area_sqft"] = round(facet_flat, 1)
        facet["area_sqft"] = round(sloped_area_sqft(facet_flat, pitch), 1)
        facet["perimeter_ft"] = round(geodesic_ring_perimeter_ft(latlngs) * gsd_scale, 1)
        flat += facet_flat
        sloped += facet["area_sqft"]
        perimeter += facet["perimeter_ft"]
    edges = classify_edges(facets, gsd_scale=gsd_scale)
    drip = edges["drip_ft"]
    return {
        "facet_count": sum(1 for facet in facets if len(facet.get("latlngs") or []) >= 3),
        "total_flat_area_sqft": round(flat, 1),
        "total_area_with_pitch_multiplier_sqft": round(sloped, 1),
        "total_squares": round(sloped / 100.0, 2),
        "waste_factor_pct": waste_pct,
        "final_area_sqft_with_waste": apply_waste_factor(sloped, waste_pct),
        "perimeter_ft": drip if edges["classified"] else round(perimeter, 1),
        "gsd_scale": gsd_scale,
        "eaves_ft": edges["eaves_ft"],
        "rakes_ft": edges["rakes_ft"],
        "ridges_ft": edges["ridges_ft"],
        "hips_ft": edges["hips_ft"],
        "valleys_ft": edges["valleys_ft"],
        "steps_ft": edges["steps_ft"],
        "ridges_hips_ft": edges["ridges_hips_ft"],
        "drip_ft": drip,
        "shared_edges": edges["shared_edges"],
        "edges_classified": edges["classified"],
        "edges": [
            {"kind": edge["kind"], "length_ft": edge["length_ft"], "latlngs": edge["latlngs"]}
            for edge in edges["edges"]
            if edge.get("latlngs")
        ],
    }


def compare_to_eagleview(summary: dict, ev: dict) -> dict:
    ev_area = ev.get("total_roof_area_sqft")
    ev_squares = ev.get("total_squares")
    ev_facets = ev.get("num_facets")
    ev_outline = None
    eaves = ev.get("total_eaves_ft")
    rakes = ev.get("total_rakes_ft")
    if eaves is not None and rakes is not None:
        ev_outline = float(eaves) + float(rakes)
    return {
        "area_error_pct": error_pct(summary.get("total_area_with_pitch_multiplier_sqft"), ev_area),
        "squares_error_pct": error_pct(summary.get("total_squares"), ev_squares),
        "facet_count_delta": (
            None
            if ev_facets is None
            else summary.get("facet_count", 0) - float(ev_facets)
        ),
        "outline_error_pct": error_pct(
            summary.get("drip_ft") if summary.get("edges_classified") else summary.get("perimeter_ft"),
            ev_outline,
        ),
        "ridges_hips_error_pct": error_pct(summary.get("ridges_hips_ft"), ev.get("total_ridges_ft")),
        "valleys_error_pct": error_pct(summary.get("valleys_ft"), ev.get("total_valleys_ft")),
        "rakes_error_pct": error_pct(summary.get("rakes_ft"), ev.get("total_rakes_ft")),
        "eaves_error_pct": error_pct(summary.get("eaves_ft"), ev.get("total_eaves_ft")),
        "ev_area_sqft": ev_area,
        "ev_squares": ev_squares,
        "ev_facets": ev_facets,
        "ev_outline_ft": ev_outline,
        "ev_ridges_hips_ft": ev.get("total_ridges_ft"),
        "ev_valleys_ft": ev.get("total_valleys_ft"),
        "ev_rakes_ft": ev.get("total_rakes_ft"),
        "ev_eaves_ft": ev.get("total_eaves_ft"),
        "ev_pitch": ev.get("predominant_pitch"),
    }


def fit_gsd_scale(traces: list[dict]) -> dict:
    """Median scale that makes traced sloped area match EagleView area."""
    ratios = []
    for trace in traces:
        summary = trace.get("summary") or {}
        ev = trace.get("ev") or {}
        traced = summary.get("total_area_with_pitch_multiplier_sqft")
        truth = ev.get("total_roof_area_sqft")
        scale_used = float(summary.get("gsd_scale") or 1.0)
        if not traced or not truth or traced <= 0:
            continue
        unscaled = traced / (scale_used ** 2)
        if unscaled <= 0:
            continue
        ratios.append(math.sqrt(float(truth) / unscaled))
    if not ratios:
        return {"gsd_scale": 1.0, "n": 0, "median_abs_error_pct": None}
    scale = float(statistics.median(ratios))
    errors = []
    for trace in traces:
        summary = trace.get("summary") or {}
        ev = trace.get("ev") or {}
        traced = summary.get("total_area_with_pitch_multiplier_sqft")
        truth = ev.get("total_roof_area_sqft")
        scale_used = float(summary.get("gsd_scale") or 1.0)
        if not traced or not truth:
            continue
        unscaled = traced / (scale_used ** 2)
        fitted = unscaled * (scale ** 2)
        err = error_pct(fitted, truth)
        if err is not None:
            errors.append(abs(err))
    return {
        "gsd_scale": round(scale, 4),
        "n": len(ratios),
        "median_abs_error_pct": round(statistics.median(errors), 2) if errors else None,
    }


def write_tune(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
