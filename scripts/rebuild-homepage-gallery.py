#!/usr/bin/env python3
"""
Rebuild the homepage gallery payload from the main gallery export.

The homepage uses a curated subset of gallery items. This script preserves the
existing homepage item order while refreshing names, dates, types, and media URLs
from data/gallery.json. It also writes stable item IDs into the homepage payload
so future repoints do not depend on parsing Midjourney URLs.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent.parent
GALLERY_PATH = PROJECT_DIR / "data" / "gallery.json"
HOMEPAGE_PATH = PROJECT_DIR / "data" / "homepage-gallery.json"
UUID_PATTERN = re.compile(
    r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gallery", type=Path, default=GALLERY_PATH, help="Path to data/gallery.json")
    parser.add_argument("--homepage", type=Path, default=HOMEPAGE_PATH, help="Path to data/homepage-gallery.json")
    parser.add_argument("--check", action="store_true", help="Exit non-zero when the homepage payload is out of date")
    return parser.parse_args()


def load_items(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        items = payload.get("items", [])
    else:
        items = payload

    if not isinstance(items, list):
        raise ValueError(f"{path} does not contain a list of items")
    return items


def extract_job_id(value: str) -> str:
    match = UUID_PATTERN.search(value)
    return match.group(1).lower() if match else ""


def build_gallery_lookup(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for item in items:
        item_id = str(item.get("id") or "").strip().lower()
        if item_id:
            lookup[item_id] = item
            continue

        cdn_url = str(item.get("cdn_url") or "").strip()
        extracted = extract_job_id(cdn_url)
        if extracted:
            lookup[extracted] = item

    return lookup


def rebuild_items(homepage_items: list[dict[str, Any]], gallery_lookup: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    rebuilt: list[dict[str, Any]] = []
    missing: list[str] = []

    for item in homepage_items:
        existing_id = str(item.get("id") or "").strip().lower()
        key = existing_id or extract_job_id(str(item.get("cdn_url") or "")) or extract_job_id(str(item.get("url") or ""))
        if not key or key not in gallery_lookup:
            missing.append(item.get("name") or key or "<unknown>")
            rebuilt.append(dict(item))
            continue

        source = gallery_lookup[key]
        rebuilt_item = dict(item)
        rebuilt_item["id"] = source.get("id") or key

        for field in ("name", "cdn_url", "created", "type"):
            source_value = source.get(field)
            if isinstance(source_value, str) and source_value.strip():
                rebuilt_item[field] = source_value.strip()

        rebuilt.append(rebuilt_item)

    return rebuilt, missing


def render_payload(items: list[dict[str, Any]]) -> str:
    return json.dumps({"items": items}, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    args = parse_args()
    gallery_items = load_items(args.gallery)
    homepage_items = load_items(args.homepage)
    rebuilt_items, missing = rebuild_items(homepage_items, build_gallery_lookup(gallery_items))

    if missing:
        print("Homepage gallery items could not be matched back to data/gallery.json:")
        for name in missing:
            print(f"- {name}")
        return 1

    rendered = render_payload(rebuilt_items)
    existing = args.homepage.read_text(encoding="utf-8")

    if args.check:
        if existing != rendered:
            print(f"Homepage gallery payload is out of date: {args.homepage}")
            return 1
        print(f"Homepage gallery payload is current: {args.homepage}")
        return 0

    args.homepage.write_text(rendered, encoding="utf-8")
    print(f"Updated {args.homepage}")
    print(f"Homepage items rebuilt: {len(rebuilt_items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
