"""
Copy Xactimate PDFs / ESX that sit with the EagleView reports into ./xactimate.
Does not delete originals. Does not commit.

    python collect_xactimate.py
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path

import pandas as pd

from file_kinds import classify_document, skip_path
from flip_folders import ingest_roots


def file_hash(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def looks_xactimate(path: Path) -> bool:
    return classify_document(path) in {"xactimate", "insurance"}


def default_roots() -> list[Path]:
    return ingest_roots()


def collect(roots: list[Path], reports_dir: Path, dest: Path) -> pd.DataFrame:
    dest.mkdir(parents=True, exist_ok=True)
    report_files = list(reports_dir.glob("*.pdf"))
    report_hashes = {file_hash(path): path.name for path in report_files}
    report_sizes = {path.stat().st_size for path in report_files}
    print(f"{len(report_hashes)} EagleView PDFs in {reports_dir}")

    ev_folders: dict[str, Path] = {}
    scanned = 0
    for root in roots:
        print(f"Scanning {root}")
        for path in root.rglob("*"):
            if not path.is_file() or skip_path(path):
                continue
            suffix = path.suffix.lower()
            if suffix not in {".pdf", ".esx", ".esz"}:
                continue
            if dest in path.resolve().parents or path.parent == dest:
                continue
            if reports_dir.resolve() in path.resolve().parents:
                continue
            scanned += 1
            if suffix == ".pdf":
                try:
                    size = path.stat().st_size
                except OSError:
                    continue
                if size not in report_sizes:
                    continue
                try:
                    digest = file_hash(path)
                except OSError:
                    continue
                if digest in report_hashes:
                    ev_name = report_hashes[digest]
                    ev_folders.setdefault(ev_name, path.parent)

    print(f"Located original folders for {len(ev_folders)} / {len(report_hashes)} EV files")

    seen_hashes: set[str] = set()
    copied: list[Path] = []
    pairs = []
    dest_by_hash: dict[str, str] = {}

    def copy_one(src: Path) -> str | None:
        try:
            digest = file_hash(src)
        except OSError:
            return None
        if digest in seen_hashes:
            return dest_by_hash.get(digest)
        seen_hashes.add(digest)
        target = dest / src.name
        if target.exists():
            target = dest / f"{src.stem}-{digest[:12]}{src.suffix}"
        shutil.copy2(src, target)
        copied.append(target)
        dest_by_hash[digest] = target.name
        print(f"  + {src.name}")
        return target.name

    search_dirs: set[Path] = set()
    for folder in ev_folders.values():
        search_dirs.add(folder)

    for folder in sorted(search_dirs):
        if not folder.exists():
            continue
        for path in folder.iterdir():
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".pdf", ".esx", ".esz"}:
                continue
            try:
                digest = file_hash(path)
            except OSError:
                continue
            if digest in report_hashes:
                continue
            if looks_xactimate(path):
                copy_one(path)

    # Map each EV file to xactimate files from its folder
    xact_in_folder: dict[Path, list[str]] = {}
    for ev_name, folder in ev_folders.items():
        names = []
        for path in folder.iterdir() if folder.exists() else []:
            if not path.is_file() or path.suffix.lower() not in {".pdf", ".esx", ".esz"}:
                continue
            try:
                digest = file_hash(path)
            except OSError:
                continue
            if digest in report_hashes:
                continue
            if digest in dest_by_hash:
                names.append(dest_by_hash[digest])
            elif looks_xactimate(path):
                copied_name = copy_one(path)
                if copied_name:
                    names.append(copied_name)
        parent = folder.parent
        if parent in search_dirs:
            for path in parent.iterdir() if parent.exists() else []:
                if not path.is_file() or path.suffix.lower() not in {".pdf", ".esx", ".esz"}:
                    continue
                try:
                    digest = file_hash(path)
                except OSError:
                    continue
                if digest in dest_by_hash and dest_by_hash[digest] not in names:
                    # only attach parent-level xact if this EV is the only one from that parent
                    pass
        pairs.append({"ev_source_file": ev_name, "xact_files": ";".join(names), "folder": str(folder)})

    dest_resolved = dest.resolve()
    reports_resolved = reports_dir.resolve()
    for root in roots:
        if not root.exists():
            continue
        print(f"Scanning shop estimates in {root}")
        for path in root.rglob("*"):
            if not path.is_file() or skip_path(path):
                continue
            if path.suffix.lower() not in {".pdf", ".esx", ".esz"}:
                continue
            try:
                resolved = path.resolve()
            except OSError:
                continue
            if dest_resolved == resolved.parent or dest_resolved in resolved.parents:
                continue
            if reports_resolved in resolved.parents:
                continue
            if looks_xactimate(path):
                copy_one(path)

    print(f"\nCopied {len(copied)} unique Xactimate file(s) into {dest}")
    print(f"Scanned {scanned} files while locating EV originals")
    return pd.DataFrame(pairs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--roots", nargs="*", default=None)
    parser.add_argument("--reports", default="./reports")
    parser.add_argument("--dest", default="./xactimate")
    parser.add_argument("--pair_map", default="./extracted/xactimate_folder_pairs.csv")
    args = parser.parse_args()
    roots = [Path(item) for item in args.roots] if args.roots else default_roots()
    pairs = collect(roots, Path(args.reports), Path(args.dest))
    out = Path(args.pair_map)
    out.parent.mkdir(parents=True, exist_ok=True)
    pairs.to_csv(out, index=False)
    print(out)


if __name__ == "__main__":
    main()
