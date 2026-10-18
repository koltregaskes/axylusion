#!/usr/bin/env python3
"""
Annotate unavailable gallery items in data/gallery.json from a CSV list.

Input CSV columns: id,reason
Reasons used in the CSV today:
- missing_in_r2
- truncated_png_in_r2

Edits each matching item by adding:
- media_status: "unavailable"
- media_unavailable_reason: "<reason>"

No items are deleted. All other fields are preserved.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
GALLERY_PATH = REPO_ROOT / "data" / "gallery.json"


@dataclass
class UnavailableEntry:
    id: str
    reason: str


def load_unavailable_csv(path: Path) -> list[UnavailableEntry]:
    entries: list[UnavailableEntry] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            _id = (row.get("id") or "").strip().lower()
            reason = (row.get("reason") or "").strip()
            if not _id or not reason:
                continue
            entries.append(UnavailableEntry(id=_id, reason=reason))
    return entries


def load_gallery(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "items" not in payload:
        raise ValueError(f"Unexpected gallery.json payload shape at {path}")
    return payload


def apply_annotations(payload: dict[str, Any], entries: list[UnavailableEntry]) -> tuple[int, int]:
    items: list[dict[str, Any]] = list(payload.get("items") or [])
    by_id = {str(item.get("id") or "").strip().lower(): item for item in items}
    updated = 0
    not_found = 0
    for entry in entries:
        item = by_id.get(entry.id)
        if not item:
            not_found += 1
            continue
        if item.get("media_status") != "unavailable" or item.get("media_unavailable_reason") != entry.reason:
            item["media_status"] = "unavailable"
            item["media_unavailable_reason"] = entry.reason
            updated += 1
    return updated, not_found


def count_visible(payload: dict[str, Any]) -> tuple[int, int]:
    items: list[dict[str, Any]] = list(payload.get("items") or [])
    total = len(items)
    visible = sum(1 for item in items if str(item.get("media_status") or "") != "unavailable")
    return total, visible


def main() -> int:
    ap = argparse.ArgumentParser(description="Annotate unavailable gallery items in data/gallery.json")
    ap.add_argument("--csv", type=Path, required=True, help="Path to CSV with id,reason")
    ap.add_argument("--gallery", type=Path, default=GALLERY_PATH, help="Path to data/gallery.json")
    args = ap.parse_args()

    csv_entries = load_unavailable_csv(args.csv)
    if not csv_entries:
        print("No CSV entries loaded; nothing to do.")
        return 1

    payload = load_gallery(args.gallery)
    before_total, before_visible = count_visible(payload)
    updated, not_found = apply_annotations(payload, csv_entries)
    after_total, after_visible = count_visible(payload)

    # Write back
    args.gallery.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("Annotation summary")
    print("==================")
    print(f"CSV entries: {len(csv_entries)} (not found in gallery.json: {not_found})")
    print(f"Updated items: {updated}")
    print(f"Before visible/total: {before_visible}/{before_total}")
    print(f"After  visible/total: {after_visible}/{after_total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

