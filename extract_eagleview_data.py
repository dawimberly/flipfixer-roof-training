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

EQ = r"\s*[=:\-]\s*"

PATTERNS = {
    "total_roof_area_sqft": rf"Total\s+(?:Roof\s+)?Area(?:\s*\([^)]+\))?{EQ}([\d,]+)\s*sq\s*ft",
    "total_squares": rf"Total\s+Squares?{EQ}([\d.]+)",
    "predominant_pitch": rf"Predominant\s+Pitch{EQ}(\d+\s*/\s*\d+)",
    "num_facets": rf"(?:Number\s+of\s+Facets|Total\s+Roof\s+Facets){EQ}(\d+)",
    "total_ridges_ft": rf"Total\s+Ridges?(?:\s*/\s*Hips?)?{EQ}([\d,]+)\s*ft",
    "total_valleys_ft": rf"Total\s+Valleys?{EQ}([\d,]+)\s*ft",
    "total_rakes_ft": rf"Total\s+Rakes?{EQ}([\d,]+)\s*ft",
    "total_eaves_ft": rf"Total\s+Eaves?(?:\s*/\s*Starter)?{EQ}([\d,]+)\s*ft",
    "waste_table_pct": r"Waste\s*%\s*0%\s+(\d{1,2})%",
    "address": r"Property\s+Address\s*[:\-]?\s*(.+)",
}


def extract_text(pdf_path: Path) -> str:
    parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
    return "\n".join(parts)


def first_nonzero_waste_pct(text: str):
    match = re.search(r"Waste\s*%\s*((?:\d{1,2}%\s*)+)", text, re.IGNORECASE)
    if not match:
        return None
    for value in re.findall(r"\d+", match.group(1)):
        if int(value) > 0:
            return value
    return None


def squares_at_zero_waste(text: str):
    match = re.search(
        r"Squares\s*\*?\s*((?:\d+(?:\.\d+)?(?:\s+|$))+)",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None
    token = match.group(1).split()[0]
    return token


def property_address(text: str):
    """Street line from the report header. Not the contractor Address: block."""
    city = re.compile(r".+,\s*[A-Z]{2}\s+\d{5}", re.I)
    skip = (
        "precise aerial",
        "premium report",
        "extended coverage",
        "wallslite",
        "prepared for",
        "table of contents",
        "measurements",
        "myroofco",
        "interstate roofing",
        "contact:",
        "company:",
        "phone:",
        "address:",
        "tel.",
        "www.",
        "report details",
        "roof details",
        "in this 3d",
        "total roof",
        "total area",
        "predominant",
        "number of",
        "claim:",
        "page ",
    )
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in lines[:50]:
        low = line.lower()
        if any(token in low for token in skip):
            continue
        if city.search(line):
            cleaned = re.sub(r"\s+Report:.*", "", line, flags=re.I).strip()
            cleaned = re.sub(r"\s+\d{1,2}/\d{1,2}/\d{2,4}\s*$", "", cleaned).strip()
            if city.search(cleaned) or re.search(r"[A-Z]{2}\s+\d{5}", cleaned):
                return cleaned
    labeled = re.search(
        r"Property(?:\s+Location)?\s*[:\-]?\s*(.+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?)",
        text,
        re.I,
    )
    if labeled:
        return labeled.group(1).strip()
    return None


def parse_fields(text: str) -> dict:
    result = {}
    for field, pattern in PATTERNS.items():
        match = re.search(pattern, text, re.IGNORECASE)
        result[field] = match.group(1).strip() if match else None
    if result.get("waste_table_pct") in (None, "0"):
        result["waste_table_pct"] = first_nonzero_waste_pct(text)
    if result.get("total_squares") is None:
        result["total_squares"] = squares_at_zero_waste(text)
    if result.get("total_squares") is None and result.get("total_roof_area_sqft"):
        try:
            area = float(str(result["total_roof_area_sqft"]).replace(",", ""))
            result["total_squares"] = str(round(area / 100.0, 2))
        except ValueError:
            pass
    if result.get("predominant_pitch"):
        result["predominant_pitch"] = re.sub(r"\s+", "", result["predominant_pitch"])
    if not result.get("address"):
        result["address"] = property_address(text)
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
