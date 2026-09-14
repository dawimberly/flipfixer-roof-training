const PITCHES = ["0/12","1/12","2/12","3/12","4/12","5/12","6/12","7/12","8/12","9/12","10/12","11/12","12/12"];
const TRACE_ZOOM = 21;

const state = {
  roofs: [],
  tune: { gsd_scale: 1, waste_pct: 12 },
  current: null,
  traces: {},
  outlineDraft: false,
  guessRing: "",
};

const listEl = document.getElementById("list");
const titleEl = document.getElementById("roof-title");
const metaEl = document.getElementById("roof-meta");
const compareEl = document.getElementById("compare");
const statusEl = document.getElementById("status");
const pitchEl = document.getElementById("pitch");
const scaleEl = document.getElementById("gsd-scale");
const wasteEl = document.getElementById("waste");
const earthLink = document.getElementById("earth-link");
const drawHelp = document.getElementById("draw-help");

PITCHES.forEach((p) => {
  const opt = document.createElement("option");
  opt.value = p;
  opt.textContent = p;
  pitchEl.appendChild(opt);
});

function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = src;
    s.async = true;
    s.onload = resolve;
    s.onerror = () => reject(new Error("Failed to load map script"));
    document.head.appendChild(s);
  });
}

const DRAINS = [
  ["", "Drain"],
  ["0", "N"],
  ["45", "NE"],
  ["90", "E"],
  ["135", "SE"],
  ["180", "S"],
  ["225", "SW"],
  ["270", "W"],
  ["315", "NW"],
];

function facetPopupHtml(pitch, slopeDeg) {
  const opts = PITCHES.map((p) => `<option${p === pitch ? " selected" : ""}>${p}</option>`).join("");
  const slope = slopeDeg === null || slopeDeg === undefined || slopeDeg === "" ? "" : String(slopeDeg);
  const drains = DRAINS.map(([value, label]) => `<option value="${value}"${value === slope ? " selected" : ""}>${label}</option>`).join("");
  return `Facet pitch <select id="facet-pitch">${opts}</select>
    <br>Drains <select id="facet-drain">${drains}</select>`;
}

function slopeFromSelect(select) {
  if (!select || select.value === "") return null;
  return Number(select.value);
}

const SNAP_FT = 2;
const EDGE_COLOR = {
  ridge: "#e23d3d",
  hip: "#e07a2f",
  valley: "#3d7dff",
  rake: "#3dd68c",
  eave: "#f4f7fa",
  step: "#8b97a3",
  unclassified: "#8b97a3",
};

function localMeters(lat) {
  const latR = (lat * Math.PI) / 180;
  return {
    mLat: 111132.92 - 559.82 * Math.cos(2 * latR),
    mLng: 111412.84 * Math.cos(latR) - 93.5 * Math.cos(3 * latR),
  };
}

function toFt(lat, lng, originLat) {
  const { mLat, mLng } = localMeters(originLat);
  return { x: lng * mLng * 3.28084, y: lat * mLat * 3.28084 };
}

function fromFt(x, y, originLat) {
  const { mLat, mLng } = localMeters(originLat);
  return { lat: y / 3.28084 / mLat, lng: x / 3.28084 / mLng };
}

function snapPlacement(lat, lng, rings) {
  if (!rings.length) return { lat, lng };
  const origin = rings[0].latlngs[0][0];
  const p = toFt(lat, lng, origin);
  let best = null;
  rings.forEach((ring, ringIndex) => {
    const pts = ring.latlngs || [];
    pts.forEach((pt) => {
      const q = toFt(pt[0], pt[1], origin);
      const d = Math.hypot(p.x - q.x, p.y - q.y);
      if (!best || d < best.d) best = { d, lat: pt[0], lng: pt[1], kind: "vertex" };
    });
    for (let i = 0; i < pts.length; i += 1) {
      const bpt = pts[(i + 1) % pts.length];
      const a = toFt(pts[i][0], pts[i][1], origin);
      const b = toFt(bpt[0], bpt[1], origin);
      const abx = b.x - a.x;
      const aby = b.y - a.y;
      const len2 = abx * abx + aby * aby;
      if (len2 < 1) continue;
      let t = ((p.x - a.x) * abx + (p.y - a.y) * aby) / len2;
      t = Math.max(0, Math.min(1, t));
      if (t < 0.04 || t > 0.96) continue;
      const x = a.x + t * abx;
      const y = a.y + t * aby;
      const d = Math.hypot(p.x - x, p.y - y);
      if (!best || d < best.d) {
        const ll = fromFt(x, y, origin);
        best = { d, lat: ll.lat, lng: ll.lng, kind: "edge", ringIndex, insertAfter: i };
      }
    }
  });
  if (!best || best.d > SNAP_FT) return { lat, lng };
  return best;
}

