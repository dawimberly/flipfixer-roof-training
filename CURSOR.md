# Cursor — ingest EagleView and Xactimate from this machine

You are working in `dawimberly/flipfixer-roof-training` on the current branch. Do not start a new architecture. Extend what is here.

## Business rule

One roof can have several Xactimates. That is normal. Insurance writes coverage. The house needs code for that zip. Jon’s high bid is usually the code ticket, not the carrier ticket. Never average them. Do not invent a recommended mid. The spread is the product.

## EagleView

1. Search Desktop / Downloads / Documents / OneDrive for EagleView / roof-measurement PDFs.
2. Copy into `reports/`. Do not delete originals. Do not git-add the PDFs.
3. Run:

```
pip install -r requirements.txt
python collect_reports.py
python extract_eagleview_data.py --input_dir ./reports --output_dir ./extracted --save_raw_text
```

4. If fields come back missing, open the matching `extracted/*_raw.txt`, tighten the regex in `extract_eagleview_data.py`, and rerun.

## Xactimate (one EV → many tickets)

Keep collecting Xactimate PDFs / ESX into `xactimate/`. Gitignore that folder and `*.esx`. Do not commit estimates.

```
python collect_xactimate.py
python extract_xactimate_data.py --save_raw_text
python pair_ev_xactimate.py
```

- Extract per file: address, estimate date, claim/estimate number, squares, shingle type, tear-off, felt, ice & water, ridge, drip, steep, decking, O&P, grand total, and notes that smell like supplement vs original.
- Join on normalized address (city/zip if the street repeats). One EV row → many XM rows.
- Classify each XM as `carrier` or `code` only when the signals are clear. Lower total + missing code lines = carrier. Higher total + ice/water, drip, steep, decking, city-required underlayment = code. If you cannot tell, leave `role=unknown`. Do not guess to look smart.
- Write `extracted/paired_ev_xactimate.csv` (one row per XM) and `extracted/roof_bid_spread.csv` (one row per property: EV squares/pitch/facets, carrier_total, code_total, delta, xm_count, role_guess_notes).

If extract fields are empty, open raw text, tighten regex, rerun. Report hit rates. When you finish: how many XM files, how many unique addresses, how many EV addresses got 2+ tickets, median carrier vs code delta.

## What we keep

Numbers only. EagleView: area, squares, pitch, facets, ridges, valleys, rakes, eaves, waste %. Xactimate: the fields above, plus the carrier/code spread. That set trains The Flip Fixer roof tracer and bid argument.

## What we do not keep

EagleView or Xactimate page layout, logos, or branded report language. Do not reproduce their design. Do not commit PDFs, ESX, raw text with names, or `.env`.
