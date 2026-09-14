"""
Re-run ingest, extract, pair, and write numbers-only defaults.

Safe to run every time a new EagleView or Xactimate lands.

    python retrain.py
    python retrain.py --skip-collect
    python retrain.py --skip-xactimate
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import roof_defaults
import roof_math as rm

ROOT = Path(__file__).resolve().parent
EXTRACTED = ROOT / "extracted"
TRACES_DIR = ROOT / "traces"
DEFAULTS_PUBLIC = ROOT / "roof_defaults.json"
DEFAULTS_PRIVATE = EXTRACTED / "roof_defaults.json"
LOG_PATH = EXTRACTED / "retrain_log.jsonl"
TUNE_PATH = EXTRACTED / "tracer_tune.json"


def run_script(script: str, extra: list[str] | None = None) -> int:
    cmd = [sys.executable, str(ROOT / script), *(extra or [])]
    print(">", " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT)
    return result.returncode


def read_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    frame = pd.read_csv(path)
    return frame


def load_traces() -> list[dict]:
    if not TRACES_DIR.exists():
        return []
    traces = []
    for path in TRACES_DIR.glob("*.json"):
        traces.append(json.loads(path.read_text(encoding="utf-8")))
    return traces


def append_log(payload: dict) -> None:
    EXTRACTED.mkdir(parents=True, exist_ok=True)
    row = {
        "generated_at": payload.get("generated_at"),
        "n_eagleview_reports": payload.get("n_eagleview_reports"),
        "avg_squares": payload.get("avg_squares"),
        "waste_pct": payload.get("waste_pct"),
        "avg_facets": payload.get("avg_facets"),
        "predominant_pitch": payload.get("predominant_pitch"),
        "gsd_scale": payload.get("gsd_scale"),
        "trace_n": payload.get("trace_n"),
        "spread": payload.get("spread"),
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-collect", action="store_true")
    parser.add_argument("--skip-xactimate", action="store_true")
    parser.add_argument("--save-raw-text", action="store_true")
    args = parser.parse_args()

    if not args.skip_collect:
        code = run_script("collect_reports.py")
        if code != 0:
            raise SystemExit(code)

    extract_flags = ["--input_dir", "./reports", "--output_dir", "./extracted"]
    if args.save_raw_text:
        extract_flags.append("--save_raw_text")
    code = run_script("extract_eagleview_data.py", extract_flags)
    if code != 0:
        raise SystemExit(code)

    if not args.skip_xactimate:
        if not args.skip_collect:
            code = run_script("collect_xactimate.py")
            if code != 0:
                raise SystemExit(code)
        code = run_script("extract_xactimate_data.py")
        if code != 0:
            raise SystemExit(code)
        code = run_script("pair_ev_xactimate.py")
        if code != 0:
            raise SystemExit(code)

    ev = read_csv(EXTRACTED / "eagleview_dataset.csv")
    spread = read_csv(EXTRACTED / "roof_bid_spread.csv")
    traces = load_traces()
    payload = roof_defaults.build_payload(ev, spread, traces)
    roof_defaults.write_defaults(payload, DEFAULTS_PRIVATE, DEFAULTS_PUBLIC)
    rm.write_tune(
        TUNE_PATH,
        {
            "gsd_scale": payload.get("gsd_scale") or 1.0,
            "waste_pct": payload.get("waste_pct") or rm.DEFAULT_WASTE_PCT,
            "n": payload.get("trace_n") or 0,
            "median_abs_error_pct": payload.get("median_abs_error_pct"),
            "updated_at": payload.get("generated_at"),
        },
    )
    append_log(payload)

    print("\n--- Retrain ---")
    print(f"EagleView reports: {payload['n_eagleview_reports']}")
    print(f"Avg squares: {payload['avg_squares']}")
    print(f"Waste % (median): {payload['waste_pct']}")
    print(f"Avg facets: {payload['avg_facets']}")
    print(f"Pitch mix: {payload['pitch_mix']}")
    print(f"GSD scale from traces: {payload['gsd_scale']} (n={payload['trace_n']})")
    spread_info = payload["spread"]
    print(
        f"Bid spread properties: {spread_info['properties']} "
        f"({spread_info['with_2plus_tickets']} with 2+ tickets)"
    )
    if spread_info.get("median_code_minus_carrier") is not None:
        print(f"Median code minus carrier: {spread_info['median_code_minus_carrier']}")
    print(spread_info["note"])
    print(DEFAULTS_PUBLIC)
    print(f"Ran at {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print("Drop more PDFs and run python retrain.py again.")


if __name__ == "__main__":
    main()
