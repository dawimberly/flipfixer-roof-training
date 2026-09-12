const PITCHES = ["0/12","1/12","2/12","3/12","4/12","5/12","6/12","7/12","8/12","9/12","10/12","11/12","12/12"];

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

PITCHES.forEach((p) => {
  const opt = document.createElement("option");
  opt.value = p;
  opt.textContent = p;
  pitchEl.appendChild(opt);
});

const map = L.map("map", { maxZoom: 22 });
const satellite = L.tileLayer(
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
  { attribution: "Tiles &copy; Esri", maxZoom: 22, maxNativeZoom: 19 }
);
satellite.addTo(map);
map.setView([29.4241, -98.4936], 18);

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

map.on(L.Draw.Event.CREATED, (event) => {
  const layer = event.layer;
  layer.feature = { properties: { pitch: pitchEl.value } };
  drawn.addLayer(layer);
  bindFacet(layer);
  preview();
});
map.on(L.Draw.Event.EDITED, preview);
map.on(L.Draw.Event.DELETED, preview);

function bindFacet(layer) {
  const pitch = (layer.feature && layer.feature.properties.pitch) || pitchEl.value;
  layer.bindPopup(facetPopup(pitch, layer));
  layer.on("popupopen", () => {
    const select = document.getElementById("facet-pitch");
    if (!select) return;
    select.onchange = () => {
      layer.feature.properties.pitch = select.value;
      preview();
    };
  });
}

function facetPopup(pitch) {
  const opts = PITCHES.map((p) => `<option${p === pitch ? " selected" : ""}>${p}</option>`).join("");
  return `Facet pitch <select id="facet-pitch">${opts}</select>`;
}

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function facetsFromMap() {
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
}

function setPolygons(facets) {
  drawn.clearLayers();
  (facets || []).forEach((facet) => {
    const latlngs = (facet.latlngs || []).map((pt) => [pt[0], pt[1]]);
    if (latlngs.length < 3) return;
    const layer = L.polygon(latlngs, { color: "#4da3ff" });
    layer.feature = { properties: { pitch: facet.pitch || pitchEl.value } };
    drawn.addLayer(layer);
    bindFacet(layer);
  });
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

async function preview() {
  if (!state.current) return;
  const payload = {
    id: state.current.id,
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
    statusEl.textContent = err === null || err === undefined ? "Trace started" : `Area error ${fmt(err, 1)}% vs EagleView`;
  } catch (err) {
    statusEl.textContent = String(err);
  }
}

async function selectRoof(id) {
  const roof = state.roofs.find((row) => row.id === id);
  if (!roof) return;
  state.current = roof;
  pitchEl.value = roof.predominant_pitch && PITCHES.includes(roof.predominant_pitch) ? roof.predominant_pitch : "6/12";
  titleEl.textContent = roof.address;
  metaEl.textContent = `${fmt(roof.total_squares, 1)} squares · ${roof.predominant_pitch} · ${roof.num_facets} facets · ${roof.source_file}`;
  earthLink.href = `https://earth.google.com/web/search/${encodeURIComponent(roof.address)}`;
  renderList();
  statusEl.textContent = "Locating…";
  drawn.clearLayers();
  try {
    const loc = await api("/api/locate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ address: roof.address }),
    });
    map.setView([loc.lat, loc.lng], 20);
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
      statusEl.textContent = "Loaded saved trace";
      renderList();
      return;
    }
  } catch (err) {
    // no saved trace
  }
  renderCompare(null);
  statusEl.textContent = "Draw the roof or Guess outline";
}

async function guessOutline() {
  if (!state.current || !state.current.lat) {
    statusEl.textContent = "Locate the house first";
    return;
  }
  statusEl.textContent = "Asking OSM for a building outline…";
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
  } catch (err) {
    statusEl.textContent = "Guess failed — draw it";
  }
}

async function saveTrace() {
  if (!state.current) return;
  const payload = {
    id: state.current.id,
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

api("/api/roofs").then((data) => {
  state.roofs = data.roofs || [];
  state.tune = data.tune || state.tune;
  scaleEl.value = state.tune.gsd_scale || 1;
  wasteEl.value = state.tune.waste_pct || 12;
  statusEl.textContent = `${state.roofs.length} EagleView roofs`;
  renderList();
  if (state.roofs[0]) selectRoof(state.roofs[0].id);
}).catch((err) => {
  statusEl.textContent = String(err);
});
