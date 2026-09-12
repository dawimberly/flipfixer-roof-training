"""
Copy EagleView-looking PDFs from common Desktop folders into ./reports.
Does not delete the originals. Does not commit anything.

    python collect_reports.py
    python collect_reports.py --roots "C:/Users/You/Desktop" "C:/Users/You/Downloads"
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
from pathlib import Path

NAME_HINTS = (
    "eagleview",
    "eagle view",
    "eagle-view",
    "ev report",
    "roof report",
    "roof measurement",
    "measurement report",
)


def default_roots() -> list[Path]:
    home = Path.home()
    candidates = [
        home / "Desktop",
        home / "Downloads",
        home / "Documents",
        home / "OneDrive" / "Desktop",
        home / "OneDrive" / "Downloads",
        Path.cwd() / "reports",
    ]
    return [path for path in candidates if path.exists()]


def looks_like_report(path: Path) -> bool:
    name = path.name.lower()
    if not name.endswith(".pdf"):
        return False
    return any(hint in name for hint in NAME_HINTS)


def file_key(path: Path) -> str:
    digest = hashlib.sha1()
    digest.update(path.name.encode("utf-8", errors="ignore"))
    digest.update(str(path.stat().st_size).encode())
    return digest.hexdigest()[:12]


def collect(roots: list[Path], dest: Path) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    copied: list[Path] = []
    for root in roots:
        if not root.exists():
            print(f"Skip missing folder: {root}")
            continue
        print(f"Scanning {root}")
        for path in root.rglob("*.pdf"):
            if not path.is_file():
                continue
            if not looks_like_report(path):
                continue
            key = file_key(path)
            if key in seen:
                continue
            seen.add(key)
            target = dest / path.name
            if target.exists():
                target = dest / f"{path.stem}-{key}{path.suffix}"
            shutil.copy2(path, target)
            copied.append(target)
            print(f"  + {path.name}")
    return copied


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--roots", nargs="*", default=None)
    parser.add_argument("--dest", default="./reports")
    args = parser.parse_args()
    roots = [Path(item) for item in args.roots] if args.roots else default_roots()
    copied = collect(roots, Path(args.dest))
    print(f"\nCopied {len(copied)} PDF(s) into {args.dest}")
    print("Next: python extract_eagleview_data.py --save_raw_text")


if __name__ == "__main__":
    main()