const ANGLES = {
  top: { tilt: 0, heading: 0, label: "Top", drain: null, note: "The run. Plan length of every side, and where the planes meet. The rise is in the side photos." },
  north: { tilt: 45, heading: 180, label: "North", drain: 0, note: "Planes that drain north face you. The rise is the triangle on the east and west ends." },
  east: { tilt: 45, heading: 270, label: "East", drain: 90, note: "Planes that drain east face you. The rise is the triangle on the north and south ends." },
  south: { tilt: 45, heading: 0, label: "South", drain: 180, note: "Planes that drain south face you. The rise is the triangle on the east and west ends." },
  west: { tilt: 45, heading: 90, label: "West", drain: 270, note: "Planes that drain west face you. The rise is the triangle on the north and south ends." },
};

const camera = { angle: "top", dateId: "" };

function waybackTileUrl(dateId, z, x, y) {
  return `https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/WMTS/1.0.0/default028mm/MapServer/tile/${dateId}/${z}/${y}/${x}`;
}

function markAngle(angle) {
  document.querySelectorAll("#angles button").forEach((btn) => {
    btn.classList.toggle("on", btn.dataset.angle === angle);
  });
}

async function openEarthPro(lat, lng, address) {
  if (!lat || !lng) {
    statusEl.textContent = "Locate the house first, then open Earth Pro";
    return;
  }
  try {
    await api("/api/open-earth", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lat, lng, address }),
    });
    statusEl.textContent = "Earth Pro opened. The address text sits on the roof. A tree next door is not this house.";
  } catch (err) {
    statusEl.textContent = String(err);
  }
}

function leafletGoogleTiles() {
  const opts = {
    subdomains: ["0", "1", "2", "3"],
    maxZoom: 22,
    maxNativeZoom: 22,
    attribution: "&copy; Google",
  };
  return {
    satellite: L.tileLayer("https://mt{s}.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}", opts),
    hybrid: L.tileLayer("https://mt{s}.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}", opts),
    esri: L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      { attribution: "Tiles &copy; Esri", maxZoom: 22, maxNativeZoom: 19 }
    ),
  };
}

