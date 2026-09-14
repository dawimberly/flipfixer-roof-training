# Flip Fixer — roof training lab

Private kit for turning a pile of EagleView PDFs and the Xactimates that sit with them into a number set The Flip Fixer can learn from.

The reports stay on your machine. Git ignores `reports/`, `xactimate/`, `*.pdf`, and `*.esx`. We keep the measurements and the bid spread — not a blended “mid.”

Repo: https://github.com/dawimberly/flipfixer-roof-training

See `SOURCES.md` for the estimator (`apps/site`), legacy marketing site, Vercel URLs, and what still lives only on the shop PC.

## What Cursor should do

Open this repo. Paste `CURSOR.md` as the task. It scans Desktop / Downloads / Documents, copies matching PDFs, then extracts and pairs.

Or do it yourself:

```bash
git clone https://github.com/dawimberly/flipfixer-roof-training.git
cd flipfixer-roof-training
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python collect_reports.py
python extract_eagleview_data.py --save_raw_text
python collect_xactimate.py
python extract_xactimate_data.py --save_raw_text
python pair_ev_xactimate.py
```

If the filenames are just `Report.pdf` and `Scan (3).pdf`, point Cursor at the folders you know:

```bash
python collect_reports.py --roots "C:/Users/YOU/Desktop" "C:/Users/YOU/Downloads"
```

Then, if collect skipped them because the name was bland, copy the PDFs into `reports/` by hand and run extract anyway.

## Business rule

One roof can have several Xactimates. Insurance writes coverage. The house needs code for that zip. The high ticket is usually the code ticket, not the carrier ticket. Never average them. The software should argue like that.

## Outputs

| File | What it is |
| --- | --- |
| `extracted/eagleview_dataset.csv` | One row per EagleView report |
| `extracted/eagleview_dataset.json` | Same rows, for the tracer |
| `extracted/xactimate_dataset.csv` | One row per Xactimate / ESX file |
| `extracted/paired_ev_xactimate.csv` | One row per XM, joined to its EagleView |
| `extracted/roof_bid_spread.csv` | One row per property: carrier vs code, no mid |
| `extracted/*_raw.txt` | Debug dump if a regex misses |

Use the averages (waste %, pitch mix, facet count) as defaults on `/exterior` in `the-flip-fixer`. Use the spread when you talk price. Field-verify before you order.

## Rules

- Do not commit PDFs, ESX, raw text with names, or `.env`.
- Do not store EagleView or Xactimate branded layout.
- Do not invent a recommended mid.
- Field-verify before you order materials. This set trains a preliminary number, not a lumber ticket.
