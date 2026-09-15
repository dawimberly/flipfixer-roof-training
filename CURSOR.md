# Cursor / agent task — roof training lab

You are working in `dawimberly/flipfixer-roof-training` on branch `cursor/ev-xactimate-satellite-tracer`. Do not start a new architecture. Extend what is here.

Read `README.md` first.

## Priority work

Build / improve an **automatic** roof measure that produces **ridge, hip, valley, rake, eave** (and squares) and scores them against EagleView line totals in `extracted/eagleview_dataset.csv`.

### Geometry

- Roof = triangles (facets), not a building-footprint box.
- Each facet: plan ring + pitch + `slope_deg` (drain bearing, 0 north, 90 east).
- Ridge / eave = plan length. Rake / hip / valley = √(plan² + rise²). Shared sides once.
- Do not paste EagleView lengths as the measurement. Report = answer key after independent measure.
- Squares-only footprint match is not a pass (area can cancel while sides are wrong).

### Photos

- Top holds the **run**. Profile (along the ridge) holds the **rise**. Facing view holds drain.
- Simple gable: ridge + run from top, rise from one profile — enough. You do **not** usually need all four corners on all five photos.
- Looking in Earth Pro / Earth web is allowed. **Do not scrape tiles.**

### Key files

| File | Role |
| --- | --- |
| `roof_math.py` | Area, `classify_edges`, summarize, compare to EV |
| `roof_views.py` | Which view holds run vs rise; `pitch_from_profile` |
| `sop_score.py` | Score a JSON measure against EV lines |
| `serve_tracer.py` + `tracer/` | Local draw UI at http://127.0.0.1:8765 |
| `test_roof_math.py` | Gable / hip / valley length tests |
| `backtest_parcel.py` | Parcel footprint squares — **not** the side-line test |

### Commands

```bash
pip install -r requirements.txt
python -m pytest test_roof_math.py -q
python serve_tracer.py
python sop_score.py extracted/sop_five.json
```

`extracted/` is gitignored. Create local SOP JSON from Earth looks when needed.

### Five-roof SOP (in progress)

Addresses used: Crooked Path, Spring Rain, Meadow Lawn, Harpers Ferry, Rebeccas Trail (San Antonio). Spring Rain, Meadow Lawn, and Harpers scored lines are in the envelope. Harpers step 50 vs 57 is recorded in `extracted/sop_pass_note.txt` — do not invent the last feet. Crooked Path / Rebeccas parked. Do not commit unless asked.

---

## Also: ingest EagleView + Xactimate

### Business rule

One roof can have several Xactimates. Insurance writes coverage. The house needs code for that zip. Jon’s high bid is usually the code ticket, not the carrier ticket. Never average them. Do not invent a recommended mid. The spread is the product.

### EagleView

1. Search Desktop / Downloads / Documents / OneDrive for EagleView / roof-measurement PDFs.
2. Copy into `reports/`. Do not delete originals. Do not git-add the PDFs.
3. Run:

```
pip install -r requirements.txt
python collect_reports.py
python extract_eagleview_data.py --input_dir ./reports --output_dir ./extracted --save_raw_text
```

4. If fields come back missing, open the matching `extracted/*_raw.txt`, tighten the regex in `extract_eagleview_data.py`, and rerun.

### Xactimate (one EV → many tickets)

```
python collect_xactimate.py
python extract_xactimate_data.py --save_raw_text
python pair_ev_xactimate.py
```

- Extract per file: address, estimate date, claim/estimate number, squares, shingle type, tear-off, felt, ice & water, ridge, drip, steep, decking, O&P, grand total, and notes that smell like supplement vs original.
- Join on normalized address. One EV row → many XM rows.
- Classify each XM as `carrier` or `code` only when clear. If you cannot tell, `role=unknown`.
- Write `extracted/paired_ev_xactimate.csv` and `extracted/roof_bid_spread.csv`.

## What we keep

Numbers only. EagleView: area, squares, pitch, facets, ridges, valleys, rakes, eaves, waste %. Xactimate: fields above + carrier/code spread. Independent measure scores against those EV line totals.

## What we do not keep

EagleView or Xactimate page layout, logos, or branded report language. Do not commit PDFs, ESX, raw text with names, or `.env`. Do not scrape map tiles.