function initLeafletMap() {
  const map = L.map("map", { maxZoom: 22, zoomControl: true });
  const tiles = leafletGoogleTiles();
  tiles.satellite.addTo(map);
  L.control.layers({
    "Google satellite": tiles.satellite,
    "Google labels": tiles.hybrid,
    Esri: tiles.esri,
  }).addTo(map);
  map.setView([29.4241, -98.4936], 18);
  setTimeout(() => map.invalidateSize(), 0);
  if (drawHelp) {
    drawHelp.hidden = false;
    drawHelp.textContent = "Use Draw facet or the polygon tool. A click within 2 ft of a corner or a side snaps to it.";
  }

  const drawn = new L.FeatureGroup();
  map.addLayer(drawn);
  const edgeLayer = new L.FeatureGroup();
  map.addLayer(edgeLayer);
  const drawControl = new L.Control.Draw({
    draw: {
      polygon: { allowIntersection: false, showArea: true },
      polyline: false,
      circle: false,
      rectangle: false,
      circlemarker: false,
      marker: false,
    },
    edit: { featureGroup: drawn },
  });
  map.addControl(drawControl);

  let pin = null;
  let wayback = null;
  map.on(L.Draw.Event.CREATED, (event) => {
    const layer = event.layer;
    const rings = leafletRings();
    const hits = [];
    const snapped = (layer.getLatLngs()[0] || []).map((pt) => {
      const hit = snapPlacement(pt.lat, pt.lng, rings);
      if (hit.kind === "edge") hits.push(hit);
      return [hit.lat, hit.lng];
    });
    hits.sort((a, b) => b.insertAfter - a.insertAfter);
    hits.forEach((hit) => insertLeafletVertex(hit));
    layer.setLatLngs(snapped);
    layer.feature = { properties: { pitch: pitchEl.value, slope_deg: null } };
    drawn.addLayer(layer);
    bindLeafletFacet(layer);
    preview();
  });
  map.on(L.Draw.Event.EDITED, () => {
    acceptOutlineEdit();
    preview();
  });
  map.on(L.Draw.Event.DELETED, () => {
    acceptOutlineEdit();
    preview();
  });

  function leafletRings() {
    const rings = [];
    drawn.eachLayer((layer) => {
      if (!layer.getLatLngs) return;
      const ring = layer.getLatLngs()[0] || [];
      if (ring.length >= 2) rings.push({ latlngs: ring.map((pt) => [pt.lat, pt.lng]) });
    });
    return rings;
  }

  function insertLeafletVertex(hit) {
    const layers = [];
    drawn.eachLayer((layer) => {
      if (layer.getLatLngs) layers.push(layer);
    });
    const layer = layers[hit.ringIndex];
    if (!layer) return;
    const ring = (layer.getLatLngs()[0] || []).slice();
    ring.splice(hit.insertAfter + 1, 0, L.latLng(hit.lat, hit.lng));
    layer.setLatLngs(ring);
  }

  function bindLeafletFacet(layer) {
    const props = (layer.feature && layer.feature.properties) || {};
    const pitch = props.pitch || pitchEl.value;
    layer.bindPopup(facetPopupHtml(pitch, props.slope_deg));
    layer.on("popupopen", () => {
      const select = document.getElementById("facet-pitch");
      const drain = document.getElementById("facet-drain");
      if (select) {
        select.onchange = () => {
          layer.feature.properties.pitch = select.value;
          preview();
        };
      }
      if (drain) {
        drain.onchange = () => {
          layer.feature.properties.slope_deg = slopeFromSelect(drain);
          preview();
        };
      }
    });
  }

  return {
    kind: "leaflet",
    setView(lat, lng, zoom) {
      map.setView([lat, lng], zoom || TRACE_ZOOM);
      if (pin) map.removeLayer(pin);
      pin = L.circleMarker([lat, lng], {
        radius: 5,
        color: "#ffd166",
        weight: 2,
        fillOpacity: 0.2,
      }).addTo(map);
    },
    clear() {
      drawn.clearLayers();
      edgeLayer.clearLayers();
    },
    setPolygons(facets) {
      drawn.clearLayers();
      edgeLayer.clearLayers();
      (facets || []).forEach((facet) => {
        const latlngs = (facet.latlngs || []).map((pt) => [pt[0], pt[1]]);
        if (latlngs.length < 3) return;
        const layer = L.polygon(latlngs, { color: "#4da3ff" });
        layer.feature = { properties: { pitch: facet.pitch || pitchEl.value, slope_deg: facet.slope_deg ?? null } };
        drawn.addLayer(layer);
        bindLeafletFacet(layer);
      });
    },
    setEdges(edges) {
      edgeLayer.clearLayers();
      (edges || []).forEach((edge) => {
        const latlngs = edge.latlngs || [];
        if (latlngs.length < 2) return;
        L.polyline(latlngs.map((pt) => [pt[0], pt[1]]), {
          color: EDGE_COLOR[edge.kind] || EDGE_COLOR.unclassified,
          weight: 4,
          opacity: 0.95,
          dashArray: edge.kind === "valley" ? "7 5" : null,
          interactive: false,
        }).addTo(edgeLayer);
      });
    },
    getFacets() {
      const facets = [];
      drawn.eachLayer((layer) => {
        if (!layer.getLatLngs) return;
        const ring = layer.getLatLngs()[0] || [];
        const latlngs = ring.map((pt) => [pt.lat, pt.lng]);
        if (latlngs.length < 3) return;
        const props = (layer.feature && layer.feature.properties) || {};
        facets.push({
          pitch: props.pitch || pitchEl.value,
          slope_deg: props.slope_deg ?? null,
          latlngs,
        });
      });
      return facets;
    },
    startDraw() {
      new L.Draw.Polygon(map, drawControl.options.draw.polygon).enable();
    },
    setAngle(angle) {
      camera.angle = "top";
      markAngle("top");
      statusEl.textContent = "This map is the top photo, the run. North, south, east, and west need the Google map for the rise.";
    },
    setDate(dateId) {
      camera.dateId = dateId || "";
      if (wayback) {
        map.removeLayer(wayback);
        wayback = null;
      }
      if (!dateId) {
        if (!map.hasLayer(tiles.satellite)) tiles.satellite.addTo(map);
        statusEl.textContent = "Latest Google satellite";
        return;
      }
      if (map.hasLayer(tiles.satellite)) map.removeLayer(tiles.satellite);
      wayback = L.tileLayer(waybackTileUrl(dateId, "{z}", "{x}", "{y}"), {
        maxZoom: 22,
        maxNativeZoom: 19,
        attribution: "Wayback imagery &copy; Esri",
      }).addTo(map);
      const opt = document.querySelector(`#imagery-date option[value="${dateId}"]`);
      statusEl.textContent = opt ? opt.textContent : "Older aerial";
    },
  };
}

