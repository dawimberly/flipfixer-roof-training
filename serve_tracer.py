"""
Local roof tracer for the EagleView set.

    python serve_tracer.py

Opens http://127.0.0.1:8765 — satellite map, draw or guess outline, compare to EagleView.
"""

from __future__ import annotations

import json
import math
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pandas as pd

import roof_math as rm

ROOT = Path(__file__).resolve().parent
TRACER_DIR = ROOT / "tracer"
TRACES_DIR = ROOT / "traces"
EXTRACTED = ROOT / "extracted"
CSV_PATH = EXTRACTED / "eagleview_dataset.csv"
CACHE_PATH = EXTRACTED / "geocode_cache.json"
TUNE_PATH = EXTRACTED / "tracer_tune.json"
HOST = "127.0.0.1"
PORT = 8765
USER_AGENT = "FlipFixerRoofTraining/1.0 (jon@theflipfixer.com)"


def load_dotenv(path: Path | None = None) -> None:
    env_path = path or (ROOT / ".env")
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def google_maps_key() -> str:
    return (
        os.environ.get("GOOGLE_MAPS_API_KEY") or os.environ.get("MAPS_API_KEY") or ""
    ).strip()


def roof_id(source_file: str) -> str:
    stem = Path(source_file).stem
    return re.sub(r"[^A-Za-z0-9._-]+", "_", stem)


def load_roofs() -> list[dict]:
    if not CSV_PATH.exists():
        return []
    df = pd.read_csv(CSV_PATH)
    rows = []
    for rec in df.to_dict("records"):
        if pd.isna(rec.get("total_squares")):
            continue
        if pd.isna(rec.get("address")) or not str(rec["address"]).strip():
            continue
        src = str(rec["source_file"])
        rid = roof_id(src)
        row = {
            "id": rid,
            "address": str(rec["address"]).strip(),
            "source_file": src,
            "total_roof_area_sqft": _num(rec.get("total_roof_area_sqft")),
            "total_squares": _num(rec.get("total_squares")),
            "predominant_pitch": None
            if pd.isna(rec.get("predominant_pitch"))
            else str(rec["predominant_pitch"]),
            "num_facets": _num(rec.get("num_facets")),
            "total_ridges_ft": _num(rec.get("total_ridges_ft")),
            "total_valleys_ft": _num(rec.get("total_valleys_ft")),
            "total_rakes_ft": _num(rec.get("total_rakes_ft")),
            "total_eaves_ft": _num(rec.get("total_eaves_ft")),
            "waste_table_pct": _num(rec.get("waste_table_pct")),
            "traced": (TRACES_DIR / f"{rid}.json").exists(),
        }
        rows.append(row)
    return rows


