# Flip Fixer sources gathered in this environment

This branch brings the **employee estimator**, **roof measurement lab**, and **satellite tracer** into one checkout so Cloud Agent work can see them together.

## What is here

| Path | Source | Role |
| --- | --- | --- |
| `apps/site/` | [dawimberly/flpfxr](https://github.com/dawimberly/flpfxr) (live) | Marketing site + employee login + kitchen/bath estimator. Deployed on Vercel as project `flpfxr` (Dirty INK) → [theflipfixer.com](https://theflipfixer.com) |
| `apps/legacy-flipfixer/` | [dawimberly/flipfixer](https://github.com/dawimberly/flipfixer) | Older Nuxt marketing site. `https://flipfixer.vercel.app` is dead |
| `apps/legacy-westwick-flipfixer/` | [westwick/flipfixer](https://github.com/westwick/flipfixer) | Earlier public Nuxt copy (large gallery originals) |
| Repo root + `tracer/` | this repo, branch `cursor/ev-xactimate-satellite-tracer` | EagleView / Xactimate extractors, pairing, `serve_tracer.py` satellite roof tracer |
| `flip_folders.py`, `retrain.py`, `bundle_projects.py`, … | consolidation branch | Folder discovery and retrain helpers |

Estimator entry points in `apps/site/`:

- `src/routes/estimator.tsx`, `src/routes/login.tsx`
- `src/components/estimator-app.tsx`, `quote-estimator.tsx`, `estimate-rail.tsx`, `estimate-log.tsx`
- `src/lib/estimator.ts`, `estimator-store.ts`, `estimate-pdf.ts`
- `migrations/0002_estimator_jobs.sql`

Roof measurement / tracer:

- `collect_reports.py`, `extract_eagleview_data.py`
- `collect_xactimate.py`, `extract_xactimate_data.py`, `pair_ev_xactimate.py`
- `roof_math.py`, `roof_facets_schema.json`
- `serve_tracer.py`, `tracer/index.html`, `tracer/app.js`, `tracer/style.css`

## Live Vercel

- **Live:** `https://theflipfixer.com` and `https://flpfxr.vercel.app` (same `flpfxr` project)
- **Dead:** `https://flipfixer.vercel.app`, `https://flipfixer-roof-training.vercel.app`
- This Cloud Agent has **no Vercel CLI token**, so dashboard project dumps were not pulled. GitHub `flpfxr` is the source of the live estimator.

## Not available in this VM

Cloud Agents cannot see the shop PC. These stay local until you copy or grant repo access:

| Location | What |
| --- | --- |
| `C:\Users\Owner\Flip Fixer\flipfixer-roof-training` | Working lab with `reports/` and `xactimate/` |
| `C:\Users\Owner\OneDrive\Desktop\Roofing Documents\MRC\` | EagleView / job pile |
| Desktop / Downloads / Documents / OneDrive copies named Flip Fixer, flpfx, etc. | Extra folder copies |
| [dawimberly/the-flip-fixer](https://github.com/dawimberly/the-flip-fixer) | Named by you; GitHub token gets 404 |
| [dawimberly/flipfixer-estimator](https://github.com/dawimberly/flipfixer-estimator) | Named by you; GitHub token gets 404 |
| [dawimberly/flpfxr-archive](https://github.com/dawimberly/flpfxr-archive) | Shop notes/ads; GitHub token gets 404 |
| MRC Gmail `dan.myroofco@gmail.com` | Attachments not readable here |

Extra clones also live at `/home/ubuntu/flipfixer-sources/` (`flpfxr`, `flipfixer`, `westwick-flipfixer`, `roof-training-tracer` worktree).

## Run locally in this environment

```bash
# roof lab
pip install -r requirements.txt
python -m unittest test_roof_math.py test_pair_ev_xactimate.py test_geocode_tidy.py
python serve_tracer.py   # satellite tracer, typically :8080

# estimator / site
cd apps/site
npm install
npm run dev              # Vite on :8080 per package.json
```

Do not commit PDFs, ESX files, or `.env` secrets. Production still deploys from `dawimberly/flpfxr`, not from this vendored copy, until you change that on purpose.