function initGoogleMap() {
  const googleMap = new google.maps.Map(document.getElementById("map"), {
    center: { lat: 29.4241, lng: -98.4936 },
    zoom: 18,
    mapTypeId: "satellite",
    tilt: 0,
    heading: 0,
    maxZoom: 22,
    minZoom: 14,
    disableDoubleClickZoom: true,
    clickableIcons: false,
    streetViewControl: false,
    fullscreenControl: true,
    rotateControl: false,
    mapTypeControl: true,
    mapTypeControlOptions: {
      mapTypeIds: ["satellite", "hybrid"],
    },
    gestureHandling: "greedy",
  });
  googleMap.setTilt(0);

  const polygons = [];
  const edgeLines = [];
  const info = new google.maps.InfoWindow();
  let pin = null;
  let waybackType = null;
  const draft = { path: [], line: null };

  function applyCamera() {
    const dated = Boolean(camera.dateId);
    const angle = dated ? ANGLES.top : (ANGLES[camera.angle] || ANGLES.top);
    if (dated) {
      if (!waybackType || waybackType.dateId !== camera.dateId) {
        waybackType = new google.maps.ImageMapType({
          getTileUrl: (coord, zoom) => waybackTileUrl(camera.dateId, zoom, coord.x, coord.y),
          tileSize: new google.maps.Size(256, 256),
          maxZoom: 19,
          minZoom: 14,
          name: "Aerial archive",
        });
        waybackType.dateId = camera.dateId;
      }
      if (!googleMap.mapTypes.get("wayback")) {
        googleMap.mapTypes.set("wayback", waybackType);
      } else {
        googleMap.mapTypes.set("wayback", waybackType);
      }
      googleMap.setMapTypeId("wayback");
      googleMap.setOptions({ maxZoom: 19, tilt: 0, heading: 0 });
      if (googleMap.getZoom() > 19) googleMap.setZoom(19);
      return;
    }
    googleMap.setMapTypeId("satellite");
    googleMap.setOptions({ maxZoom: 22, tilt: angle.tilt, heading: angle.heading });
    googleMap.setTilt(angle.tilt);
    googleMap.setHeading(angle.heading);
  }

  function stylePoly() {
    return {
      strokeColor: "#4da3ff",
      strokeWeight: 2,
      fillColor: "#4da3ff",
      fillOpacity: 0.22,
      editable: true,
      clickable: true,
    };
  }

  function googleRings() {
    return polygons.map((polygon) => ({
      latlngs: polygon.getPath().getArray().map((pt) => [pt.lat(), pt.lng()]),
    })).filter((ring) => ring.latlngs.length >= 2);
  }

  function insertGoogleVertex(hit) {
    const polygon = polygons[hit.ringIndex];
    if (!polygon) return;
    polygon.getPath().insertAt(hit.insertAfter + 1, { lat: hit.lat, lng: hit.lng });
  }

  function clearEdgeLines() {
    edgeLines.splice(0).forEach((line) => line.setMap(null));
  }

  function bindGoogleFacet(polygon) {
    polygon.addListener("click", () => {
      const viewDrain = ANGLES[camera.angle] && ANGLES[camera.angle].drain;
      if ((polygon.slopeDeg === null || polygon.slopeDeg === undefined) && viewDrain !== null && viewDrain !== undefined) {
        polygon.slopeDeg = viewDrain;
        preview();
      }
      const pitch = polygon.facetPitch || pitchEl.value;
      info.setContent(facetPopupHtml(pitch, polygon.slopeDeg));
      info.setPosition(polygon.getPath().getAt(0));
      info.open(googleMap);
      google.maps.event.addListenerOnce(info, "domready", () => {
        const select = document.getElementById("facet-pitch");
        const drain = document.getElementById("facet-drain");
        if (select) {
          select.onchange = () => {
            polygon.facetPitch = select.value;
            preview();
          };
        }
        if (drain) {
          drain.onchange = () => {
            polygon.slopeDeg = slopeFromSelect(drain);
            preview();
          };
        }
      });
    });
    const path = polygon.getPath();
    path.addListener("set_at", () => {
      acceptOutlineEdit();
      preview();
    });
    path.addListener("insert_at", () => {
      acceptOutlineEdit();
      preview();
    });
    path.addListener("remove_at", () => {
      acceptOutlineEdit();
      preview();
    });
  }

  function redrawDraft() {
    if (draft.line) draft.line.setMap(null);
    if (draft.path.length < 1) return;
    draft.line = new google.maps.Polyline({
      path: draft.path,
      strokeColor: "#ffd166",
      strokeWeight: 2,
      map: googleMap,
      clickable: false,
    });
  }

  function closeDraft() {
    if (draft.path.length < 3) {
      statusEl.textContent = "Need at least 3 corners";
      return;
    }
    const polygon = new google.maps.Polygon({
      paths: draft.path,
      map: googleMap,
      ...stylePoly(),
    });
    polygon.facetPitch = pitchEl.value;
    polygon.slopeDeg = null;
    polygons.push(polygon);
    bindGoogleFacet(polygon);
    draft.path = [];
    if (draft.line) {
      draft.line.setMap(null);
      draft.line = null;
    }
    preview();
    statusEl.textContent = "Facet added — click the next roof plane, or Save";
  }

  googleMap.addListener("click", (event) => {
    const rings = googleRings();
    const hit = snapPlacement(event.latLng.lat(), event.latLng.lng(), rings);
    if (hit.kind === "edge") insertGoogleVertex(hit);
    draft.path.push({ lat: hit.lat, lng: hit.lng });
    redrawDraft();
    statusEl.textContent = `${draft.path.length} points — Enter or double-click to close`;
  });
  googleMap.addListener("dblclick", (event) => {
    event.stop();
    closeDraft();
  });

  document.addEventListener("keydown", (event) => {
    if (event.target.tagName === "INPUT" || event.target.tagName === "SELECT") return;
    if (event.key === "Enter" && draft.path.length >= 3) {
      event.preventDefault();
      closeDraft();
    }
    if (event.key === "Backspace" && draft.path.length) {
      event.preventDefault();
      draft.path.pop();
      redrawDraft();
    }
    if (event.key === "Escape") {
      draft.path = [];
      if (draft.line) {
        draft.line.setMap(null);
        draft.line = null;
      }
    }
  });

  if (drawHelp) {
    drawHelp.hidden = false;
    drawHelp.textContent = "Click roof corners · a click within 2 ft snaps to a corner or a side · Enter or double-click to close";
  }

  return {
    kind: "google",
    setView(lat, lng, zoom) {
      googleMap.setCenter({ lat, lng });
      googleMap.setZoom(zoom || TRACE_ZOOM);
      applyCamera();
      if (pin) pin.setMap(null);
      pin = new google.maps.Marker({
        position: { lat, lng },
        map: googleMap,
        title: "Geocoded location",
        opacity: 0.7,
      });
    },
    clear() {
      polygons.splice(0).forEach((poly) => poly.setMap(null));
      clearEdgeLines();
      draft.path = [];
      if (draft.line) {
        draft.line.setMap(null);
        draft.line = null;
      }
      info.close();
    },
    setPolygons(facets) {
      this.clear();
      (facets || []).forEach((facet) => {
        const path = (facet.latlngs || []).map((pt) => ({ lat: pt[0], lng: pt[1] }));
        if (path.length < 3) return;
        const polygon = new google.maps.Polygon({
          paths: path,
          map: googleMap,
          ...stylePoly(),
        });
        polygon.facetPitch = facet.pitch || pitchEl.value;
        polygon.slopeDeg = facet.slope_deg ?? null;
        polygons.push(polygon);
        bindGoogleFacet(polygon);
      });
    },
    setEdges(edges) {
      clearEdgeLines();
      (edges || []).forEach((edge) => {
        const path = (edge.latlngs || []).map((pt) => ({ lat: pt[0], lng: pt[1] }));
        if (path.length < 2) return;
        edgeLines.push(new google.maps.Polyline({
          path,
          map: googleMap,
          strokeColor: EDGE_COLOR[edge.kind] || EDGE_COLOR.unclassified,
          strokeWeight: 4,
          strokeOpacity: 0.95,
          clickable: false,
        }));
      });
    },
    getFacets() {
      return polygons.map((polygon) => {
        const latlngs = polygon.getPath().getArray().map((pt) => [pt.lat(), pt.lng()]);
        return { pitch: polygon.facetPitch || pitchEl.value, slope_deg: polygon.slopeDeg ?? null, latlngs };
      }).filter((facet) => facet.latlngs.length >= 3);
    },
    startDraw() {
      draft.path = [];
      if (draft.line) {
        draft.line.setMap(null);
        draft.line = null;
      }
      statusEl.textContent = "Click the roof corners, then Enter to close";
    },
    setAngle(angle) {
      if (camera.dateId) {
        statusEl.textContent = "Side photos are on Latest Google. The date view stays top-down.";
        return;
      }
      camera.angle = ANGLES[angle] ? angle : "top";
      markAngle(camera.angle);
      applyCamera();
      const label = ANGLES[camera.angle].label;
      window.setTimeout(() => {
        if (camera.angle !== "top" && googleMap.getTilt() < 20) {
          statusEl.textContent = `No ${label} photo here. The top photo still has the run. This side is the rise.`;
          camera.angle = "top";
          markAngle("top");
          applyCamera();
          return;
        }
        statusEl.textContent = `${label} photo. ${ANGLES[camera.angle].note}`;
      }, 500);
    },
    setDate(dateId) {
      camera.dateId = dateId || "";
      if (camera.dateId) {
        camera.angle = "top";
        markAngle("top");
      }
      applyCamera();
      const opt = document.querySelector(`#imagery-date option[value="${CSS.escape(camera.dateId)}"]`);
      statusEl.textContent = camera.dateId
        ? (opt ? opt.textContent : "Older aerial")
        : "Latest Google satellite";
    },
  };
}

