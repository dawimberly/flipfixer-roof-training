"""Coordinate EagleView, tickets, insurance, and photos by address or name."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

from extract_xactimate_data import dummy_address, property_key
from path_keys import keys_from_path, keys_from_text, name_key


def _present(value) -> bool:
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except TypeError:
        pass
    return str(value).strip() not in {"", "nan", "None"}


def parse_join_keys(blob: str | None) -> set[str]:
    if not blob:
        return set()
    return {item for item in str(blob).split(";;") if item}


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def add(self, item: str) -> None:
        self.parent.setdefault(item, item)

    def find(self, item: str) -> str:
        self.add(item)
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: str, right: str) -> None:
        root_l, root_r = self.find(left), self.find(right)
        if root_l != root_r:
            self.parent[root_r] = root_l


def cluster(members: list[dict]) -> list[list[dict]]:
    uf = UnionFind()
    by_key: dict[str, list[str]] = defaultdict(list)
    for member in members:
        uf.add(member["id"])
        for key in member["keys"]:
            by_key[key].append(member["id"])
    for ids in by_key.values():
        first = ids[0]
        for other in ids[1:]:
            uf.union(first, other)
    groups: dict[str, list[dict]] = defaultdict(list)
    lookup = {member["id"]: member for member in members}
    for member in members:
        groups[uf.find(member["id"])].append(lookup[member["id"]])
    return list(groups.values())


def ev_members(frame: pd.DataFrame) -> list[dict]:
    out = []
    if frame is None or frame.empty:
        return out
    for rec in frame.to_dict("records"):
        src = str(rec.get("source_file") or "")
        keys = keys_from_text(rec.get("address")) | keys_from_text(src)
        out.append(
            {
                "id": f"ev:{src}",
                "kind": "eagleview",
                "label": rec.get("address") or src,
                "source_file": src,
                "address": rec.get("address"),
                "keys": keys,
            }
        )
    return out


def xm_members(frame: pd.DataFrame) -> list[dict]:
    out = []
    if frame is None or frame.empty:
        return out
    for rec in frame.to_dict("records"):
        src = str(rec.get("source_file") or "")
        keys = keys_from_text(rec.get("address")) | keys_from_text(src)
        estimate = rec.get("estimate_number")
        if _present(estimate):
            named = name_key(str(estimate))
            if named:
                keys.add(named)
        out.append(
            {
                "id": f"xm:{src}",
                "kind": "xactimate",
                "label": rec.get("address") or src,
                "source_file": src,
                "address": rec.get("address"),
                "keys": keys,
            }
        )
    return out


def photo_members(rows: list[dict]) -> list[dict]:
    out = []
    for rec in rows:
        src = rec.get("source_path") or rec.get("filename")
        keys = parse_join_keys(rec.get("join_keys"))
        if not keys:
            keys = keys_from_path(Path(src))
        out.append(
            {
                "id": f"photo:{src}",
                "kind": "photo",
                "label": rec.get("filename"),
                "source_file": src,
                "role": rec.get("role"),
                "keys": keys,
            }
        )
    return out


def extra_doc_members(rows: list[dict]) -> list[dict]:
    out = []
    for rec in rows:
        src = rec.get("source_path") or rec.get("filename")
        kind = rec.get("kind") or "document"
        keys = parse_join_keys(rec.get("join_keys")) | keys_from_path(Path(str(src)))
        out.append(
            {
                "id": f"doc:{src}",
                "kind": kind,
                "label": rec.get("filename") or src,
                "source_file": src,
                "keys": keys,
            }
        )
    return out


def bundle_label(group: list[dict]) -> str:
    for member in group:
        address = member.get("address")
        if _present(address) and not dummy_address(str(address)):
            return str(address)
    for member in group:
        if member.get("kind") != "photo" and member.get("label"):
            return str(member["label"])
    return str(group[0]["label"] if group else "unknown")


def summarize_group(group: list[dict]) -> dict:
    photos = [m for m in group if m["kind"] == "photo"]
    roles = {m.get("role") for m in photos}
    docs = [m for m in group if m["kind"] != "photo"]
    kinds = sorted({m["kind"] for m in group})
    address = None
    for member in group:
        if _present(member.get("address")) and not dummy_address(str(member.get("address"))):
            address = member["address"]
            break
    return {
        "project_key": property_key(address) or name_key(bundle_label(group)) or bundle_label(group),
        "label": bundle_label(group),
        "kinds": kinds,
        "eagleview_n": sum(1 for m in group if m["kind"] == "eagleview"),
        "xactimate_n": sum(1 for m in group if m["kind"] == "xactimate"),
        "insurance_n": sum(1 for m in group if m["kind"] == "insurance"),
        "photo_n": len(photos),
        "has_before_after": "before" in roles and "after" in roles,
        "documents": [m.get("source_file") for m in docs],
        "photo_roles": sorted(role for role in roles if role),
    }


def bundle_stats(bundles: list[dict]) -> dict:
    return {
        "n_projects": len(bundles),
        "n_with_photos": sum(1 for row in bundles if row["photo_n"] > 0),
        "n_photos": int(sum(row["photo_n"] for row in bundles)),
        "n_before_after": sum(1 for row in bundles if row["has_before_after"]),
        "n_with_eagleview_and_ticket": sum(
            1 for row in bundles if row["eagleview_n"] and (row["xactimate_n"] or row["insurance_n"])
        ),
        "note": "grouped by address or job name; photos stay on disk",
    }


def read_photo_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def build_bundles(
    ev: pd.DataFrame,
    xm: pd.DataFrame,
    photos: list[dict],
    extra_docs: list[dict] | None = None,
) -> tuple[list[dict], dict]:
    members = ev_members(ev) + xm_members(xm) + photo_members(photos)
    if extra_docs:
        members += extra_doc_members(extra_docs)
    groups = cluster(members)
    bundles = [summarize_group(group) for group in groups]
    bundles.sort(key=lambda row: (-row["photo_n"], -row["eagleview_n"], str(row["label"])))
    return bundles, bundle_stats(bundles)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ev_csv", default="./extracted/eagleview_dataset.csv")
    parser.add_argument("--xm_csv", default="./extracted/xactimate_dataset.csv")
    parser.add_argument("--photos", default="./extracted/photo_index.csv")
    parser.add_argument("--output_dir", default="./extracted")
    args = parser.parse_args()
    bundles, stats = build_bundles(
        read_csv(Path(args.ev_csv)),
        read_csv(Path(args.xm_csv)),
        read_photo_csv(Path(args.photos)),
    )
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "project_bundles.json").write_text(json.dumps(bundles, indent=2), encoding="utf-8")
    pd.DataFrame(bundles).to_csv(out / "project_bundles.csv", index=False)
    (out / "project_stats.json").write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print(f"Projects: {stats['n_projects']}")
    print(f"With photos: {stats['n_with_photos']} ({stats['n_photos']} images)")
    print(f"Before/after pairs: {stats['n_before_after']}")
    print(f"EV + ticket: {stats['n_with_eagleview_and_ticket']}")
    print(out / "project_bundles.csv")


if __name__ == "__main__":
    main()
