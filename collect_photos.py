"""Index job photos from Flip Fixer folders. Does not git-add images."""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

from file_kinds import PHOTO_SUFFIXES, classify_photo, photo_role, skip_path
from flip_folders import ingest_roots
from path_keys import keys_from_path


def file_hash(path: Path) -> str:
    digest = hashlib.sha1()
    digest.update(path.name.encode("utf-8", errors="ignore"))
    try:
        digest.update(str(path.stat().st_size).encode())
    except OSError:
        pass
    return digest.hexdigest()[:12]


def collect_photos(roots: list[Path], out_csv: Path) -> list[dict]:
    seen: set[str] = set()
    rows: list[dict] = []
    for root in roots:
        if not root.exists():
            print(f"Skip missing folder: {root}")
            continue
        print(f"Scanning photos in {root}")
        for path in root.rglob("*"):
            if not path.is_file() or skip_path(path):
                continue
            if path.suffix.lower() not in PHOTO_SUFFIXES:
                continue
            if classify_photo(path) != "photo":
                continue
            key = file_hash(path)
            if key in seen:
                continue
            seen.add(key)
            role = photo_role(path)
            join_keys = sorted(keys_from_path(path))
            rows.append(
                {
                    "source_path": str(path),
                    "filename": path.name,
                    "folder": str(path.parent),
                    "role": role,
                    "bytes": path.stat().st_size,
                    "join_keys": ";;".join(join_keys),
                }
            )
            print(f"  + {path.name} ({role})")
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source_path", "filename", "folder", "role", "bytes", "join_keys"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nIndexed {len(rows)} photo(s) into {out_csv}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--roots", nargs="*", default=None)
    parser.add_argument("--out", default="./extracted/photo_index.csv")
    args = parser.parse_args()
    roots = [Path(item) for item in args.roots] if args.roots else ingest_roots()
    collect_photos(roots, Path(args.out))


if __name__ == "__main__":
    main()
