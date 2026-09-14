"""
Pull numbers out of Xactimate PDFs / ESX copies in ./xactimate.
Writes one row per file. Pairing lives in pair_ev_xactimate.py.

    python extract_xactimate_data.py --input_dir ./xactimate --save_raw_text
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

OPTIONAL_FIELDS = {
    "steep_charge",
    "op",
    "felt_30",
    "ice_water",
    "ice_water_amount",
    "decking",
    "decking_amount",
    "insurance_company",
    "drip",
    "drip_amount",
    "ridge",
    "ridge_amount",
}


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
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    text = str(value).lower()
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
        r"\bcrossing\b": "xing",
        r"\bnorth\b": "n",
        r"\bsouth\b": "s",
        r"\beast\b": "e",
        r"\bwest\b": "w",
    }
    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text)
    text = re.sub(r"(\d{5})-\d{4}", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def dummy_address(value: str | None) -> bool:
    norm = normalize_address(value)
    if not norm:
        return True
    if "anywhere" in norm:
        return True
    if re.search(r"\b00000\b", norm):
        return True
    return False


def address_keys(value: str | None) -> set[str]:
    keys = set()
    if dummy_address(value):
        return keys
    norm = normalize_address(value)
    if not norm:
        return keys
    keys.add(norm)
    match = re.search(r"^(\d+)\s+(.+?)\s+([a-z]{2})\s+(\d{5})$", norm)
    if match:
        number, street, state, zip_code = match.groups()
        tokens = street.split()
        first = tokens[0] if tokens else ""
        first_two = " ".join(tokens[:2]) if tokens else ""
        keys.add(f"{number}|{zip_code}")
        keys.add(f"{number}|{first}|{zip_code}")
        keys.add(f"{number}|{first}|{state}")
        if first_two:
            keys.add(f"{number}|{first_two}|{zip_code}")
    else:
        bits = norm.split()
        if bits and bits[0].isdigit():
            zip_hit = re.search(r"\b(\d{5})\b", norm)
            if zip_hit:
                keys.add(f"{bits[0]}|{zip_hit.group(1)}")
            keys.add(f"{bits[0]}|{bits[1]}" if len(bits) > 1 else bits[0])
    return {item for item in keys if item}


def property_key(value: str | None) -> str:
    if dummy_address(value):
        return ""
    norm = normalize_address(value)
    match = re.search(r"^(\d+)\s+(.+?)\s+([a-z]{2})\s+(\d{5})$", norm)
    if match:
        number, street, _state, zip_code = match.groups()
        street = re.sub(r"\b(apt|unit|ste)\s*\S+$", "", street).strip()
        named = " ".join(street.split()[:3])
        return f"{number}|{named}|{zip_code}"
    zip_hit = re.search(r"\b(\d{5})\b", norm)
    bits = norm.split()
    if bits and bits[0].isdigit() and zip_hit:
        named = " ".join(bits[1:3])
        return f"{bits[0]}|{named}|{zip_hit.group(1)}"
    return norm


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
            line = re.split(
                r"\s+(?:Claim Number|Policy Number|Type of Loss|Cellular)\s*:",
                line,
                maxsplit=1,
                flags=re.I,
            )[0].strip()
            low = line.lower()
            if any(
                low.startswith(token)
                for token in (
                    "e-mail",
                    "email",
                    "home:",
                    "claim rep",
                    "claim number",
                    "estimator",
                    "operator",
                    "company:",
                    "business:",
                    "cellular",
                    "phone",
                    "fax:",
                    "insured:",
                )
            ):
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
    ice_item = first_item(items, "ice", "water") or first_item(items, "ice & water")
    deck_item = None
    for item in items:
        blob = item["desc"].lower()
        if "remove" in blob and "shingle" in blob:
            continue
        if any(word in blob for word in ("decking", "sheathing", "plywood", " osb")):
            deck_item = item
            break
    felt_30 = first_item(items, "30 lb") or first_item(items, "30#") or first_item(items, "synthetic")

    claim_number = None
    claim_hit = re.search(r"Claim Number:\s*(\S+)", text, re.I)
    if claim_hit:
        claim_number = claim_hit.group(1).strip(".,;")

    estimate_number = None
    est_hit = re.search(r"^Estimate:\s*([A-Z0-9][A-Z0-9._-]{2,})", text, re.I | re.M)
    if est_hit:
        estimate_number = est_hit.group(1).strip()

    date_of_loss = date
    estimate_date = None
    for pattern in (
        r"Date Est\.?\s*Completed:\s*(\d{1,2}/\d{1,2}/\d{2,4})",
        r"Estimate Date:\s*(\d{1,2}/\d{1,2}/\d{2,4})",
        r"Date Entered:\s*(\d{1,2}/\d{1,2}/\d{2,4})",
    ):
        match = re.search(pattern, text, re.I)
        if match:
            estimate_date = match.group(1)
            break

    insurance_company = None
    ins_hit = re.search(r"Insurance Company:\s*(.+)", text, re.I)
    if ins_hit:
        insurance_company = re.sub(r"\s+", " ", ins_hit.group(1)).strip()

    price_list = None
    pl_hit = re.search(r"Price List:\s*(\S+)", text, re.I)
    if pl_hit:
        price_list = pl_hit.group(1).strip()

    return {
        "address": xactimate_address(text),
        "claim_number": claim_number,
        "estimate_number": estimate_number,
        "date_of_loss": date_of_loss,
        "estimate_date": estimate_date,
        "claim_date": estimate_date or date_of_loss,
        "roof_squares": squares,
        "shingle_type": shingle_type,
        "tear_off": tear["qty"] if tear else None,
        "tear_off_amount": tear["amount"] if tear else None,
        "felt": felt["qty"] if felt else None,
        "felt_amount": felt["amount"] if felt else None,
        "felt_30": felt_30["qty"] if felt_30 else None,
        "ice_water": ice_item["qty"] if ice_item else None,
        "ice_water_amount": ice_item["amount"] if ice_item else None,
        "ridge": ridge_item["qty"] if ridge_item else None,
        "ridge_amount": ridge_item["amount"] if ridge_item else None,
        "drip": drip_item["qty"] if drip_item else None,
        "drip_amount": drip_item["amount"] if drip_item else None,
        "decking": deck_item["qty"] if deck_item else None,
        "decking_amount": deck_item["amount"] if deck_item else None,
        "steep_charge": sum_amounts(items, "steep"),
        "op": op,
        "grand_total": grand,
        "insurance_company": insurance_company,
        "price_list": price_list,
    }


def ticket_notes(text: str, filename: str = "") -> str:
    notes: list[str] = []
    fn = filename.lower()
    filename_flags = (
        (r"\bsupplement\b", "supplement"),
        (r"\boriginal\b", "original"),
        (r"\binitial\b", "initial"),
        (r"\binsurance\b", "insurance"),
        (r"\busaa\b", "usaa"),
        (r"state\s*farm", "state farm"),
        (r"\baaa\b", "aaa"),
        (r"\bmrc\b", "mrc"),
        (r"myroofco", "mrc"),
        (r"final\s+draft", "contractor draft"),
    )
    for pattern, label in filename_flags:
        if re.search(pattern, fn, re.I):
            notes.append(label)
    if re.search(r"^\s*\d+\.\s+Supplement\b", text, re.I | re.M):
        notes.append("supplement line")
    if re.search(r"Insurance Company:", text, re.I):
        notes.append("carrier header")
    if re.search(r"Company:\s*My Roof Co", text, re.I):
        notes.append("contractor header")
    if re.search(r"Price List:\s*CODE", text, re.I):
        notes.append("CODE price list")
    return "; ".join(dict.fromkeys(notes))


def _present(value) -> bool:
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except TypeError:
        pass
    return True


def hit_rates(frame: pd.DataFrame) -> dict[str, str]:
    n = len(frame)
    rates = {}
    for col in frame.columns:
        if col == "source_file":
            continue
        filled = frame[col].apply(_present).sum()
        rates[col] = f"{int(filled)}/{n}"
    return rates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", default="./xactimate")
    parser.add_argument("--output_dir", default="./extracted")
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
        fields["ticket_note"] = ticket_notes(text, path.name)
        missing = [
            key
            for key, value in fields.items()
            if value in (None, "") and key not in OPTIONAL_FIELDS and key != "ticket_note"
        ]
        if missing:
            print(f"  Missing: {missing}")
        rows.append(fields)

    xa = pd.DataFrame(rows)
    xa.to_csv(output_dir / "xactimate_dataset.csv", index=False)
    print(f"\nWrote {len(xa)} Xactimate rows to {output_dir / 'xactimate_dataset.csv'}")
    print("Hit rates:")
    for key, rate in hit_rates(xa).items():
        print(f"  {key}: {rate}")


if __name__ == "__main__":
    main()
