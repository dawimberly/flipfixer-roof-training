"""Score a roof that was registered the way the photos have to be read.

The same corners are marked on the top photo and on the side photos first.
Only then does a facet exist: a plan ring from the top photo (the run), a
drain from the side photo that face is toward, and a pitch from the rise in
the profile photos over that run.

    python sop_score.py extracted/sop_five.json

Does not use a building footprint. Does not paste the report pitch.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

import roof_math as rm

EXTRACTED = Path(__file__).resolve().parent / "extracted"


def latlngs_from_feet(lat0: float, lng0: float, pts) -> list[list[float]]:
    m_lat, m_lng = rm.meters_per_degree(lat0)
    ring = []
    for east, north in pts:
        lat = lat0 + (float(north) / rm.FT_PER_M) / m_lat
        lng = lng0 + (float(east) / rm.FT_PER_M) / m_lng
        ring.append([lat, lng])
    return ring


def facets_from_record(record: dict) -> list[dict]:
    lat0, lng0 = record["origin"]
    facets = []
    for facet in record.get("facets") or []:
        if facet.get("latlngs"):
            latlngs = facet["latlngs"]
        else:
            latlngs = latlngs_from_feet(lat0, lng0, facet.get("feet") or [])
        item = {
            "pitch": facet.get("pitch"),
            "slope_deg": facet.get("slope_deg"),
            "latlngs": latlngs,
        }
        if facet.get("wall"):
            item["wall"] = True
        if facet.get("wall_edges"):
            item["wall_edges"] = list(facet["wall_edges"])
        facets.append(item)
    return facets


def ev_row(address: str) -> dict:
    frame = pd.read_csv(EXTRACTED / "eagleview_dataset.csv")
    hit = frame[frame["address"].str.lower() == address.lower()]
    if hit.empty:
        key = address.split(",")[0].lower()
        hit = frame[frame["address"].str.lower().str.startswith(key)]
    if hit.empty:
        raise SystemExit(f"No EagleView row for {address}")
    row = hit.iloc[0]
    return {
        "address": row["address"],
        "total_roof_area_sqft": None if pd.isna(row["total_roof_area_sqft"]) else float(row["total_roof_area_sqft"]),
        "total_squares": None if pd.isna(row["total_squares"]) else float(row["total_squares"]),
        "num_facets": None if pd.isna(row["num_facets"]) else float(row["num_facets"]),
        "total_ridges_ft": None if pd.isna(row["total_ridges_ft"]) else float(row["total_ridges_ft"]),
        "total_valleys_ft": None if pd.isna(row["total_valleys_ft"]) else float(row["total_valleys_ft"]),
        "total_rakes_ft": None if pd.isna(row["total_rakes_ft"]) else float(row["total_rakes_ft"]),
        "total_eaves_ft": None if pd.isna(row["total_eaves_ft"]) else float(row["total_eaves_ft"]),
        "predominant_pitch": None if pd.isna(row["predominant_pitch"]) else str(row["predominant_pitch"]),
    }


def score_record(record: dict) -> dict:
    # A simple gable needs the top (run) and one profile that holds the rise.
    # All five views are useful; they are not a gate for every roof.
    seen = set(record.get("views_registered") or [])
    has_top = "top" in seen
    has_profile = bool(seen & {"north", "south", "east", "west", "profile"})
    pitches = [f.get("pitch") for f in (record.get("facets") or [])]
    has_pitch = any(p for p in pitches)
    ready = has_top and (has_profile or has_pitch) and bool(record.get("facets"))
    missing = []
    if not has_top:
        missing.append("top")
    if not (has_profile or has_pitch):
        missing.append("profile")
    ev = ev_row(record["address"])
    facets = facets_from_record(record)
    if not ready:
        return {
            "address": ev["address"],
            "status": "not registered",
            "missing_views": missing,
            "ev_facets": ev["num_facets"],
        }
    summary = rm.summarize_facets(facets, waste_pct=0, gsd_scale=1.0)
    compare = rm.compare_to_eagleview(summary, ev)
    return {
        "address": ev["address"],
        "status": "registered",
        "missing_views": missing,
        "notes": record.get("notes") or "",
        "facets": summary.get("facet_count"),
        "ev_facets": ev["num_facets"],
        "ridge": summary.get("ridges_ft"),
        "hip": summary.get("hips_ft"),
        "ridge_hip": summary.get("ridges_hips_ft"),
        "ev_ridge_hip": ev["total_ridges_ft"],
        "ridge_hip_err": compare.get("ridges_hips_error_pct"),
        "valley": summary.get("valleys_ft"),
        "ev_valley": ev["total_valleys_ft"],
        "valley_err": compare.get("valleys_error_pct"),
        "rake": summary.get("rakes_ft"),
        "ev_rake": ev["total_rakes_ft"],
        "rake_err": compare.get("rakes_error_pct"),
        "eave": summary.get("eaves_ft"),
        "ev_eave": ev["total_eaves_ft"],
        "eave_err": compare.get("eaves_error_pct"),
        "step": summary.get("steps_ft"),
        "squares": summary.get("total_squares"),
        "ev_squares": ev["total_squares"],
        "squares_err": compare.get("squares_error_pct"),
        "shared_edges": summary.get("shared_edges"),
    }


def main() -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else EXTRACTED / "sop_five.json")
    records = json.loads(path.read_text(encoding="utf-8"))
    rows = [score_record(record) for record in records]
    frame = pd.DataFrame(rows)
    print(frame.to_string(index=False))
    out = EXTRACTED / "sop_five_score.csv"
    frame.to_csv(out, index=False)
    print(out)


if __name__ == "__main__":
    main()
