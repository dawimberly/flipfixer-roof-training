"""
Measure each EagleView roof the way 7627 was remeasured.

Look up the county lot by house number and street, take the Microsoft
building whose centroid sits inside that lot, measure it as one plane at
the EagleView pitch, no waste. Does not use the geocode pin.

    python backtest_parcel.py

Writes extracted/parcel_backtest.csv (gitignored). Does not commit reports.
"""

from __future__ import annotations

import json
import math
import re
import time
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd

import roof_math as rm
from serve_tracer import EXTRACTED, load_roofs

USER_AGENT = "FlipFixerRoofTraining/1.0 (jon@theflipfixer.com)"
SUFFIXES = {
    "st", "street", "dr", "drive", "ave", "avenue", "ln", "lane", "rd", "road",
    "cir", "circle", "ct", "court", "blvd", "boulevard", "ter", "terrace",
    "way", "pl", "place", "pkwy", "trl", "trail", "hwy", "pt", "point",
    "crk", "creek", "xing", "crossing",
}
DIRS = {"n", "s", "e", "w", "ne", "nw", "se", "sw", "north", "south", "east", "west"}
ALIASES = {
    "FIELD": "FLD",
    "RANCH": "RNCH",
    "COURT": "CT",
    "TRAIL": "TRL",
    "HEIGHTS": "HTS",
    "MOUNTAIN": "MTN",
}

BEXAR = (
    "https://maps.bexar.org/arcgis/rest/services/Parcels/MapServer/0/query",
    "Situs",
    "bexar",
)
TRAVIS = (
    "https://services1.arcgis.com/HGcSYZ5bvjRswoCb/ArcGIS/rest/services/TCAD_Parcels_Dec_2025/FeatureServer/0/query",
    "situs_address",
    "travis",
)
COLORADO = (
    "https://gis.colorado.gov/public/rest/services/Address_and_Parcel/Colorado_Public_Parcels/FeatureServer/0/query",
    "situsAdd",
    "colorado",
)
KENDALL = (
    "https://maps.pape-dawson.com/server2/rest/services/PD_GIS_Webmap/PD_GIS_WebMap__SanAntonio_External/MapServer/216/query",
    "SITUS_ADDR",
    "kendall",
)
GUADALUPE = (
    "https://maps.pape-dawson.com/server1/rest/services/LandDevelopment/LANDDEVELOPMENT__Lennar_SiteSelection/MapServer/83/query",
    "SITUS_ADDR",
    "guadalupe",
)


def http_json(url: str, timeout: int = 25) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def parse_address(address: str) -> tuple[str | None, list[str], str | None, str | None]:
    head = address.split(",")[0]
    unit = None
    unit_match = re.search(r"#\s*([A-Za-z0-9]+)", head)
    if unit_match:
        unit = unit_match.group(1).upper()
        head = head[: unit_match.start()]
    zip_match = re.search(r"\b(\d{5})(?:-\d{4})?\b", address)
    zip_code = zip_match.group(1) if zip_match else None
    parts = re.findall(r"[A-Za-z0-9]+", head.replace(".", " "))
    number = parts[0] if parts and parts[0].isdigit() else None
    tokens = []
    for part in parts[1:] if number else parts:
        low = part.lower()
        if low in DIRS or low in SUFFIXES:
            continue
        tokens.append(part.upper())
    return number, tokens, zip_code, unit


def stems(token: str) -> list[str]:
    """Query hints only. A lot is accepted only if the street word itself matches."""
    out = [token]
    if len(token) >= 6 and token.endswith("S"):
        out.append(token[:-1])
    short = ALIASES.get(token)
    if short:
        out.append(short)
    seen = []
    for item in out:
        if item not in seen and len(item) >= 3:
            seen.append(item)
    return seen


def token_in_situs(token: str, words: list[str]) -> bool:
    options = {token, ALIASES.get(token)}
    options.discard(None)
    if len(token) >= 6 and token.endswith("S"):
        options.add(token[:-1])
    for word in words:
        if word in options:
            return True
        for option in options:
            if len(option) >= 6 and word.startswith(option):
                return True
    return False


def services_for(address: str, zip_code: str | None) -> list[tuple[str, str, str]]:
    text = address.upper()
    if " CO " in f" {text} " or text.endswith(" CO") or ", CO" in text:
        return [COLORADO]
    if re.search(r"\b(MT|ND)\b", text):
        return []
    if zip_code and zip_code.startswith("787"):
        return [TRAVIS]
    if zip_code == "78006" or "BOERNE" in text:
        return [KENDALL, BEXAR]
    if zip_code == "78108" or "CIBOLO" in text:
        return [GUADALUPE, BEXAR]
    if zip_code == "78023" or "HELOTES" in text:
        return [BEXAR, KENDALL]
    return [BEXAR]


