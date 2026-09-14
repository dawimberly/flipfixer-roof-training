"""Numbers-only defaults from the EagleView set. Never averages carrier vs code tickets."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import roof_math as rm


def _series_mean(frame: pd.DataFrame, column: str) -> float | None:
    if column not in frame.columns or frame[column].dropna().empty:
        return None
    return float(pd.to_numeric(frame[column], errors="coerce").mean())


def _series_median(frame: pd.DataFrame, column: str) -> float | None:
    if column not in frame.columns or frame[column].dropna().empty:
        return None
    return float(pd.to_numeric(frame[column], errors="coerce").median())


def pitch_mix(frame: pd.DataFrame) -> dict[str, int]:
    if "predominant_pitch" not in frame.columns:
        return {}
    counts = (
        frame["predominant_pitch"]
        .dropna()
        .astype(str)
        .str.replace(r"\s+", "", regex=True)
        .value_counts()
        .to_dict()
    )
    return {str(key): int(value) for key, value in counts.items()}


def from_eagleview(frame: pd.DataFrame) -> dict:
    mix = pitch_mix(frame)
    predominant = max(mix, key=mix.get) if mix else None
    return {
        "n_eagleview_reports": int(len(frame)),
        "avg_squares": _round(_series_mean(frame, "total_squares"), 1),
        "avg_waste_pct": _round(_series_mean(frame, "waste_table_pct"), 1),
        "median_waste_pct": _round(_series_median(frame, "waste_table_pct"), 1),
        "avg_facets": _round(_series_mean(frame, "num_facets"), 1),
        "pitch_mix": mix,
        "predominant_pitch": predominant,
    }


def from_spread(frame: pd.DataFrame) -> dict:
    if frame is None or frame.empty:
        return {
            "properties": 0,
            "with_2plus_tickets": 0,
            "median_code_minus_carrier": None,
            "median_carrier_total": None,
            "median_code_total": None,
            "note": "never average tickets; no recommended mid",
        }
    both = frame[
        frame["carrier_total"].notna()
        & frame["code_total"].notna()
        & (frame["xm_count"] >= 2)
    ]
    return {
        "properties": int(len(frame)),
        "with_2plus_tickets": int((frame["xm_count"] >= 2).sum()),
        "median_code_minus_carrier": _round(_series_median(both, "delta"), 0),
        "median_carrier_total": _round(_series_median(both, "carrier_total"), 0),
        "median_code_total": _round(_series_median(both, "code_total"), 0),
        "note": "never average tickets; no recommended mid",
    }


def from_traces(traces: list[dict]) -> dict:
    fitted = rm.fit_gsd_scale(traces)
    wastes = []
    for trace in traces:
        waste = (trace.get("summary") or {}).get("waste_factor_pct")
        if waste is not None:
            wastes.append(float(waste))
    waste_pct = float(pd.Series(wastes).median()) if wastes else rm.DEFAULT_WASTE_PCT
    return {
        "gsd_scale": fitted.get("gsd_scale", 1.0),
        "trace_n": int(fitted.get("n") or 0),
        "median_abs_error_pct": fitted.get("median_abs_error_pct"),
        "waste_pct": round(waste_pct, 1),
    }


def build_payload(
    ev: pd.DataFrame | None,
    spread: pd.DataFrame | None,
    traces: list[dict] | None = None,
    projects: dict | None = None,
) -> dict:
    ev_frame = ev if ev is not None else pd.DataFrame()
    geometry = from_eagleview(ev_frame)
    tune = from_traces(traces or [])
    waste = geometry.get("median_waste_pct")
    if waste is None:
        waste = tune.get("waste_pct") or rm.DEFAULT_WASTE_PCT
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": "EagleView geometry trains /exterior defaults. Bid spread is carrier vs code, never a mid.",
        **geometry,
        "waste_pct": waste,
        "gsd_scale": tune.get("gsd_scale", 1.0),
        "trace_n": tune.get("trace_n", 0),
        "median_abs_error_pct": tune.get("median_abs_error_pct"),
        "spread": from_spread(spread if spread is not None else pd.DataFrame()),
        "projects": projects or {
            "n_projects": 0,
            "n_with_photos": 0,
            "n_photos": 0,
            "n_before_after": 0,
            "n_with_eagleview_and_ticket": 0,
            "note": "grouped by address or job name; photos stay on disk",
        },
    }
    return payload


def write_defaults(payload: dict, *paths: Path) -> None:
    body = json.dumps(payload, indent=2) + "\n"
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")


def _round(value: float | None, digits: int) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), digits)
