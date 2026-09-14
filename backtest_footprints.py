"""
Auto-trace EagleView roofs with OSM / Microsoft footprints + predominant pitch.

    python backtest_footprints.py

Writes extracted/footprint_backtest.csv (gitignored). Does not commit reports.
"""

from __future__ import annotations

import time

import pandas as pd

import roof_math as rm
from serve_tracer import EXTRACTED, geocode, guess_building, load_roofs, load_tune


def main() -> None:
    roofs = [row for row in load_roofs() if (row.get("total_squares") or 0) >= 8]
    tune = load_tune()
    scale = float(tune.get("gsd_scale") or 1.0)
    rows = []
    for i, roof in enumerate(roofs, start=1):
        address = roof["address"]
        print(f"[{i}/{len(roofs)}] {address}")
        loc = geocode(address)
        if not loc:
            rows.append(_row(roof, None, None, None, scale, "geocode failed"))
            continue
        ring, source = guess_building(loc["lat"], loc["lng"])
        if not ring:
            rows.append(_row(roof, loc, None, None, scale, "no footprint"))
            continue
        pitch = roof.get("predominant_pitch") or "6/12"
        trace = rm.summarize_facets(
            [{"pitch": pitch, "latlngs": ring}],
            waste_pct=rm.DEFAULT_WASTE_PCT,
            gsd_scale=scale,
        )
        compare = rm.compare_to_eagleview(
            trace,
            {
                "total_roof_area_sqft": roof.get("total_roof_area_sqft"),
                "total_squares": roof.get("total_squares"),
                "num_facets": roof.get("num_facets"),
            },
        )
        rows.append(
            _row(roof, loc, source, ring, scale, "ok", trace, compare)
        )
        time.sleep(0.15)

    frame = pd.DataFrame(rows)
    EXTRACTED.mkdir(parents=True, exist_ok=True)
    out = EXTRACTED / "footprint_backtest.csv"
    frame.to_csv(out, index=False)
    print(out)
    ok = frame[frame["status"] == "ok"].copy()
    print(f"Traced {len(ok)} / {len(frame)}")
    if ok.empty:
        return
    abs_sq = ok["squares_error_pct"].abs()
    print(f"Median |squares error|: {abs_sq.median():.2f}%")
    print(f"Mean |squares error|: {abs_sq.mean():.2f}%")
    for band in (1, 5, 8, 15):
        n = int((abs_sq <= band).sum())
        print(f"Within {band}%: {n}/{len(ok)} ({100 * n / len(ok):.0f}%)")
    print(ok.sort_values("squares_error_pct", key=lambda s: s.abs())[
        ["address", "source", "ev_squares", "traced_squares", "squares_error_pct"]
    ].to_string(index=False))


def _row(roof, loc, source, ring, scale, status, trace=None, compare=None) -> dict:
    return {
        "id": roof["id"],
        "address": roof["address"],
        "ev_squares": roof.get("total_squares"),
        "ev_area_sqft": roof.get("total_roof_area_sqft"),
        "ev_pitch": roof.get("predominant_pitch"),
        "ev_facets": roof.get("num_facets"),
        "lat": None if not loc else loc.get("lat"),
        "lng": None if not loc else loc.get("lng"),
        "source": source,
        "ring_pts": None if not ring else len(ring),
        "gsd_scale": scale,
        "traced_squares": None if not trace else trace.get("total_squares"),
        "traced_area_sqft": None if not trace else trace.get("total_area_with_pitch_multiplier_sqft"),
        "squares_error_pct": None if not compare else compare.get("squares_error_pct"),
        "area_error_pct": None if not compare else compare.get("area_error_pct"),
        "facet_count_delta": None if not compare else compare.get("facet_count_delta"),
        "status": status,
    }


if __name__ == "__main__":
    main()