def point_in_ring(lng: float, lat: float, ring: list[list[float]]) -> bool:
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > lat) != (yj > lat)) and (lng < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-15) + xi):
            inside = not inside
        j = i
    return inside


def exteriors(geometry: dict) -> list[list[list[float]]]:
    coords = geometry.get("coordinates") or []
    kind = geometry.get("type")
    if kind == "Polygon":
        return [coords[0]] if coords else []
    if kind == "MultiPolygon":
        return [poly[0] for poly in coords if poly]
    return []


def ring_centroid(ring: list[list[float]]) -> tuple[float, float]:
    lng = sum(pt[0] for pt in ring) / len(ring)
    lat = sum(pt[1] for pt in ring) / len(ring)
    return lng, lat


def contains(geometry: dict, lng: float, lat: float) -> bool:
    return any(point_in_ring(lng, lat, ring) for ring in exteriors(geometry) if len(ring) >= 3)


def query_parcels(service: tuple[str, str, str], number: str, token: str) -> list[dict]:
    url_base, field, _name = service
    where = f"UPPER({field}) LIKE '%{number}%' AND UPPER({field}) LIKE '%{token}%'"
    query = urllib.parse.urlencode(
        {
            "where": where,
            "outFields": field,
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "geojson",
            "resultRecordCount": 15,
        }
    )
    payload = http_json(f"{url_base}?{query}")
    if payload.get("error"):
        raise RuntimeError(str(payload["error"])[:180])
    rows = []
    for feat in payload.get("features") or []:
        props = feat.get("properties") or {}
        situs = str(props.get(field) or "")
        geometry = feat.get("geometry") or {}
        if exteriors(geometry):
            rows.append({"situs": situs, "geometry": geometry})
    return rows


def score_parcel(row: dict, number: str, tokens: list[str], zip_code: str | None, unit: str | None) -> int:
    situs = re.sub(r"\s+", " ", row["situs"].upper())
    words = re.findall(r"[A-Z0-9]+", situs)
    if not re.search(rf"(^|\D){re.escape(number)}(\D|$)", situs):
        return -1
    if not tokens or not all(token_in_situs(token, words) for token in tokens):
        return -1
    if unit and unit not in words and f"#{unit}" not in situs:
        return -1
    score = 10 + 5 * len(tokens)
    if zip_code and zip_code in situs:
        score += 4
    if unit:
        score += 6
    return score


def find_parcel(address: str) -> tuple[dict | None, str]:
    number, tokens, zip_code, unit = parse_address(address)
    if not number or not tokens:
        return None, "address did not parse"
    services = services_for(address, zip_code)
    if not services:
        return None, "no parcel layer for this state"
    last_error = "parcel not found"
    for service in services:
        tried = []
        for token in tokens:
            tried.extend(stems(token))
        seen = []
        for stem in tried:
            if stem not in seen:
                seen.append(stem)
        for stem in seen[:4]:
            try:
                hits = query_parcels(service, number, stem)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as err:
                last_error = f"{service[2]} lookup failed"
                print(f"    {service[2]} {stem}: {err}")
                continue
            ranked = []
            for hit in hits:
                score = score_parcel(hit, number, tokens, zip_code, unit)
                if score >= 10:
                    ranked.append((score, hit))
            if not ranked:
                continue
            ranked.sort(key=lambda item: item[0], reverse=True)
            best_score = ranked[0][0]
            best = [hit for score, hit in ranked if score == best_score]
            chosen = best[0]
            chosen["source"] = service[2]
            chosen["hits"] = len(ranked)
            return chosen, "ok"
    return None, last_error


def microsoft_in_parcel(geometry: dict) -> tuple[list[list[float]] | None, int]:
    rings = exteriors(geometry)
    if not rings:
        return None, 0
    pts = [pt for ring in rings for pt in ring]
    min_lng = min(pt[0] for pt in pts)
    max_lng = max(pt[0] for pt in pts)
    min_lat = min(pt[1] for pt in pts)
    max_lat = max(pt[1] for pt in pts)
    pad_lat = 30 / 111000
    pad_lng = 30 / (111000 * max(0.2, abs(math.cos(math.radians((min_lat + max_lat) / 2)))))
    envelope = json.dumps(
        {
            "xmin": min_lng - pad_lng,
            "ymin": min_lat - pad_lat,
            "xmax": max_lng + pad_lng,
            "ymax": max_lat + pad_lat,
            "spatialReference": {"wkid": 4326},
        }
    )
    query = urllib.parse.urlencode(
        {
            "f": "geojson",
            "returnGeometry": "true",
            "spatialRel": "esriSpatialRelIntersects",
            "geometry": envelope,
            "geometryType": "esriGeometryEnvelope",
            "outSR": "4326",
            "outFields": "OBJECTID",
        }
    )
    url = (
        "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
        f"MSBFP2/FeatureServer/0/query?{query}"
    )
    payload = http_json(url, timeout=40)
    inside = []
    for feat in payload.get("features") or []:
        building = feat.get("geometry") or {}
        building_rings = exteriors(building)
        if not building_rings:
            continue
        ring = max(building_rings, key=len)
        lng, lat = ring_centroid(ring)
        if not contains(geometry, lng, lat):
            continue
        latlngs = [[pt[1], pt[0]] for pt in ring]
        area = rm.geodesic_ring_area_sqft([(pt[0], pt[1]) for pt in latlngs])
        inside.append((area, latlngs))
    if not inside:
        return None, 0
    inside.sort(key=lambda item: item[0], reverse=True)
    return inside[0][1], len(inside)


