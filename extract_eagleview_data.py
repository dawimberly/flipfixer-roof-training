"""
Pull numbers out of a folder of EagleView PDFs.
Writes CSV/JSON for tracer validation. Does not store branded page design.

    python extract_eagleview_data.py --input_dir ./reports --output_dir ./extracted --save_raw_text
"""

import argparse
import re
from pathlib import Path

import pandas as pd
import pdfplumber

PATTERNS = {
    "total_roof_area_sqft": r"Total\s+Area\s*[:\-]?\s*([\d,]+)\s*sq\s*ft",
    "total_squares": r"Total\s+Squares?\s*[:\-]?\s*([\d.]+)",
    "predominant_pitch": r"Predominant\s+Pitch\s*[:\-]?\s*(\d+/\d+)",
    "num_facets": r"Number\s+of\s+Facets\s*[:\-]?\s*(\d+)",
    "total_ridges_ft": r"Total\s+Ridges?\s*[/,]?\s*Hips?\s*[:\-]?\s*([\d,]+)\s*ft",
    "total_valleys_ft": r"Total\s+Valleys?\s*[:\-]?\s*([\d,]+)\s*ft",
    "total_rakes_ft": r"Total\s+Rakes?\s*[:\-]?\s*([\d,]+)\s*ft",
    "total_eaves_ft": r"Total\s+Eaves?\s*[/,]?\s*Starter\s*[:\-]?\s*([\d,]+)\s*ft",
    "waste_table_pct": r"(\d{1,2})%\s*Waste",
    "address": r"(?:Property\s+Address|Address)\s*[:\-]?\s*(.+)",
}


def extract_text(pdf_path: Path) -> str:
    parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
    return "\n".join(parts)


def parse_fields(text: str) -> dict:
    result = {}
    for field, pattern in PATTERNS.items():
        match = re.search(pattern, text, re.IGNORECASE)
        result[field] = match.group(1).strip() if match else None
    return result


def clean_numeric(value):
    if value is None:
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", default="./reports")
    parser.add_argument("--output_dir", default="./extracted")
    parser.add_argument("--save_raw_text", action="store_true")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(input_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDFs in {input_dir}. Drop reports there, then run again.")
        return

    rows = []
    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")
        try:
            text = extract_text(pdf_path)
        except Exception as exc:
            print(f"  FAILED: {exc}")
            continue

        if args.save_raw_text:
            (output_dir / f"{pdf_path.stem}_raw.txt").write_text(text, encoding="utf-8")

        fields = parse_fields(text)
        fields["source_file"] = pdf_path.name
        for key in (
            "total_roof_area_sqft",
            "total_squares",
            "num_facets",
            "total_ridges_ft",
            "total_valleys_ft",
            "total_rakes_ft",
            "total_eaves_ft",
            "waste_table_pct",
        ):
            fields[key] = clean_numeric(fields[key])

        missing = [key for key, value in fields.items() if value is None and key != "source_file"]
        if missing:
            print(f"  Missing: {missing}")
        rows.append(fields)

    df = pd.DataFrame(rows)
    df.to_csv(output_dir / "eagleview_dataset.csv", index=False)
    df.to_json(output_dir / "eagleview_dataset.json", orient="records", indent=2)
    print(f"\nDone. {len(rows)} reports.")
    print(output_dir / "eagleview_dataset.csv")

    if df.empty:
        return
    print("\n--- Defaults ---")
    if df["total_squares"].notna().any():
        print(f"Avg squares: {df['total_squares'].mean():.1f}")
    if df["waste_table_pct"].notna().any():
        print(f"Avg waste %: {df['waste_table_pct'].mean():.1f}")
    if df["predominant_pitch"].notna().any():
        print(df["predominant_pitch"].value_counts().to_string())
    if df["num_facets"].notna().any():
        print(f"Avg facets: {df['num_facets'].mean():.1f}")


if __name__ == "__main__":
    main()
