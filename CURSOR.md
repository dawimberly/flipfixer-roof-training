# Cursor — ingest EagleView PDFs from this machine

You are working in `dawimberly/flipfixer-roof-training`.

## Job

1. Search the user's Desktop, Downloads, Documents, and OneDrive Desktop for PDFs whose names look like EagleView / roof measurement reports.
2. Copy them into `reports/` in this repo. Do not delete originals. Do not git-add the PDFs.
3. Run:

```
pip install -r requirements.txt
python collect_reports.py
python extract_eagleview_data.py --input_dir ./reports --output_dir ./extracted --save_raw_text
```

4. If fields come back missing, open the matching `extracted/*_raw.txt`, tighten the regex in `extract_eagleview_data.py`, and rerun.
5. Commit only code and `extracted/eagleview_dataset.csv` / `.json` if the user wants numbers in git. Never commit PDFs or raw text that still has full client addresses unless they say so.

## What we keep

Numbers only: total area, squares, pitch, facet count, ridges, valleys, rakes, eaves, waste %. That is the training set for The Flip Fixer roof tracer.

## What we do not keep

EagleView page layout, logos, or branded report language. Do not reproduce their design.
