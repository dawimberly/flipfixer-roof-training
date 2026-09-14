"""Classify shop PDFs and photos. Peek bytes; do not store branded layout."""

from __future__ import annotations

from pathlib import Path

PHOTO_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff", ".avif"}
DOC_SUFFIXES = {".pdf", ".esx", ".esz"}

EAGLE_NAME = (
    "eagleview",
    "eagle view",
    "eagle-view",
    "ev report",
    "roof report",
    "roof measurement",
    "measurement report",
    "precise aerial",
)
EAGLE_BYTES = (b"EagleView", b"Eagle View", b"EAGLEVIEW", b"Precise Aerial")
XACT_BYTES = (b"Xactimate", b"xactimate", b"Xactware", b"XACTWARE")
INSURANCE_BYTES = (
    b"Insurance Company",
    b"Claim Number",
    b"Type of Loss",
    b"Date of Loss",
    b"Price List:",
)
SHOP_NAME_HINTS = (
    "wimberly",
    "flip fixer",
    "flipfixer",
    "flpfx",
    "the flip fixer",
)
SHOP_BYTES = (
    b"Wimberly",
    b"wimberly",
    b"WIMBERLY",
    b"Flip Fixer",
    b"flip fixer",
    b"The Flip Fixer",
    b"FLPFX",
    b"flpfx",
)

SKIP_DIR_PARTS = {
    ".venv",
    "venv",
    "node_modules",
    ".git",
    "site-packages",
    "__pycache__",
    "AppData",
    ".cache",
    ".cursor",
    "flipfixer-roof-training",
}


def skip_path(path: Path) -> bool:
    return any(part in SKIP_DIR_PARTS for part in path.parts)


def peek_bytes(path: Path, limit: int = 400_000) -> bytes:
    try:
        with path.open("rb") as handle:
            return handle.read(limit)
    except OSError:
        return b""


def shop_in_name(path: Path) -> bool:
    blob = path.name.lower()
    return any(hint in blob for hint in SHOP_NAME_HINTS)


def shop_in_bytes(data: bytes) -> bool:
    low = data.lower()
    return any(needle.lower() in low for needle in SHOP_BYTES)


def photo_role(path: Path) -> str:
    name = path.name.lower()
    if "before" in name:
        return "before"
    if "after" in name:
        return "after"
    if any(token in name for token in ("hail", "damage", "storm", "shingle")):
        return "damage"
    if "roof" in name:
        return "roof"
    return "project"


def classify_photo(path: Path) -> str | None:
    if path.suffix.lower() not in PHOTO_SUFFIXES:
        return None
    if skip_path(path):
        return None
    try:
        size = path.stat().st_size
    except OSError:
        return None
    if size < 20_000:
        return None
    low_parts = {part.lower() for part in path.parts}
    if "node_modules" in low_parts:
        return None
    return "photo"


def classify_document(path: Path, data: bytes | None = None) -> str | None:
    suffix = path.suffix.lower()
    if suffix not in DOC_SUFFIXES:
        return None
    if skip_path(path):
        return None
    name = path.name.lower()
    if suffix in {".esx", ".esz"}:
        return "xactimate"
    if data is None:
        data = peek_bytes(path)
    if any(hint in name for hint in EAGLE_NAME) or any(marker in data for marker in EAGLE_BYTES):
        return "eagleview"
    if any(marker in data for marker in XACT_BYTES):
        return "xactimate"
    insurance = any(marker in data for marker in INSURANCE_BYTES) or "estimate" in name or "insurance" in name
    if insurance and (shop_in_name(path) or shop_in_bytes(data)):
        return "insurance"
    if shop_in_name(path) and "estimate" in name:
        return "insurance"
    return None
