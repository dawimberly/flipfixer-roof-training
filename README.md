# Flip Fixer — roof training lab

Private kit for turning a pile of EagleView PDFs into a number set The Flip Fixer can learn from.

The reports stay on your machine. Git ignores `reports/` and `*.pdf`. We keep the measurements: squares, pitch, facets, ridges, valleys, eaves, waste.

Repo: https://github.com/dawimberly/flipfixer-roof-training

## What Cursor should do

Open this repo. Paste `CURSOR.md` as the task. It scans Desktop / Downloads / Documents, copies matching PDFs into `reports/`, then runs the extractor.

Or do it yourself:

```bash
git clone https://github.com/dawimberly/flipfixer-roof-training.git
cd flipfixer-roof-training
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python collect_reports.py
python extract_eagleview_data.py --save_raw_text
```

If the filenames are just `Report.pdf` and `Scan (3).pdf`, point Cursor at the folders you know:

```bash
python collect_reports.py --roots "C:/Users/YOU/Desktop" "C:/Users/YOU/Downloads"
```

Then, if collect skipped them because the name was bland, copy the PDFs into `reports/` by hand and run extract anyway.

## Outputs

| File | What it is |
| --- | --- |
| `extracted/eagleview_dataset.csv` | One row per report |
| `extracted/eagleview_dataset.json` | Same rows, for the tracer |
| `extracted/*_raw.txt` | Debug dump if a regex misses |

Use the averages (waste %, pitch mix, facet count) as defaults on `/exterior` in `the-flip-fixer`.

`roof_math.trace_sanity` is a 1-story smell test: living + garage, a drip-edge band, then pitch. A ~1,700 sq ft ranch with a 2-car garage should land in the mid-20s squares, not 39.

The usual way to get 39 on a house that size: take living area, apply pitch, **count both slopes as the full plan**, then add 12% waste. Pitch already converts plan to slope — one drip-edge outline is enough. `diagnose_measured_squares(39, 1673, 620)` spells that out.

## Rules

- Do not commit PDFs.
- Do not store EagleView's branded layout.
- Field-verify before you order materials. This set trains a preliminary number, not a lumber ticket.