let view = null;

function facetsFromMap() {
  return view ? view.getFacets() : [];
}

function setPolygons(facets) {
  if (view) view.setPolygons(facets);
}

function ringKey(latlngs) {
  return JSON.stringify((latlngs || []).map((pt) => [
    Number(pt[0]).toFixed(7),
    Number(pt[1]).toFixed(7),
  ]));
}

function acceptOutlineEdit() {
  if (!state.outlineDraft) return;
  const facets = facetsFromMap();
  if (facets.length && ringKey(facets[0].latlngs) === state.guessRing) return;
  state.outlineDraft = false;
  state.guessRing = "";
  if (facets.length) {
    statusEl.textContent = "Edited. Save when the line sits on the roof edge.";
  }
}

function fmt(n, digits = 1) {
  if (n === null || n === undefined || Number.isNaN(n)) return "—";
  return Number(n).toFixed(digits);
}

function errClass(pct) {
  if (pct === null || pct === undefined) return "";
  return Math.abs(pct) <= 8 ? "ok" : "bad";
}

function renderList() {
  listEl.innerHTML = "";
  state.roofs.forEach((roof) => {
    const div = document.createElement("div");
    div.className = "roof" + (state.current && state.current.id === roof.id ? " active" : "");
    const trace = state.traces[roof.id];
    const err = trace && trace.compare ? trace.compare.area_error_pct : null;
    div.innerHTML = `<div class="addr">${roof.address}</div>
      <div class="meta">${fmt(roof.total_squares, 1)} sq · ${roof.predominant_pitch || "?"} · ${roof.num_facets || "?"} facets
      ${err !== null ? `<span class="err ${errClass(err)}"> ${fmt(err, 1)}%</span>` : roof.traced ? " · saved" : ""}</div>`;
    div.onclick = () => selectRoof(roof.id);
    listEl.appendChild(div);
  });
}