def measure(roof: dict, latlngs: list[list[float]]) -> tuple[dict, dict]:
    pitch = roof.get("predominant_pitch") or "6/12"
    summary = rm.summarize_facets(
        [{"pitch": pitch, "latlngs": latlngs}],
        waste_pct=0,
        gsd_scale=1.0,
    )
    compare = rm.compare_to_eagleview(
        summary,
        {
            "total_roof_area_sqft": roof.get("total_roof_area_sqft"),
            "total_squares": roof.get("total_squares"),
            "num_facets": roof.get("num_facets"),
            "predominant_pitch": pitch,
        },
    )
    return summary, compare


def main() -> None:
    roofs = [row for row in load_roofs() if (row.get("total_squares") or 0) >= 8]
    cache: dict[str, tuple] = {}
    rows = []
    for i, roof in enumerate(roofs, start=1):
        address = roof["address"]
        print(f"[{i}/{len(roofs)}] {address}")
        key = re.sub(r"\s+", " ", address.upper())
        if key not in cache:
            parcel, note = find_parcel(address)
            if not parcel:
                cache[key] = (None, None, 0, note)
            else:
                try:
                    ring, n_buildings = microsoft_in_parcel(parcel["geometry"])
                except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as err:
                    print(f"    microsoft: {err}")
                    cache[key] = (parcel, None, 0, "microsoft lookup failed")
                else:
                    status = "ok" if ring else "no building in parcel"
                    cache[key] = (parcel, ring, n_buildings, status)
            time.sleep(0.12)
        parcel, ring, n_buildings, status = cache[key]
        trace = compare = None
        if ring:
            trace, compare = measure(roof, ring)
            status = "ok"
        rows.append(
            {
                "id": roof["id"],
                "address": address,
                "parcel_source": None if not parcel else parcel.get("source"),
                "parcel_situs": None if not parcel else re.sub(r"\s+", " ", parcel.get("situs") or "").strip(),
                "buildings_in_parcel": n_buildings or None,
                "ev_squares": roof.get("total_squares"),
                "ev_area_sqft": roof.get("total_roof_area_sqft"),
                "ev_pitch": roof.get("predominant_pitch"),
                "ev_facets": roof.get("num_facets"),
                "traced_squares": None if not trace else trace.get("total_squares"),
                "traced_area_sqft": None if not trace else trace.get("total_area_with_pitch_multiplier_sqft"),
                "squares_error_pct": None if not compare else compare.get("squares_error_pct"),
                "area_error_pct": None if not compare else compare.get("area_error_pct"),
                "status": status,
            }
        )

    frame = pd.DataFrame(rows)
    EXTRACTED.mkdir(parents=True, exist_ok=True)
    out = EXTRACTED / "parcel_backtest.csv"
    frame.to_csv(out, index=False)
    print(out)
    ok = frame[frame["status"] == "ok"].copy()
    print(f"Measured {len(ok)} / {len(frame)}")
    if not ok.empty:
        abs_sq = ok["squares_error_pct"].abs()
        print(f"Median |squares error|: {abs_sq.median():.1f}%")
        print(f"Mean |squares error|: {abs_sq.mean():.1f}%")
        for band in (5, 10, 15, 25):
            n = int((abs_sq <= band).sum())
            print(f"Within {band}%: {n}/{len(ok)}")
        worst = ok.assign(abs_err=ok["squares_error_pct"].abs()).sort_values("abs_err", ascending=False)
        print(worst[["address", "parcel_situs", "ev_squares", "traced_squares", "squares_error_pct"]].head(12).to_string(index=False))
    missed = frame[frame["status"] != "ok"]
    if not missed.empty:
        print("Not measured:")
        print(missed[["address", "status"]].to_string(index=False))


if __name__ == "__main__":
    main()
