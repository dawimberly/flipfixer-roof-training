# The Flip Fixer

Private home for the shop: live site + estimator under `apps/site`, roof training lab at the repo root.

**Repo:** https://github.com/dawimberly/flipfixer-roof-training  
**Live site:** https://theflipfixer.com (still deploys from `dawimberly/flpfxr` on Vercel until you point that project here)

EagleView PDFs, Xactimates, keys, recovery codes, HEIC/zip piles, and friend-pool estimates stay **off GitHub**. Do not delete those local originals.

## Layout

| Path | What it is |
| --- | --- |
| `apps/site` | Snapshot of [flpfxr](https://github.com/dawimberly/flpfxr) — marketing site + employee estimator. iOS/Android tap-to-call is on `cursor/fix-ios-android-call-buttons` in that repo. |
| Root (`collect_*.py`, `tracer/`, `retrain.py`) | Roof lab: EagleView + Xactimate ingest, pairing, satellite tracer. |
| [flpfxr-archive](https://github.com/dawimberly/flpfxr-archive) | Shop file cabinet (ads, how-tos, brand, job notes, cabinetry PDFs). Not copied here. |
| [flipfixer](https://github.com/dawimberly/flipfixer) | Older Nuxt site. Not revived. |

This cloud token still cannot clone `flpfxr-archive`, `the-flip-fixer`, or `flipfixer-estimator`. `apps/site` is the estimator that was already inside `flpfxr`.

## Roof lab

Open this repo. Paste `CURSOR.md` as the task. It scans Desktop / Downloads / Documents, copies matching PDFs, then extracts and pairs. Do not treat archive ads or cabinetry PDFs as EagleViews.

Or do it yourself:

```bash
git clone https://github.com/dawimberly/flipfixer-roof-training.git
cd flipfixer-roof-training
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python collect_reports.py
python collect_xactimate.py
python collect_photos.py
python extract_eagleview_data.py --save_raw_text
python extract_xactimate_data.py --save_raw_text
python pair_ev_xactimate.py
python bundle_projects.py
```

Keep retraining. Drop more PDFs and run the same loop:

```bash
python retrain.py
```

That collect / extract / pairs / bundles again, then writes `roof_defaults.json` (waste %, pitch mix, facet count, GSD scale, project photo counts). Bid files still keep carrier vs code as a spread — they are never averaged into a mid. Photos stay on disk; git only keeps the index.

If the filenames are just `Report.pdf` and `Scan (3).pdf`, point Cursor at the folders you know:

```bash
python collect_reports.py --roots "C:/Users/YOU/Desktop" "C:/Users/YOU/Downloads"
```

Then, if collect skipped them because the name was bland, copy the PDFs into `reports/` by hand and run extract anyway.

## Site + estimator

```bash
cd apps/site
cp .env.example .env   # local secrets only; never commit .env
npm install
npm run dev            # http://localhost:8080
```

Tap-to-call for iPhone/Android PWA is on `flpfxr` branch `cursor/fix-ios-android-call-buttons` (commit `e8bf92b`). Production Vercel still tracks `flpfxr` main.

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
| `extracted/project_bundles.csv` | One job: EagleView + tickets + photo counts, keyed by address or name |
| `roof_defaults.json` | Numbers-only snapshot for `/exterior` (safe to commit; no addresses) |

Use the averages (waste %, pitch mix, facet count) as defaults on `/exterior` in `the-flip-fixer`. Use the spread when you talk price. Field-verify before you order.

## Rules

- Do not commit EagleView/Xactimate PDFs, ESX, raw text with names, or `.env`.
- Site brand assets under `apps/site/public` are already in git.
- Do not store EagleView or Xactimate branded layout.
- Do not invent a recommended mid.
- Field-verify before you order materials. This set trains a preliminary number, not a lumber ticket.
