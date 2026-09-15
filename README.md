# Flip Fixer — roof training lab

Private kit for turning EagleView PDFs and the Xactimates that sit with them into a number set The Flip Fixer can learn from — and for building an automatic roof measure that scores against EagleView **line totals** (ridge, hip, valley, rake, eave), not a footprint-box area match.

The reports stay on your machine. Git ignores `reports/`, `xactimate/`, `extracted/`, `*.pdf`, and `*.esx`. We keep the measurements and the bid spread — not a blended “mid.”

Repo: https://github.com/dawimberly/flipfixer-roof-training  
Branch for current tracer / measure work: `cursor/ev-xactimate-satellite-tracer`

## What this repo is for

1. **Ingest** — collect EagleView + Xactimate PDFs, extract numbers, pair carrier vs code tickets.
2. **Measure** — independent roof geometry from photos (top + side), then score ridge / hip / valley / rake / eave against the EagleView row.
3. **Tracer** — local web UI to draw facets on satellite imagery and classify edges.

Do **not** scrape Google Earth tiles (TOS). Looking in Earth Pro / Earth web is fine. Do **not** paste EagleView lengths as the measurement (the report is the answer key after an independent measure). Do **not** chase 1% accuracy or add a paid AI API for this lab.

## Model (read this first)

A roof is **triangles**, not a building-footprint box.

- Ridge, rake, eave, valley, and hip are **sides of those triangles**.
- Each facet has its own **pitch** and **drain** (`slope_deg`: compass bearing water runs, 0 = north, 90 = east).
- A **ridge** and an **eave** are level → plan length = roof length.
- A **rake**, **hip**, and **valley** are hypotenuses → √(plan² + rise²). A hip is **not** plan × pitch factor.
- Shared sides counted once. Do not reapply pitch factor to already-sloped EV area.
- Area can land close by cancellation while missing the sides — squares-only is not a pass.

### Photos

Five views help: **top, north, south, east, west**.

- **Top** holds the **run** (plan length of sides and where planes meet).
- A **profile** (looking along the ridge) holds the **rise**.
- A **facing** view shows which way a plane drains.

A **simple gable** does **not** need four corners on every photo. Ridge + run from top, rise from one profile, is enough. More corners / more views help on complex roofs; they are not a gate for a simple one.

Operator order when you *do* register carefully: open the views → mark the same corners on top and sides → only then mark sides between corners → pitch = rise/run in that shared grid. A footprint on the top photo alone skips registration.

## Setup

```bash
git clone https://github.com/dawimberly/flipfixer-roof-training.git
cd flipfixer-roof-training
git checkout cursor/ev-xactimate-satellite-tracer
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

PowerShell: use `;` not `&&`.

## Ingest (EagleView + Xactimate)

Paste `CURSOR.md` as the task, or:

```bash
python collect_reports.py
python extract_eagleview_data.py --save_raw_text
python collect_xactimate.py
python extract_xactimate_data.py --save_raw_text
python pair_ev_xactimate.py
```

### Business rule

One roof can have several Xactimates. Insurance writes coverage. The house needs code for that zip. The high ticket is usually the code ticket. **Never average them.**

### Outputs (local under `extracted/`, gitignored)

| File | What it is |
| --- | --- |
| `eagleview_dataset.csv` | One row per EagleView report |
| `xactimate_dataset.csv` | One row per Xactimate / ESX |
| `paired_ev_xactimate.csv` | One XM row joined to its EagleView |
| `roof_bid_spread.csv` | Carrier vs code per property, no mid |
| `sop_five.json` / `sop_five_score.csv` | Five-roof SOP scores (local) |

## Tracer (draw facets)

```bash
python serve_tracer.py
# open http://127.0.0.1:8765
```

- Guess building = OSM / Microsoft footprint draft (not the roof).
- Draw facets with pitch + drain direction.
- Edge overlay names ridge / hip / valley / rake / eave from the triangles.
- NSEW buttons tilt the camera; they do not by themselves register corners across photos.

## Roof math

```bash
python -m pytest test_roof_math.py -q
# or: python test_roof_math.py
```

Core module: `roof_math.py` — pitch multipliers, facet area, `classify_edges`, `summarize_facets`, `compare_to_eagleview`.

Views helper: `roof_views.py` — which photo holds run vs rise; `pitch_from_profile(rise, run)`.

## SOP score (independent measure vs EagleView lines)

Build a JSON list of roofs with `origin`, `views_registered` (`top` + at least a profile or pitches set), and `facets` (plan feet or latlngs, pitch, `slope_deg`). Then:

```bash
python sop_score.py extracted/sop_five.json
```

Scoring gate: top + (profile view **or** pitches already set) + facets. Not “all five views or fail.”

Helpers (Earth screenshots you already captured — not tile scrapes):

- `sop_grid.py` — ft/px grid on a top screenshot from camera height
- `sop_camera.py` — parse settled Earth URLs; project plan ↔ side
- `sop_edges.py` — exploratory edge/mask helpers (top photo)

### Current five-roof check (local)

San Antonio span: Crooked Path, Spring Rain, Meadow Lawn, Harpers Ferry, Rebeccas Trail.

As of the last pass: **Spring Rain**, **Meadow Lawn**, and **Harpers Ferry** scored lines are in the envelope. Harpers step is 50.1 vs EV 57; the missing feet are not on the rings (see `extracted/sop_pass_note.txt`). Crooked Path and Rebeccas Trail are not registered.

Parcel / footprint backtests (`backtest_parcel.py`, `backtest_footprints.py`) score **squares from one ring**. That is **not** the test of the triangle measure. Do not treat a squares-only box match as a pass.

## Rules

- Do not commit PDFs, ESX, raw extract text with names, or `.env`.
- Do not store EagleView or Xactimate branded layout.
- Do not invent a recommended mid.
- Do not scrape Earth / Maps tiles.
- Field-verify before you order materials.

## For Grok / Claude / other agents

1. Checkout `cursor/ev-xactimate-satellite-tracer`.
2. Read this README and `CURSOR.md`.
3. Extend what is here — do not start a new architecture.
4. Prefer scoring **ridge / hip / valley / rake / eave** against `eagleview_dataset.csv`.
5. Simple roofs: ridge + run + rise. Complex roofs: more facets, same math.
6. Do not commit unless asked. Do not push secrets.
