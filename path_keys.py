"""Join keys from addresses, folder names, and client names."""

from __future__ import annotations

import re
from pathlib import Path

from extract_xactimate_data import dummy_address, normalize_address, property_key
from flip_folders import looks_like_flip_folder

GENERIC_SLUGS = {
    "desktop",
    "downloads",
    "documents",
    "onedrive",
    "photos",
    "pictures",
    "images",
    "img",
    "dcim",
    "camera",
    "reports",
    "xactimate",
    "estimates",
    "projects",
    "backup",
    "copy",
    "misc",
}


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


def name_key(text: str | None) -> str:
    compact = slug(text or "")
    if len(compact) < 4:
        return ""
    if compact.isdigit():
        return ""
    if compact in {slug(item) for item in GENERIC_SLUGS}:
        return ""
    if looks_like_flip_folder(text or ""):
        return ""
    return f"name:{compact}"


STREET_STEMS = {
    "loop",
    "trail",
    "trl",
    "crossing",
    "xing",
    "parkway",
    "pkwy",
    "terrace",
    "ter",
}


def street_keys(text: str | None) -> set[str]:
    """House number plus street tokens. Keeps St vs Way apart. Allows a short folder name."""
    keys: set[str] = set()
    if dummy_address(text):
        return keys
    bits = normalize_address(text).split()
    if bits and re.fullmatch(r"\d{5}", bits[-1]):
        bits = bits[:-1]
    if len(bits) >= 2 and re.fullmatch(r"[a-z]{2}", bits[-1]):
        bits = bits[:-1]
    if len(bits) < 2 or not bits[0].isdigit():
        return keys
    rest = bits[1:]
    number = bits[0]
    if len(rest) >= 3:
        keys.add(f"{number}|{' '.join(rest[:3])}")
        if rest[1] in STREET_STEMS:
            keys.add(f"{number}|{' '.join(rest[:2])}")
    elif len(rest) >= 2:
        keys.add(f"{number}|{' '.join(rest[:2])}")
    elif rest:
        keys.add(f"{number}|{rest[0]}")
    return keys


def keys_from_text(text: str | None) -> set[str]:
    keys: set[str] = set()
    if not text:
        return keys
    named = name_key(text)
    if named:
        keys.add(named)
    if dummy_address(text):
        return keys
    pk = property_key(text)
    if pk:
        keys.add(pk)
    keys |= street_keys(text)
    return keys


SKIP_NAME_STEMS = {
    "before",
    "after",
    "roof",
    "damage",
    "hail",
    "storm",
    "shingle",
    "photo",
    "photos",
    "image",
    "images",
    "pic",
    "scan",
    "report",
    "document",
    "estimate",
    "insurance",
}


def keys_from_path(path: Path) -> set[str]:
    keys: set[str] = set()
    stem_slug = slug(path.stem)
    if stem_slug not in SKIP_NAME_STEMS and not stem_slug.startswith(("img", "dsc", "photo")):
        keys |= keys_from_text(path.stem)
    for part in path.parts[:-1]:
        if looks_like_flip_folder(part):
            continue
        if slug(part) in {slug(item) for item in GENERIC_SLUGS}:
            continue
        if len(part) <= 3 or part in {path.anchor, "/", "\\"}:
            continue
        keys |= keys_from_text(part)
    return keys