function renderCompare(trace) {
  if (!trace || !trace.summary) {
    compareEl.innerHTML = "";
    return;
  }
  const c = trace.compare || {};
  const s = trace.summary;
  compareEl.innerHTML = `
    <div class="stat"><span>Traced squares</span><b>${fmt(s.total_squares, 2)}</b></div>
    <div class="stat"><span>EagleView squares</span><b>${fmt(c.ev_squares, 2)}</b></div>
    <div class="stat"><span>Area error</span><b class="${errClass(c.area_error_pct)}">${fmt(c.area_error_pct, 1)}%</b></div>
    <div class="stat"><span>Facet Δ</span><b>${fmt(c.facet_count_delta, 0)}</b></div>
    <div class="stat"><span>Ridge</span><b>${fmt(s.ridges_ft, 0)}</b></div>
    <div class="stat"><span>Hip</span><b>${fmt(s.hips_ft, 0)}</b></div>
    <div class="stat"><span>Ridge+hip vs EV</span><b class="${errClass(c.ridges_hips_error_pct)}">${fmt(s.ridges_hips_ft, 0)} / ${fmt(c.ev_ridges_hips_ft, 0)}</b></div>
    <div class="stat"><span>Valley vs EV</span><b class="${errClass(c.valleys_error_pct)}">${fmt(s.valleys_ft, 0)} / ${fmt(c.ev_valleys_ft, 0)}</b></div>
    <div class="stat"><span>Rake vs EV</span><b class="${errClass(c.rakes_error_pct)}">${fmt(s.rakes_ft, 0)} / ${fmt(c.ev_rakes_ft, 0)}</b></div>
    <div class="stat"><span>Eave vs EV</span><b class="${errClass(c.eaves_error_pct)}">${fmt(s.eaves_ft, 0)} / ${fmt(c.ev_eaves_ft, 0)}</b></div>
    <div class="stat"><span>Traced sqft</span><b>${fmt(s.total_area_with_pitch_multiplier_sqft, 0)}</b></div>
    <div class="stat"><span>EV sqft</span><b>${fmt(c.ev_area_sqft, 0)}</b></div>
    ${s.facet_count > 1 && !s.shared_edges ? `<p class="hint">Corners do not meet, so nothing is a ridge or a valley yet.</p>` : ""}
    ${s.facet_count && !s.edges_classified ? `<p class="hint">Click each plane and set which way it drains. The sides are not named until then.</p>` : ""}
    ${s.edges_classified ? `<p class="legend"><i class="swatch ridge"></i> ridge <i class="swatch hip"></i> hip <i class="swatch valley"></i> valley <i class="swatch rake"></i> rake <i class="swatch eave"></i> eave</p>` : ""}
  `;
}

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function preview() {
  if (!state.current) return;
  const payload = {
    id: state.current.id,
    address: state.current.address,
    facets: facetsFromMap(),
    gsd_scale: Number(scaleEl.value),
    waste_pct: Number(wasteEl.value),
  };
  try {
    const trace = await api("/api/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.traces[state.current.id] = trace;
    renderCompare(trace);
    renderList();
    if (view && view.setEdges) view.setEdges((trace.summary && trace.summary.edges) || []);
    const s = trace.summary || {};
    if (facetsFromMap().length && s.edges_classified) {
      statusEl.textContent = `Ridge ${fmt(s.ridges_ft, 0)} · hip ${fmt(s.hips_ft, 0)} · valley ${fmt(s.valleys_ft, 0)} · eave ${fmt(s.eaves_ft, 0)} · rake ${fmt(s.rakes_ft, 0)}`;
    } else if (facetsFromMap().length) {
      statusEl.textContent = "Click each plane and set which way it drains";
    }
  } catch (err) {
    statusEl.textContent = String(err);
  }
}

async function jumpToAddress(query) {
  const q = (query || "").trim();
  if (!q) {
    statusEl.textContent = "Type an address";
    return;
  }
  const listed = state.roofs.find((row) => row.address && row.address.toLowerCase().includes(q.toLowerCase()));
  if (listed) {
    await selectRoof(listed.id);
    return;
  }
  const id = "scratch_" + q.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");
  let roof = state.roofs.find((row) => row.id === id);
  if (!roof) {
    roof = {
      id,
      address: q,
      source_file: "scratch",
      total_squares: null,
      predominant_pitch: "6/12",
      num_facets: null,
      traced: false,
    };
    state.roofs.unshift(roof);
  }
  await selectRoof(roof.id);
}

async function selectRoof(id) {
  const roof = state.roofs.find((row) => row.id === id);
  if (!roof) return;
  state.current = roof;
  state.outlineDraft = false;
  state.guessRing = "";
  pitchEl.value = roof.predominant_pitch && PITCHES.includes(roof.predominant_pitch) ? roof.predominant_pitch : "6/12";
  titleEl.textContent = roof.address;
  metaEl.textContent = roof.source_file === "scratch"
    ? "Not in the EagleView set — draw to get squares. Field-verify before you order."
    : `${fmt(roof.total_squares, 1)} squares · ${roof.predominant_pitch} · ${roof.num_facets} facets · ${roof.source_file}`;
  earthLink.onclick = () => openEarthPro(roof.lat, roof.lng, roof.address);
  renderList();
  statusEl.textContent = "Locating…";
  if (view) view.clear();
  try {
    const loc = await api("/api/locate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address: roof.address }),
    });
    view.setView(loc.lat, loc.lng, TRACE_ZOOM);
    roof.lat = loc.lat;
    roof.lng = loc.lng;
    earthLink.onclick = () => openEarthPro(loc.lat, loc.lng, roof.address);
  } catch (err) {
    statusEl.textContent = "Geocode failed — pan the map yourself";
  }
  try {
    const saved = await fetch(`/api/traces/${roof.id}`);
    if (saved.ok) {
      const trace = await saved.json();
      state.traces[roof.id] = trace;
      setPolygons(trace.facets);
      if (view && view.setEdges) view.setEdges((trace.summary && trace.summary.edges) || []);
      renderCompare(trace);
      statusEl.textContent = "Loaded saved trace — zoom in if you need more detail";
      renderList();
      return;
    }
  } catch (err) {
    // no saved trace
  }
  renderCompare(null);
  if (roof.source_file === "scratch") {
    statusEl.textContent = roof.lat
      ? "Not in the EagleView set — draw the roof to get squares"
      : "Geocode failed — pan the map yourself";
    return;
  }
  statusEl.textContent = view && view.kind === "google"
    ? "Click the roof corners, Enter to close"
    : "Draw the roof (polygon tool, top-right) or Guess outline";
}

