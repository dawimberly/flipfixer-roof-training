"""
Join EagleView rows to every Xactimate on the same roof.

One EV address can have several XM tickets. That is normal. Never average them.
Classify carrier vs code only when the signals are clear.

    python pair_ev_xactimate.py
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

from extract_xactimate_data import (
    address_keys,
    dummy_address,
    property_key,
    to_float,
)

CARRIERS = (
    "allstate",
    "usaa",
    "state farm",
    "statefarm",
    "farmers",
    "nationwide",
    "liberty mutual",
    "travelers",
    "american family",
    "progressive",
    "aaa",
    "amica",
    "chubb",
    "hartford",
)


def _present(value) -> bool:
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except TypeError:
        pass
    text = str(value).strip()
    return text not in {"", "nan", "None"}


def _num(value):
    if not _present(value):
        return None
    return to_float(value)


def code_line_flags(row: dict) -> list[str]:
    flags = []
    if _present(row.get("ice_water")) or _present(row.get("ice_water_amount")):
        flags.append("ice & water")
    if _present(row.get("steep_charge")):
        flags.append("steep")
    if _present(row.get("decking")) or _present(row.get("decking_amount")):
        flags.append("decking")
    if _present(row.get("felt_30")):
        flags.append("code underlayment")
    return flags


def classify_role(row: dict, filename: str = "") -> tuple[str, str]:
    """Return (role, notes). role is carrier, code, or unknown.

    Do not guess. Lower total alone is not a role.
    """
    carrier = 0
    code = 0
    notes: list[str] = []
    filename = filename or str(row.get("source_file") or "")
    blob = " ".join(
        filter(
            None,
            [
                str(row.get("insurance_company") or ""),
                str(row.get("price_list") or ""),
                str(row.get("ticket_note") or ""),
                filename,
            ],
        )
    ).lower()

    if _present(row.get("insurance_company")) or any(name in blob for name in CARRIERS):
        carrier += 2
        notes.append("carrier header")
    if re.search(r"\binsurance\b", filename, re.I):
        carrier += 2
        notes.append("filename insurance")

    if re.search(r"\bmrc\b|myroofco|final\s+draft", filename, re.I):
        code += 2
        notes.append("filename contractor ticket")
    if str(row.get("price_list") or "").upper().startswith("CODE"):
        code += 2
        notes.append("CODE price list")
    if "contractor header" in str(row.get("ticket_note") or "") and not _present(row.get("insurance_company")):
        code += 2
        notes.append("contractor header")

    flags = code_line_flags(row)
    if flags:
        code += len(flags)
        notes.append("code lines: " + ", ".join(flags))
    else:
        carrier += 1
        notes.append("missing code lines")

    if carrier >= 2 and carrier > code:
        return "carrier", "; ".join(notes)
    if code >= 2 and code > carrier:
        return "code", "; ".join(notes)
    return "unknown", "; ".join(notes) if notes else "no clear signal"


def _specificity(overlap: set[str]) -> int:
    best = 0
    for key in overlap:
        pipes = key.count("|")
        if pipes == 2:
            best = max(best, 3)
        elif pipes == 1:
            best = max(best, 2)
        else:
            best = max(best, 1)
    return best


def pick_ev(xm: dict, ev_rows: list[dict]) -> tuple[dict | None, str | None]:
    xm_keys = address_keys(xm.get("address"))
    if not xm_keys:
        return None, None
    ranked = []
    for ev in ev_rows:
        overlap = xm_keys & address_keys(ev.get("address"))
        if not overlap:
            continue
        ranked.append((_specificity(overlap), ev, overlap))
    if not ranked:
        return None, None
    top_spec = max(item[0] for item in ranked)
    top = [item[1] for item in ranked if item[0] == top_spec]
    if len(top) == 1:
        return top[0], "address"
    xm_sq = _num(xm.get("roof_squares"))
    if xm_sq is not None:
        top.sort(
            key=lambda ev: (
                abs((_num(ev.get("total_squares")) or 0) - xm_sq),
                -(_num(ev.get("total_squares")) or 0),
            )
        )
        return top[0], "address"
    top.sort(key=lambda ev: -(_num(ev.get("total_squares")) or 0))
    return top[0], "address"


def folder_index(pair_map_path: Path) -> dict[str, list[str]]:
    if not pair_map_path.exists():
        return {}
    folder = pd.read_csv(pair_map_path)
    xm_to_ev: dict[str, list[str]] = {}
    for rec in folder.to_dict("records"):
        ev_name = rec.get("ev_source_file")
        names = [part for part in str(rec.get("xact_files") or "").split(";") if part]
        for name in names:
            xm_to_ev.setdefault(name, [])
            if ev_name not in xm_to_ev[name]:
                xm_to_ev[name].append(ev_name)
    return xm_to_ev


def pair_rows(ev: pd.DataFrame, xa: pd.DataFrame, pair_map_path: Path | None = None) -> pd.DataFrame:
    ev_rows = ev.to_dict("records")
    ev_by_file = {row.get("source_file"): row for row in ev_rows}
    folder_map = folder_index(pair_map_path) if pair_map_path else {}
    out = []
    for xm in xa.to_dict("records"):
        ev_row, method = pick_ev(xm, ev_rows)
        if ev_row is None and not dummy_address(xm.get("address")):
            mapped = folder_map.get(str(xm.get("source_file") or ""), [])
            mapped = [name for name in mapped if name in ev_by_file]
            xm_keys = address_keys(xm.get("address"))
            compatible = []
            for name in mapped:
                candidate = ev_by_file[name]
                ev_keys = address_keys(candidate.get("address"))
                if not xm_keys or (xm_keys & ev_keys):
                    compatible.append(candidate)
            if len(compatible) == 1:
                ev_row = compatible[0]
                method = "folder"
            elif len(compatible) > 1:
                xm_sq = _num(xm.get("roof_squares"))
                if xm_sq is not None:
                    compatible.sort(
                        key=lambda row: abs((_num(row.get("total_squares")) or 0) - xm_sq)
                    )
                else:
                    compatible.sort(key=lambda row: -(_num(row.get("total_squares")) or 0))
                ev_row = compatible[0]
                method = "folder"
        role, role_notes = classify_role(xm, str(xm.get("source_file") or ""))
        row = {
            "address": (ev_row or {}).get("address") or xm.get("address"),
            "property_key": property_key((ev_row or {}).get("address") or xm.get("address")),
            "match_method": method,
            "role": role,
            "role_notes": role_notes,
            "ev_source_file": (ev_row or {}).get("source_file"),
            "ev_squares": (ev_row or {}).get("total_squares"),
            "ev_area_sqft": (ev_row or {}).get("total_roof_area_sqft"),
            "ev_pitch": (ev_row or {}).get("predominant_pitch"),
            "ev_facets": (ev_row or {}).get("num_facets"),
            "ev_ridges_ft": (ev_row or {}).get("total_ridges_ft"),
            "ev_valleys_ft": (ev_row or {}).get("total_valleys_ft"),
            "ev_rakes_ft": (ev_row or {}).get("total_rakes_ft"),
            "ev_eaves_ft": (ev_row or {}).get("total_eaves_ft"),
            "ev_waste_pct": (ev_row or {}).get("waste_table_pct"),
            "xact_source_file": xm.get("source_file"),
            "claim_number": xm.get("claim_number"),
            "estimate_number": xm.get("estimate_number"),
            "date_of_loss": xm.get("date_of_loss"),
            "estimate_date": xm.get("estimate_date"),
            "claim_date": xm.get("claim_date"),
            "xact_squares": xm.get("roof_squares"),
            "shingle_type": xm.get("shingle_type"),
            "tear_off": xm.get("tear_off"),
            "tear_off_amount": xm.get("tear_off_amount"),
            "felt": xm.get("felt"),
            "felt_amount": xm.get("felt_amount"),
            "felt_30": xm.get("felt_30"),
            "ice_water": xm.get("ice_water"),
            "ice_water_amount": xm.get("ice_water_amount"),
            "ridge": xm.get("ridge"),
            "ridge_amount": xm.get("ridge_amount"),
            "drip": xm.get("drip"),
            "drip_amount": xm.get("drip_amount"),
            "decking": xm.get("decking"),
            "decking_amount": xm.get("decking_amount"),
            "steep_charge": xm.get("steep_charge"),
            "op": xm.get("op"),
            "grand_total": xm.get("grand_total"),
            "insurance_company": xm.get("insurance_company"),
            "price_list": xm.get("price_list"),
            "ticket_note": xm.get("ticket_note"),
        }
        out.append(row)
    return pd.DataFrame(out)


def _pick_total(rows: list[dict], role: str) -> float | None:
    tagged = [_num(r.get("grand_total")) for r in rows if r.get("role") == role]
    tagged = [n for n in tagged if n is not None]
    if tagged:
        return min(tagged) if role == "carrier" else max(tagged)
    return None


def build_spread(paired: pd.DataFrame, ev: pd.DataFrame) -> pd.DataFrame:
    """One row per property. Spread is the product. No recommended mid."""
    ev_by_key: dict[str, dict] = {}
    for rec in ev.to_dict("records"):
        key = property_key(rec.get("address"))
        if not key:
            continue
        current = ev_by_key.get(key)
        if current is None or (_num(rec.get("total_squares")) or 0) > (_num(current.get("total_squares")) or 0):
            ev_by_key[key] = rec

    groups: dict[str, list[dict]] = {}
    for rec in paired.to_dict("records"):
        if dummy_address(rec.get("address")) and not rec.get("ev_source_file"):
            continue
        key = rec.get("property_key") or property_key(rec.get("address"))
        if not key:
            key = f"file:{rec.get('xact_source_file')}"
        groups.setdefault(key, []).append(rec)

    # Properties with EV but no XM
    for key, rec in ev_by_key.items():
        groups.setdefault(key, [])

    rows = []
    for key, tickets in groups.items():
        ev_row = ev_by_key.get(key) or {}
        if not ev_row and tickets:
            # unmatched XM cluster
            ev_row = {
                "address": tickets[0].get("address"),
                "source_file": tickets[0].get("ev_source_file"),
                "total_squares": tickets[0].get("ev_squares"),
                "predominant_pitch": tickets[0].get("ev_pitch"),
                "num_facets": tickets[0].get("ev_facets"),
            }
        totals = [_num(t.get("grand_total")) for t in tickets]
        totals = [n for n in totals if n is not None]
        untagged = [_num(t.get("grand_total")) for t in tickets if t.get("role") == "unknown"]
        untagged = [n for n in untagged if n is not None]
        carrier_total = _pick_total(tickets, "carrier")
        code_total = _pick_total(tickets, "code")
        notes = []
        used_minmax = False
        if carrier_total is None and code_total is None and totals:
            carrier_total = min(totals)
            code_total = max(totals)
            used_minmax = True
            if len(totals) == 1:
                notes.append("single untagged ticket; min and max are the same number")
            else:
                notes.append("untagged; spread is min vs max, not a role call")
        else:
            if carrier_total is None and untagged:
                carrier_total = min(untagged)
                notes.append("carrier_total is min of untagged tickets")
            if code_total is None and untagged:
                code_total = max(untagged)
                notes.append("code_total is max of untagged tickets")

        delta = None
        if carrier_total is not None and code_total is not None:
            delta = code_total - carrier_total

        role_bits = []
        for t in tickets:
            role_bits.append(f"{t.get('xact_source_file')}:{t.get('role')}")
        if used_minmax:
            notes.append("do not average; do not recommend a mid")
        notes.extend(
            sorted(
                {
                    str(t.get("role_notes"))
                    for t in tickets
                    if t.get("role") in {"carrier", "code"} and t.get("role_notes")
                }
            )
        )

        rows.append(
            {
                "address": ev_row.get("address") or (tickets[0].get("address") if tickets else None),
                "property_key": key,
                "ev_source_file": ev_row.get("source_file"),
                "ev_squares": ev_row.get("total_squares"),
                "ev_pitch": ev_row.get("predominant_pitch"),
                "ev_facets": ev_row.get("num_facets"),
                "carrier_total": carrier_total,
                "code_total": code_total,
                "delta": delta,
                "xm_count": len(tickets),
                "role_guess_notes": "; ".join(role_bits + notes),
            }
        )
    frame = pd.DataFrame(rows)
    if not frame.empty:
        frame = frame.sort_values(["xm_count", "address"], ascending=[False, True])
    return frame


def summarize(paired: pd.DataFrame, spread: pd.DataFrame) -> None:
    xm_n = len(paired)
    unique_addr = paired["property_key"].replace("", pd.NA).nunique(dropna=True)
    matched = paired["ev_source_file"].notna().sum()
    multi = (spread["xm_count"] >= 2).sum()
    print(f"XM files: {xm_n}")
    print(f"Unique property keys: {unique_addr}")
    print(f"XM joined to an EagleView: {matched} / {xm_n}")
    print(f"EV/property rows with 2+ tickets: {int(multi)}")
    print(f"Roles: {paired['role'].value_counts(dropna=False).to_dict()}")
    both = spread[spread["carrier_total"].notna() & spread["code_total"].notna() & (spread["xm_count"] >= 2)]
    if not both.empty:
        median_delta = both["delta"].median()
        print(f"Median code minus carrier (2+ tickets): {median_delta:.0f}")
        print(f"Median carrier total: {both['carrier_total'].median():.0f}")
        print(f"Median code total: {both['code_total'].median():.0f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ev_csv", default="./extracted/eagleview_dataset.csv")
    parser.add_argument("--xm_csv", default="./extracted/xactimate_dataset.csv")
    parser.add_argument("--pair_map", default="./extracted/xactimate_folder_pairs.csv")
    parser.add_argument("--output_dir", default="./extracted")
    args = parser.parse_args()

    ev_path = Path(args.ev_csv)
    xm_path = Path(args.xm_csv)
    if not ev_path.exists():
        print(f"No EagleView CSV at {ev_path}")
        return
    if not xm_path.exists():
        print(f"No Xactimate CSV at {xm_path}")
        return

    ev = pd.read_csv(ev_path)
    xa = pd.read_csv(xm_path)
    paired = pair_rows(ev, xa, Path(args.pair_map))
    spread = build_spread(paired, ev)

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paired_path = out_dir / "paired_ev_xactimate.csv"
    spread_path = out_dir / "roof_bid_spread.csv"
    paired.to_csv(paired_path, index=False)
    spread.to_csv(spread_path, index=False)
    print(paired_path)
    print(spread_path)
    summarize(paired, spread)


if __name__ == "__main__":
    main()
