"""
Copy EagleView-looking PDFs from common Desktop folders into ./reports.
Does not delete the originals. Does not commit anything.

    python collect_reports.py
    python collect_reports.py --roots "C:/Users/You/Desktop" "C:/Users/You/Downloads"
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

from file_kinds import classify_document, skip_path
from flip_folders import ingest_roots


def default_roots() -> list[Path]:
    roots = ingest_roots()
    reports = Path.cwd() / "reports"
    if reports.exists() and reports not in roots:
        roots.append(reports)
    return roots


def looks_like_report(path: Path) -> bool:
    return classify_document(path) == "eagleview"


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
        dest_resolved = dest.resolve()
        for path in root.rglob("*.pdf"):
            if not path.is_file() or skip_path(path):
                continue
            try:
                resolved = path.resolve()
            except OSError:
                continue
            if dest_resolved == resolved.parent or dest_resolved in resolved.parents:
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