async function guessOutline() {
  if (!state.current || !state.current.lat) {
    statusEl.textContent = "Locate the house first";
    return;
  }
  statusEl.textContent = "Asking OSM, then Microsoft footprints…";
  try {
    const data = await api("/api/guess", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ lat: state.current.lat, lng: state.current.lng }),
    });
    if (!data.latlngs) {
      statusEl.textContent = "No building outline there. Draw it.";
      return;
    }
    setPolygons([{ pitch: pitchEl.value, latlngs: data.latlngs }]);
    const facets = facetsFromMap();
    state.guessRing = facets[0] ? ringKey(facets[0].latlngs) : "";
    state.outlineDraft = true;
    await preview();
    const src = data.source === "microsoft" ? "Microsoft footprint" : data.source === "osm" ? "OSM" : "outline";
    statusEl.textContent = "That outline is the building, not the top-view measure. The run is the top photo. The rise is north, south, east, and west.";
  } catch (err) {
    statusEl.textContent = "Guess failed — draw it";
  }
}

async function saveTrace() {
  if (!state.current) return;
  if (state.outlineDraft) {
    statusEl.textContent = "Guess is not saved. Drag a corner onto the roof edge, then Save.";
    return;
  }
  const payload = {
    id: state.current.id,
    address: state.current.address,
    facets: facetsFromMap(),
    gsd_scale: Number(scaleEl.value),
    waste_pct: Number(wasteEl.value),
  };
  try {
    const data = await api("/api/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    state.current.traced = true;
    state.traces[state.current.id] = data.trace;
    renderList();
    renderCompare(data.trace);
    statusEl.textContent = "Saved";
  } catch (err) {
    statusEl.textContent = String(err);
  }
}

async function fitScale() {
  try {
    const data = await api("/api/fit", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
    state.tune = data.current;
    scaleEl.value = data.current.gsd_scale;
    statusEl.textContent = `Scale ${data.current.gsd_scale} from ${data.traced} traces (median |error| ${data.fitted.median_abs_error_pct ?? "—"}%)`;
    preview();
  } catch (err) {
    statusEl.textContent = String(err);
  }
}

scaleEl.addEventListener("change", preview);
wasteEl.addEventListener("change", preview);
document.getElementById("btn-guess").onclick = guessOutline;
document.getElementById("btn-save").onclick = saveTrace;
document.getElementById("btn-fit").onclick = fitScale;
document.getElementById("btn-draw").onclick = () => view && view.startDraw();
document.querySelectorAll("#angles button").forEach((btn) => {
  btn.onclick = () => view && view.setAngle(btn.dataset.angle);
});
const dateEl = document.getElementById("imagery-date");
if (dateEl) {
  dateEl.onchange = () => {
    if (view && view.setDate) view.setDate(dateEl.value);
    document.querySelectorAll("#angles button").forEach((btn) => {
      if (btn.dataset.angle !== "top") btn.disabled = Boolean(dateEl.value);
    });
  };
}
document.getElementById("btn-leafoff").onclick = () => {
  const opt = document.querySelector("#imagery-date option[data-leafoff='1']");
  if (!opt || !dateEl) {
    statusEl.textContent = "No leaf-off date loaded";
    return;
  }
  dateEl.value = opt.value;
  dateEl.onchange();
};
const gotoForm = document.getElementById("goto-form");
if (gotoForm) {
  gotoForm.addEventListener("submit", (event) => {
    event.preventDefault();
    jumpToAddress(document.getElementById("goto").value);
  });
}
document.addEventListener("keydown", (event) => {
  if (event.target.tagName === "INPUT" || event.target.tagName === "SELECT") return;
  const idx = state.roofs.findIndex((row) => state.current && row.id === state.current.id);
  if (event.key === "n" || event.key === "ArrowDown") {
    const next = state.roofs[idx + 1] || state.roofs[0];
    if (next) selectRoof(next.id);
  }
  if (event.key === "p" || event.key === "ArrowUp") {
    const prev = state.roofs[idx - 1] || state.roofs[state.roofs.length - 1];
    if (prev) selectRoof(prev.id);
  }
  if (event.key === "s" && (event.ctrlKey || event.metaKey)) {
    event.preventDefault();
    saveTrace();
  }
});

async function boot() {
  const cfg = await api("/api/config").catch(() => ({}));
  if (cfg.googleMapsKey) {
    try {
      await loadScript(`https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(cfg.googleMapsKey)}&v=weekly`);
      view = initGoogleMap();
    } catch (err) {
      view = initLeafletMap();
    }
  } else {
    view = initLeafletMap();
  }

  const data = await api("/api/roofs");
  state.roofs = data.roofs || [];
  state.tune = data.tune || state.tune;
  scaleEl.value = state.tune.gsd_scale || 1;
  wasteEl.value = state.tune.waste_pct || 12;
  statusEl.textContent = `${state.roofs.length} EagleView roofs · Google satellite`;
  try {
    const dated = await api("/api/imagery-dates");
    const select = document.getElementById("imagery-date");
    (dated.dates || []).forEach((row) => {
      const opt = document.createElement("option");
      opt.value = row.id;
      opt.textContent = row.label;
      if (row.leafOff) opt.dataset.leafoff = "1";
      select.appendChild(opt);
    });
  } catch (err) {
    // latest Google still works
  }
  renderList();
  const want = new URLSearchParams(window.location.search).get("q");
  if (want) {
    const box = document.getElementById("goto");
    if (box) box.value = want;
    await jumpToAddress(want);
  } else if (state.roofs[0]) {
    selectRoof(state.roofs[0].id);
  }
}

boot().catch((err) => {
  statusEl.textContent = String(err);
});
