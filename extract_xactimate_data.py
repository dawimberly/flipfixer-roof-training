"""
Pull numbers out of Xactimate PDFs / ESX copies in ./xactimate.
Join to EagleView rows on normalized address.

    python extract_xactimate_data.py --input_dir ./xactimate --ev_csv ./extracted/eagleview_dataset.csv
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
import pdfplumber

from extract_eagleview_data import property_address

MONEY = re.compile(r"[\d,]+\.\d{2}")
CITY = re.compile(r"(.+?),\s*([A-Z]{2})\s+(\d{5})(?:-\d{4})?", re.I)
LINE = re.compile(
    r"^\s*\d+\.\s+(?P<desc>.+?)\s+(?P<qty>[\d,.]+)\s*(?P<unit>SQ|LF|EA|SF|HR)\b(?P<rest>.*)$",
    re.I | re.M,
)


def extract_text(path: Path) -> str:
    if path.suffix.lower() == ".esx":
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return path.read_bytes()[:2_000_000].decode("latin-1", errors="ignore")
    parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                parts.append(text)
    return "\n".join(parts)


def last_money(text: str):
    hits = MONEY.findall(text or "")
    if not hits:
        return None
    return float(hits[-1].replace(",", ""))


def to_float(value):
    if value is None:
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


def normalize_address(value: str | None) -> str:
    if not value:
        return ""
    text = value.lower()
    text = text.replace("#", " ")
    text = re.sub(r"[.,]", " ", text)
    replacements = {
        r"\bstreet\b": "st",
        r"\bavenue\b": "ave",
        r"\bdrive\b": "dr",
        r"\blane\b": "ln",
        r"\bterrace\b": "ter",
        r"\bcircle\b": "cir",
        r"\bcourt\b": "ct",
        r"\bplace\b": "pl",
        r"\broad\b": "rd",
        r"\bparkway\b": "pkwy",
        r"\bboulevard\b": "blvd",
        r"\bnorth\b": "n",
        r"\bsouth\b": "s",
        r"\beast\b": "e",
        r"\bwest\b": "w",
    }
    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text)
    text = re.sub(r"(\d{5})-\d{4}", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def address_keys(value: str | None) -> set[str]:
    keys = set()
    norm = normalize_address(value)
    if not norm:
        return keys
    keys.add(norm)
    match = re.search(r"^(\d+)\s+(.+?)\s+([a-z]{2})\s+(\d{5})$", norm)
    if match:
        number, street, state, zip_code = match.groups()
        first = street.split()[0] if street.split() else ""
        keys.add(f"{number}|{zip_code}")
        keys.add(f"{number}|{first}|{zip_code}")
        keys.add(f"{number}|{first}|{state}")
    else:
        bits = norm.split()
        if bits and bits[0].isdigit():
            zip_hit = re.search(r"\b(\d{5})\b", norm)
            if zip_hit:
                keys.add(f"{bits[0]}|{zip_hit.group(1)}")
            keys.add(f"{bits[0]}|{bits[1]}" if len(bits) > 1 else bits[0])
    return {item for item in keys if item}


def xactimate_address(text: str) -> str | None:
    match = re.search(r"Property:\s*", text, re.I)
    if match:
        chunk = text[match.end() : match.end() + 500].splitlines()
        street = None
        city_line = None
        for raw in chunk[:8]:
            line = raw.strip()
            low = line.lower()
            if not line:
                continue
            if low.startswith("property:"):
                line = re.sub(r"^Property:\s*", "", line, flags=re.I).strip()
                low = line.lower()
            if any(token in low for token in ("e-mail", "email", "home:", "claim", "estimator", "operator", "company:", "business:")):
                continue
            city_hit = CITY.search(line)
            if city_hit:
                city_line = city_hit.group(0)
                break
            if street is None and re.search(r"\d", line):
                street = line
        if street and city_line:
            return f"{street}, {city_line}"
        if street:
            return street
        if city_line:
            return city_line
    return property_address(text)


def line_items(text: str) -> list[dict]:
    items = []
    for match in LINE.finditer(text):
        desc = re.sub(r"\s+", " ", match.group("desc")).strip()
        items.append(
            {
                "desc": desc,
                "qty": to_float(match.group("qty")),
                "unit": match.group("unit").upper(),
                "amount": last_money(match.group("rest")),
            }
        )
    return items


def first_item(items: list[dict], *needles: str, unit: str | None = None):
    for item in items:
        blob = item["desc"].lower()
        if all(needle in blob for needle in needles):
            if unit and item["unit"] != unit:
                continue
            return item
    return None


def sum_amounts(items: list[dict], *needles: str):
    total = 0.0
    found = False
    for item in items:
        blob = item["desc"].lower()
        if all(needle in blob for needle in needles) and item["amount"] is not None:
            total += item["amount"]
            found = True
    return total if found else None


def parse_fields(text: str) -> dict:
    items = line_items(text)
    shingle_install = None
    for item in items:
        blob = item["desc"].lower()
        if item["unit"] != "SQ":
            continue
        if "remove" in blob:
            continue
        if "steep" in blob or "high roof" in blob or "felt" in blob:
            continue
        if any(word in blob for word in ("shingle", "laminated", "3 tab", "comp.")):
            shingle_install = item
            break

    tear = None
    for item in items:
        blob = item["desc"].lower()
        if "remove" in blob and any(word in blob for word in ("shingle", "laminated", "3 tab", "comp")):
            if "steep" in blob:
                continue
            tear = item
            break

    felt = None
    for item in items:
        blob = item["desc"].lower()
        if "felt" in blob or "underlayment" in blob:
            if "remove" in blob and "shingle" in blob:
                continue
            felt = item
            break

    squares = None
    sq_match = re.search(r"([\d,.]+)\s+Number of Squares", text, re.I)
    if sq_match:
        squares = to_float(sq_match.group(1))
    if squares is None and shingle_install:
        squares = shingle_install["qty"]
    if squares is None and tear:
        squares = tear["qty"]

    shingle_type = None
    source = shingle_install or tear
    if source:
        shingle_type = source["desc"]
        shingle_type = re.sub(r"^(?:Remove|R&R)\s+", "", shingle_type, flags=re.I)
        shingle_type = shingle_type.strip(" -")

    date = None
    for pattern in (
        r"Date of Loss:\s*(\d{1,2}/\d{1,2}/\d{2,4})",
        r"Date Entered:\s*(\d{1,2}/\d{1,2}/\d{2,4})",
        r"Date Inspected:\s*(\d{1,2}/\d{1,2}/\d{2,4})",
    ):
        match = re.search(pattern, text, re.I)
        if match:
            date = match.group(1)
            break

    totals_line = re.search(r"Line Item Totals:\s+\S+\s+(.+)", text, re.I)
    grand = None
    op = None
    if totals_line:
        nums = [to_float(item) for item in MONEY.findall(totals_line.group(1))]
        nums = [n for n in nums if n is not None]
        if re.search(r"TAX\s+O&P\s+TOTAL", text, re.I) and len(nums) >= 2:
            op = nums[-2]
            grand = nums[-1]
        elif len(nums) >= 3:
            grand = nums[0]
        elif nums:
            grand = nums[-1]
    if op is None:
        oh = re.search(r"^Overhead\s+[^\n]{0,20}([\d,]+\.\d{2})", text, re.I | re.M)
        profit = re.search(r"^Profit\s+[^\n]{0,20}([\d,]+\.\d{2})", text, re.I | re.M)
        if oh and profit:
            op = to_float(oh.group(1)) + to_float(profit.group(1))
        elif oh:
            op = to_float(oh.group(1))

    ridge_item = first_item(items, "ridge cap") or first_item(items, "hip / ridge")
    drip_item = first_item(items, "drip edge")

    return {
        "address": xactimate_address(text),
        "claim_date": date,
        "roof_squares": squares,
        "shingle_type": shingle_type,
        "tear_off": tear["qty"] if tear else None,
        "tear_off_amount": tear["amount"] if tear else None,
        "felt": felt["qty"] if felt else None,
        "felt_amount": felt["amount"] if felt else None,
        "ridge": ridge_item["qty"] if ridge_item else None,
        "ridge_amount": ridge_item["amount"] if ridge_item else None,
        "drip": drip_item["qty"] if drip_item else None,
        "drip_amount": drip_item["amount"] if drip_item else None,
        "steep_charge": sum_amounts(items, "steep"),
        "op": op,
        "grand_total": grand,
    }


def attach_folder_matches(paired: pd.DataFrame, xa: pd.DataFrame, pair_map_path: Path) -> pd.DataFrame:
    if not pair_map_path.exists() or xa.empty:
        return paired
    folder = pd.read_csv(pair_map_path)
    xa_by_name = {row["source_file"]: row for row in xa.to_dict("records")}
    used = set(paired.loc[paired["xact_source_file"].notna(), "xact_source_file"])
    for idx, row in paired.iterrows():
        if pd.notna(row["xact_source_file"]):
            continue
        hits = folder.loc[folder["ev_source_file"] == row["ev_source_file"], "xact_files"]
        if hits.empty:
            continue
        names = [part for part in str(hits.iloc[0]).split(";") if part]
        pick = None
        for name in names:
            if name in used or name not in xa_by_name:
                continue
            candidate = xa_by_name[name]
            score = (0 if pd.isna(candidate.get("grand_total")) else 2) + (
                0 if pd.isna(candidate.get("roof_squares")) else 1
            )
            if pick is None or score > pick[0]:
                pick = (score, name, candidate)
        if pick is None:
            continue
        _, name, match = pick
        used.add(name)
        paired.at[idx, "match_method"] = "folder"
        paired.at[idx, "xact_source_file"] = match.get("source_file")
        paired.at[idx, "claim_date"] = match.get("claim_date")
        paired.at[idx, "xact_squares"] = match.get("roof_squares")
        paired.at[idx, "shingle_type"] = match.get("shingle_type")
        paired.at[idx, "tear_off"] = match.get("tear_off")
        paired.at[idx, "tear_off_amount"] = match.get("tear_off_amount")
        paired.at[idx, "felt"] = match.get("felt")
        paired.at[idx, "felt_amount"] = match.get("felt_amount")
        paired.at[idx, "ridge"] = match.get("ridge")
        paired.at[idx, "ridge_amount"] = match.get("ridge_amount")
        paired.at[idx, "drip"] = match.get("drip")
        paired.at[idx, "drip_amount"] = match.get("drip_amount")
        paired.at[idx, "steep_charge"] = match.get("steep_charge")
        paired.at[idx, "op"] = match.get("op")
        paired.at[idx, "grand_total"] = match.get("grand_total")
    return paired


def pair_frames(ev: pd.DataFrame, xa: pd.DataFrame) -> pd.DataFrame:
    ev = ev.copy()
    xa = xa.copy()
    ev_keys_list = [address_keys(value) if pd.notna(value) else set() for value in ev["address"]]
    xa_keys_list = [address_keys(value) if pd.notna(value) else set() for value in xa["address"]]

    used = set()
    rows = []
    xa_records = xa.to_dict("records")
    for ev_i, ev_row in enumerate(ev.to_dict("records")):
        match = None
        match_how = None
        ev_keys = ev_keys_list[ev_i]
        if ev_keys:
            best = None
            for i, xa_row in enumerate(xa_records):
                if i in used:
                    continue
                overlap = ev_keys & xa_keys_list[i]
                if not overlap:
                    continue
                score = (0 if pd.isna(xa_row.get("grand_total")) else 2) + (
                    0 if pd.isna(xa_row.get("roof_squares")) else 1
                )
                if best is None or score > best[0]:
                    best = (score, i, xa_row, "address")
            if best:
                match = best[2]
                match_how = best[3]
                used.add(best[1])
        row = {
            "address": ev_row.get("address"),
            "ev_source_file": ev_row.get("source_file"),
            "ev_squares": ev_row.get("total_squares"),
            "ev_area_sqft": ev_row.get("total_roof_area_sqft"),
            "ev_pitch": ev_row.get("predominant_pitch"),
            "ev_facets": ev_row.get("num_facets"),
            "ev_ridges_ft": ev_row.get("total_ridges_ft"),
            "ev_valleys_ft": ev_row.get("total_valleys_ft"),
            "ev_rakes_ft": ev_row.get("total_rakes_ft"),
            "ev_eaves_ft": ev_row.get("total_eaves_ft"),
            "ev_waste_pct": ev_row.get("waste_table_pct"),
        }
        if match is None:
            row.update(
                {
                    "match_method": None,
                    "xact_source_file": None,
                    "claim_date": None,
                    "xact_squares": None,
                    "shingle_type": None,
                    "tear_off": None,
                    "tear_off_amount": None,
                    "felt": None,
                    "felt_amount": None,
                    "ridge": None,
                    "ridge_amount": None,
                    "drip": None,
                    "drip_amount": None,
                    "steep_charge": None,
                    "op": None,
                    "grand_total": None,
                }
            )
        else:
            row.update(
                {
                    "match_method": match_how,
                    "xact_source_file": match.get("source_file"),
                    "claim_date": match.get("claim_date"),
                    "xact_squares": match.get("roof_squares"),
                    "shingle_type": match.get("shingle_type"),
                    "tear_off": match.get("tear_off"),
                    "tear_off_amount": match.get("tear_off_amount"),
                    "felt": match.get("felt"),
                    "felt_amount": match.get("felt_amount"),
                    "ridge": match.get("ridge"),
                    "ridge_amount": match.get("ridge_amount"),
                    "drip": match.get("drip"),
                    "drip_amount": match.get("drip_amount"),
                    "steep_charge": match.get("steep_charge"),
                    "op": match.get("op"),
                    "grand_total": match.get("grand_total"),
                }
            )
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", default="./xactimate")
    parser.add_argument("--output_dir", default="./extracted")
    parser.add_argument("--ev_csv", default="./extracted/eagleview_dataset.csv")
    parser.add_argument("--pair_map", default="./extracted/xactimate_folder_pairs.csv")
    parser.add_argument("--save_raw_text", action="store_true")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(
        [path for path in input_dir.iterdir() if path.suffix.lower() in {".pdf", ".esx", ".esz"}]
    )
    if not files:
        print(f"No Xactimate files in {input_dir}.")
        return

    rows = []
    for path in files:
        print(f"Processing: {path.name}")
        try:
            text = extract_text(path)
        except Exception as exc:
            print(f"  FAILED: {exc}")
            continue
        if args.save_raw_text:
            (output_dir / f"xact_{path.stem}_raw.txt").write_text(text, encoding="utf-8")
        fields = parse_fields(text)
        fields["source_file"] = path.name
        missing = [
            key
            for key, value in fields.items()
            if value is None and key not in {"steep_charge", "op"}
        ]
        if missing:
            print(f"  Missing: {missing}")
        rows.append(fields)

    xa = pd.DataFrame(rows)
    xa.to_csv(output_dir / "xactimate_dataset.csv", index=False)
    print(f"\nWrote {len(xa)} Xactimate rows")

    ev_path = Path(args.ev_csv)
    if not ev_path.exists():
        print(f"No EagleView CSV at {ev_path}; skip join")
        return
    ev = pd.read_csv(ev_path)
    paired = pair_frames(ev, xa)
    paired = attach_folder_matches(paired, xa, Path(args.pair_map))
    out = output_dir / "paired_ev_xactimate.csv"
    paired.to_csv(out, index=False)
    matched = paired["xact_source_file"].notna().sum()
    by_addr = (paired["match_method"] == "address").sum()
    by_folder = (paired["match_method"] == "folder").sum()
    print(f"Paired {matched} / {len(paired)} EagleView rows ({by_addr} address, {by_folder} folder)")
    print(out)
    if paired["grand_total"].notna().any():
        print(f"Avg grand total: {paired['grand_total'].mean():.0f}")
    if paired["xact_squares"].notna().any():
        print(f"Avg Xactimate squares: {paired['xact_squares'].mean():.1f}")


if __name__ == "__main__":
    main()
