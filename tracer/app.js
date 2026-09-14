const PITCHES = ["0/12","1/12","2/12","3/12","4/12","5/12","6/12","7/12","8/12","9/12","10/12","11/12","12/12"];
const TRACE_ZOOM = 21;

const state = {
  roofs: [],
  tune: { gsd_scale: 1, waste_pct: 12 },
  current: null,
  traces: {},
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

function facetPopupHtml(pitch) {
  const opts = PITCHES.map((p) => `<option${p === pitch ? " selected" : ""}>${p}</option>`).join("");
  return `Facet pitch <select id="facet-pitch">${opts}</select>`;
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
    drawHelp.textContent = "Use Draw facet or the polygon tool. Scroll to zoom — Google satellite goes to rooftop.";
  }

  const drawn = new L.FeatureGroup();
  map.addLayer(drawn);
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
  map.on(L.Draw.Event.CREATED, (event) => {
    const layer = event.layer;
    layer.feature = { properties: { pitch: pitchEl.value } };
    drawn.addLayer(layer);
    bindLeafletFacet(layer);
    preview();
  });
  map.on(L.Draw.Event.EDITED, preview);
  map.on(L.Draw.Event.DELETED, preview);

  function bindLeafletFacet(layer) {
    const pitch = (layer.feature && layer.feature.properties.pitch) || pitchEl.value;
    layer.bindPopup(facetPopupHtml(pitch));
    layer.on("popupopen", () => {
      const select = document.getElementById("facet-pitch");
      if (!select) return;
      select.onchange = () => {
        layer.feature.properties.pitch = select.value;
        preview();
      };
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
    },
    setPolygons(facets) {
      drawn.clearLayers();
      (facets || []).forEach((facet) => {
        const latlngs = (facet.latlngs || []).map((pt) => [pt[0], pt[1]]);
        if (latlngs.length < 3) return;
        const layer = L.polygon(latlngs, { color: "#4da3ff" });
        layer.feature = { properties: { pitch: facet.pitch || pitchEl.value } };
        drawn.addLayer(layer);
        bindLeafletFacet(layer);
      });
    },
    getFacets() {
      const facets = [];
      drawn.eachLayer((layer) => {
        if (!layer.getLatLngs) return;
        const ring = layer.getLatLngs()[0] || [];
        const latlngs = ring.map((pt) => [pt.lat, pt.lng]);
        if (latlngs.length < 3) return;
        facets.push({
          pitch: (layer.feature && layer.feature.properties.pitch) || pitchEl.value,
          latlngs,
        });
      });
      return facets;
    },
    startDraw() {
      new L.Draw.Polygon(map, drawControl.options.draw.polygon).enable();
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
  const info = new google.maps.InfoWindow();
  let pin = null;
  const draft = { path: [], line: null };

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

  function bindGoogleFacet(polygon) {
    polygon.addListener("click", () => {
      const pitch = polygon.facetPitch || pitchEl.value;
      info.setContent(facetPopupHtml(pitch));
      info.setPosition(polygon.getPath().getAt(0));
      info.open(googleMap);
      google.maps.event.addListenerOnce(info, "domready", () => {
        const select = document.getElementById("facet-pitch");
        if (!select) return;
        select.onchange = () => {
          polygon.facetPitch = select.value;
          preview();
        };
      });
    });
    const path = polygon.getPath();
    path.addListener("set_at", preview);
    path.addListener("insert_at", preview);
    path.addListener("remove_at", preview);
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
    draft.path.push(event.latLng);
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
    drawHelp.textContent = "Click roof corners · Enter or double-click to close · Backspace undoes a point";
  }

  return {
    kind: "google",
    setView(lat, lng, zoom) {
      googleMap.setOptions({ tilt: 0, heading: 0 });
      googleMap.setCenter({ lat, lng });
      googleMap.setZoom(zoom || TRACE_ZOOM);
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
        polygons.push(polygon);
        bindGoogleFacet(polygon);
      });
    },
    getFacets() {
      return polygons.map((polygon) => {
        const latlngs = polygon.getPath().getArray().map((pt) => [pt.lat(), pt.lng()]);
        return { pitch: polygon.facetPitch || pitchEl.value, latlngs };
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
  };
}

let view = null;

function facetsFromMap() {
  return view ? view.getFacets() : [];
}

function setPolygons(facets) {
  if (view) view.setPolygons(facets);
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
    <div class="stat"><span>Traced sqft</span><b>${fmt(s.total_area_with_pitch_multiplier_sqft, 0)}</b></div>
    <div class="stat"><span>EV sqft</span><b>${fmt(c.ev_area_sqft, 0)}</b></div>
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
    const err = trace.compare && trace.compare.area_error_pct;
    if (facetsFromMap().length) {
      statusEl.textContent = err === null || err === undefined ? "Trace started" : `Area error ${fmt(err, 1)}% vs EagleView`;
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
  pitchEl.value = roof.predominant_pitch && PITCHES.includes(roof.predominant_pitch) ? roof.predominant_pitch : "6/12";
  titleEl.textContent = roof.address;
  metaEl.textContent = roof.source_file === "scratch"
    ? "Not in the EagleView set — draw to get squares. Field-verify before you order."
    : `${fmt(roof.total_squares, 1)} squares · ${roof.predominant_pitch} · ${roof.num_facets} facets · ${roof.source_file}`;
  earthLink.href = `https://earth.google.com/web/search/${encodeURIComponent(roof.address)}`;
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
  } catch (err) {
    statusEl.textContent = "Geocode failed — pan the map yourself";
  }
  try {
    const saved = await fetch(`/api/traces/${roof.id}`);
    if (saved.ok) {
      const trace = await saved.json();
      state.traces[roof.id] = trace;
      setPolygons(trace.facets);
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
    await preview();
    const src = data.source === "microsoft" ? "Microsoft footprint" : data.source === "osm" ? "OSM" : "outline";
    const err = state.traces[state.current.id] && state.traces[state.current.id].compare
      ? state.traces[state.current.id].compare.area_error_pct
      : null;
    const errBit = err === null || err === undefined ? "" : ` · area error ${fmt(err, 1)}% vs EagleView`;
    statusEl.textContent = `${src} (house outline, not roof facets)${errBit}`;
  } catch (err) {
    statusEl.textContent = "Guess failed — draw it";
  }
}

async function saveTrace() {
  if (!state.current) return;
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