def _num(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict) -> None:
    EXTRACTED.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def http_json(url: str, data: bytes | None = None, headers: dict | None = None, timeout: int = 30):
    req = urllib.request.Request(url, data=data, headers=headers or {"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def geocode_google(address: str, key: str) -> dict | None:
    query = urllib.parse.urlencode({"address": address, "key": key})
    url = f"https://maps.googleapis.com/maps/api/geocode/json?{query}"
    try:
        payload = http_json(url)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    if payload.get("status") != "OK" or not payload.get("results"):
        return None
    pick = payload["results"][0]
    for row in payload["results"]:
        if (row.get("geometry") or {}).get("location_type") == "ROOFTOP":
            pick = row
            break
    loc = pick["geometry"]["location"]
    return {
        "lat": float(loc["lat"]),
        "lng": float(loc["lng"]),
        "label": pick.get("formatted_address"),
        "source": "google",
    }


def tidy_address(address: str) -> str:
    """Strip junk that makes free geocoders miss. Does not invent a city."""
    text = re.sub(r"\s+", " ", address or "").strip()
    text = re.sub(r"\s*#\d+[A-Z]?\s*", " ", text, flags=re.I)
    text = re.sub(r",\s*San Antonio Ln,", ", San Antonio,", text, flags=re.I)
    text = re.sub(r"\bCrk\b", "Creek", text, flags=re.I)
    text = re.sub(r"\bPt\b", "Point", text, flags=re.I)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+,", ",", text)
    return text.strip()


def geocode_nominatim(address: str) -> dict | None:
    query = urllib.parse.urlencode({"q": tidy_address(address), "format": "json", "limit": 1})
    url = f"https://nominatim.openstreetmap.org/search?{query}"
    try:
        hits = http_json(url)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    if not hits:
        return None
    return {
        "lat": float(hits[0]["lat"]),
        "lng": float(hits[0]["lon"]),
        "label": hits[0].get("display_name"),
        "source": "nominatim",
    }


def geocode_census(address: str) -> dict | None:
    """US Census Bureau. Free, no key. Street match, not always rooftop."""
    query = urllib.parse.urlencode(
        {
            "address": tidy_address(address),
            "benchmark": "Public_AR_Current",
            "format": "json",
        }
    )
    url = f"https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?{query}"
    try:
        payload = http_json(url, timeout=45)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    matches = ((payload or {}).get("result") or {}).get("addressMatches") or []
    if not matches:
        return None
    coords = matches[0].get("coordinates") or {}
    try:
        lat = float(coords["y"])
        lng = float(coords["x"])
    except (KeyError, TypeError, ValueError):
        return None
    return {
        "lat": lat,
        "lng": lng,
        "label": matches[0].get("matchedAddress") or tidy_address(address),
        "source": "census",
    }


def geocode(address: str) -> dict | None:
    cache = load_cache()
    cached = cache.get(address)
    key = google_maps_key()
    if isinstance(cached, dict) and cached.get("lat") is not None:
        if not key or cached.get("source") == "google":
            return cached
    hit = geocode_google(address, key) if key else None
    if hit is None:
        hit = geocode_census(address)
    if hit is None:
        hit = geocode_nominatim(address)
        if hit:
            time.sleep(1.05)
    if hit:
        cache[address] = hit
        save_cache(cache)
    elif cache.get(address) is None:
        cache.pop(address, None)
        save_cache(cache)
    return hit


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def ring_centroid(latlngs: list[list[float]]) -> tuple[float, float]:
    lat = sum(pt[0] for pt in latlngs) / len(latlngs)
    lng = sum(pt[1] for pt in latlngs) / len(latlngs)
    return lat, lng


def closest_ring(rings: list[list[list[float]]], lat: float, lng: float, max_m: float = 40.0):
    best = None
    best_d = None
    for ring in rings:
        if len(ring) < 3:
            continue
        clat, clng = ring_centroid(ring)
        dist = haversine_m(lat, lng, clat, clng)
        if best_d is None or dist < best_d:
            best = ring
            best_d = dist
    if best is None or best_d is None or best_d > max_m:
        return None
    return best


def osm_building(lat: float, lng: float, radius_m: float = 80.0) -> list[list[float]] | None:
    query = (
        f'[out:json][timeout:25];'
        f'(way["building"](around:{int(radius_m)},{lat},{lng});'
        f'relation["building"](around:{int(radius_m)},{lat},{lng}););'
        f"out geom;"
    )
    url = "https://overpass-api.de/api/interpreter"
    body = urllib.parse.urlencode({"data": query}).encode()
    try:
        payload = http_json(
            url,
            data=body,
            headers={"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"},
        )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    rings = []
    for el in payload.get("elements") or []:
        geom = el.get("geometry") or []
        latlngs = [[pt["lat"], pt["lon"]] for pt in geom]
        if len(latlngs) >= 3:
            rings.append(latlngs)
    return closest_ring(rings, lat, lng)


def microsoft_building(lat: float, lng: float, radius_m: float = 70.0) -> list[list[float]] | None:
    """Microsoft US building footprints via Esri. Footprint, not roof facets."""
    dlat = radius_m / 111000.0
    dlng = radius_m / (111000.0 * max(0.2, abs(math.cos(math.radians(lat)))))
    geom = json.dumps(
        {
            "xmin": lng - dlng,
            "ymin": lat - dlat,
            "xmax": lng + dlng,
            "ymax": lat + dlat,
            "spatialReference": {"wkid": 4326},
        }
    )
    query = urllib.parse.urlencode(
        {
            "f": "geojson",
            "returnGeometry": "true",
            "spatialRel": "esriSpatialRelIntersects",
            "geometry": geom,
            "geometryType": "esriGeometryEnvelope",
            "outSR": "4326",
            "outFields": "*",
        }
    )
    url = (
        "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
        f"MSBFP2/FeatureServer/0/query?{query}"
    )
    try:
        payload = http_json(url)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    rings = []
    for feat in payload.get("features") or []:
        geometry = feat.get("geometry") or {}
        coords = geometry.get("coordinates")
        if not coords:
            continue
        if geometry.get("type") == "MultiPolygon":
            coords = max(coords, key=lambda poly: len(poly[0]) if poly else 0)
        ring = [[pt[1], pt[0]] for pt in coords[0]]
        if len(ring) >= 3:
            rings.append(ring)
    return closest_ring(rings, lat, lng)


def guess_building(lat: float, lng: float) -> tuple[list[list[float]] | None, str | None]:
    ring = osm_building(lat, lng)
    if ring:
        return ring, "osm"
    ring = microsoft_building(lat, lng)
    if ring:
        return ring, "microsoft"
    return None, None


def load_tune() -> dict:
    if TUNE_PATH.exists():
        return json.loads(TUNE_PATH.read_text(encoding="utf-8"))
    return {"gsd_scale": 1.0, "waste_pct": rm.DEFAULT_WASTE_PCT, "n": 0}


def load_all_traces() -> list[dict]:
    if not TRACES_DIR.exists():
        return []
    traces = []
    for path in TRACES_DIR.glob("*.json"):
        traces.append(json.loads(path.read_text(encoding="utf-8")))
    return traces


def build_trace(roof: dict, facets: list[dict], gsd_scale: float, waste_pct: float) -> dict:
    summary = rm.summarize_facets(facets, waste_pct=waste_pct, gsd_scale=gsd_scale)
    ev = {
        "total_roof_area_sqft": roof.get("total_roof_area_sqft"),
        "total_squares": roof.get("total_squares"),
        "num_facets": roof.get("num_facets"),
        "total_eaves_ft": roof.get("total_eaves_ft"),
        "total_rakes_ft": roof.get("total_rakes_ft"),
        "predominant_pitch": roof.get("predominant_pitch"),
    }
    compare = rm.compare_to_eagleview(summary, ev)
    latlngs_all = [pt for facet in facets for pt in facet.get("latlngs") or []]
    lat = lng = None
    if latlngs_all:
        lat = sum(pt[0] for pt in latlngs_all) / len(latlngs_all)
        lng = sum(pt[1] for pt in latlngs_all) / len(latlngs_all)
    zoom = rm.DEFAULT_ZOOM
    origin = None
    schema_facets = []
    for i, facet in enumerate(facets, start=1):
        pts = [(float(p[0]), float(p[1])) for p in facet.get("latlngs") or []]
        if len(pts) < 3:
            continue
        if origin is None and lat is not None:
            wx, wy = rm.latlng_to_world_px(lat, lng, zoom)
            origin = (wx - 320, wy - 320)
        schema_facets.append(
            {
                "facet_id": facet.get("facet_id") or f"F{i}",
                "facet_type": facet.get("facet_type") or "unknown",
                "pitch": facet.get("pitch") or roof.get("predominant_pitch") or "6/12",
                "polygon_px": rm.polygon_px_from_latlngs(pts, zoom, origin),
                "latlngs": pts,
                "area_sqft": facet.get("area_sqft"),
                "notes": facet.get("notes") or "",
            }
        )
    return {
        "id": roof["id"],
        "property": {
            "address": roof["address"],
            "lat": lat,
            "lng": lng,
            "image_zoom": zoom,
            "image_gsd_ft_per_px": rm.gsd_ft_per_pixel(lat or 29.42, zoom) if lat else None,
            "source_file": roof["source_file"],
        },
        "facets": schema_facets,
        "summary": summary,
        "ev": ev,
        "compare": compare,
    }


def json_response(handler: SimpleHTTPRequestHandler, payload, status: int = 200) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler: SimpleHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length") or 0)
    raw = handler.rfile.read(length) if length else b"{}"
    return json.loads(raw.decode("utf-8") or "{}")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(TRACER_DIR), **kwargs)

    def log_message(self, fmt: str, *args) -> None:
        print(f"[tracer] {self.address_string()} {fmt % args}")

    def end_headers(self):
        path = urllib.parse.urlparse(self.path).path
        if path.endswith((".js", ".css", ".html")):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path == "/api/config":
            key = google_maps_key()
            json_response(self, {"googleMapsKey": key, "hasGoogleMaps": bool(key)})
            return
        if path == "/api/roofs":
            json_response(self, {"roofs": load_roofs(), "tune": load_tune()})
            return
        if path.startswith("/api/traces/"):
            rid = path.split("/api/traces/", 1)[-1].strip("/")
            file = TRACES_DIR / f"{rid}.json"
            if not file.exists():
                json_response(self, {"error": "not found"}, 404)
                return
            json_response(self, json.loads(file.read_text(encoding="utf-8")))
            return
        if path == "/api/tune":
            traces = load_all_traces()
            fitted = rm.fit_gsd_scale(traces)
            current = load_tune()
            json_response(self, {"current": current, "fitted": fitted, "traced": len(traces)})
            return
        if path == "/api/earth.kml":
            self._send_kml()
            return
        if path in {"/", "/index.html"}:
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = read_json(self)
        if path == "/api/locate":
            address = body.get("address") or ""
            hit = geocode(address)
            if not hit:
                json_response(self, {"error": "geocode failed"}, 404)
                return
            json_response(self, hit)
            return
        if path == "/api/guess":
            lat, lng = body.get("lat"), body.get("lng")
            if lat is None or lng is None:
                json_response(self, {"error": "lat/lng required"}, 400)
                return
            ring, source = guess_building(float(lat), float(lng))
            json_response(self, {"latlngs": ring, "source": source})
            return
        if path == "/api/preview":
            json_response(self, self._preview(body))
            return
        if path == "/api/save":
            json_response(self, self._save(body))
            return
        if path == "/api/fit":
            traces = load_all_traces()
            fitted = rm.fit_gsd_scale(traces)
            current = load_tune()
            current.update(fitted)
            current["waste_pct"] = current.get("waste_pct", rm.DEFAULT_WASTE_PCT)
            rm.write_tune(TUNE_PATH, current)
            json_response(self, {"current": current, "fitted": fitted, "traced": len(traces)})
            return
        json_response(self, {"error": "unknown endpoint"}, 404)

    def _preview(self, body: dict) -> dict:
        roofs = {row["id"]: row for row in load_roofs()}
        roof = roofs.get(body.get("id"))
        if not roof:
            address = (body.get("address") or "").strip()
            rid = (body.get("id") or "").strip() or roof_id(address or "scratch")
            if not address and not rid:
                return {"error": "unknown roof"}
            roof = {
                "id": rid,
                "address": address or rid,
                "source_file": "scratch",
                "total_roof_area_sqft": None,
                "total_squares": None,
                "predominant_pitch": body.get("predominant_pitch"),
                "num_facets": None,
                "total_ridges_ft": None,
                "total_valleys_ft": None,
                "total_rakes_ft": None,
                "total_eaves_ft": None,
                "waste_table_pct": None,
            }
        tune = load_tune()
        gsd_scale = float(body.get("gsd_scale") or tune.get("gsd_scale") or 1.0)
        waste_pct = float(body.get("waste_pct") or tune.get("waste_pct") or rm.DEFAULT_WASTE_PCT)
        facets = body.get("facets") or []
        return build_trace(roof, facets, gsd_scale, waste_pct)

    def _save(self, body: dict) -> dict:
        preview = self._preview(body)
        if preview.get("error"):
            return preview
        TRACES_DIR.mkdir(parents=True, exist_ok=True)
        path = TRACES_DIR / f"{preview['id']}.json"
        path.write_text(json.dumps(preview, indent=2), encoding="utf-8")
        return {"ok": True, "path": str(path), "trace": preview}

    def _send_kml(self) -> None:
        roofs = load_roofs()
        placemarks = []
        for roof in roofs:
            cache = load_cache().get(roof["address"]) or {}
            name = roof["address"].replace("&", "and")
            extra = ""
            if cache.get("lat"):
                extra = f"<Point><coordinates>{cache['lng']},{cache['lat']},0</coordinates></Point>"
            placemarks.append(
                f"<Placemark><name>{name}</name><description>{roof['source_file']} {roof['total_squares']} sq</description>{extra}</Placemark>"
            )
        kml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
            "<name>Flip Fixer EagleView set</name>"
            + "".join(placemarks)
            + "</Document></kml>"
        )
        data = kml.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/vnd.google-earth.kml+xml")
        self.send_header("Content-Disposition", "attachment; filename=eagleview-roofs.kml")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    load_dotenv()
    TRACER_DIR.mkdir(parents=True, exist_ok=True)
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACTED.mkdir(parents=True, exist_ok=True)
    roofs = load_roofs()
    print(f"Tracer: {len(roofs)} EagleView roofs")
    print(f"http://{HOST}:{PORT}")
    if google_maps_key():
        print("Google Maps: official satellite (API key loaded)")
    else:
        print("Geocode: US Census (free). Google stays off until you add a key.")
    print("Draw on satellite, or Guess outline, then Save. Fit scale when you have a handful.")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped")


if __name__ == "__main__":
    main()
