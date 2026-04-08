#!/usr/bin/env python3
"""
Generate or verify the tracked digest manifest used by news.html.

The site can read digests in both of these formats:
  - YYYY-MM-DD-digest.md
  - digest-YYYY-MM-DD.md

Keeping a manifest avoids expensive 404-heavy date probing on static hosting.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
NEWS_DIGESTS_DIR = PROJECT_DIR / "news-digests"
INDEX_PATH = NEWS_DIGESTS_DIR / "index.json"
DIGEST_PATTERN = re.compile(
    r"(?:(\d{4})-(\d{2})-(\d{2})-digest|digest-(\d{4})-(\d{2})-(\d{2}))\.md$"
)


def digest_sort_key(path: Path) -> tuple[int, str]:
    match = DIGEST_PATTERN.match(path.name)
    if not match:
        return (0, path.name)

    year = int(match.group(1) or match.group(4))
    month = int(match.group(2) or match.group(5))
    day = int(match.group(3) or match.group(6))
    return (year * 10000 + month * 100 + day, path.name)


def build_manifest() -> dict[str, list[str]]:
    digest_files = [
        path
        for path in NEWS_DIGESTS_DIR.glob("*.md")
        if DIGEST_PATTERN.match(path.name)
    ]
    ordered_files = [
        path.name
        for path in sorted(digest_files, key=digest_sort_key, reverse=True)
    ]
    return {"files": ordered_files}


def main() -> int:
    parser = argparse.ArgumentParser(description="Update or verify news-digests/index.json")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero when the manifest does not match the current digest files.",
    )
    args = parser.parse_args()

    manifest = build_manifest()
    rendered = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"

    if args.check:
        if not INDEX_PATH.exists():
            print(f"Missing manifest: {INDEX_PATH}")
            return 1

        existing = INDEX_PATH.read_text(encoding="utf-8")
        if existing != rendered:
            print("news-digests/index.json is out of date.")
            return 1

        print("news-digests/index.json is up to date.")
        return 0

    INDEX_PATH.write_text(rendered, encoding="utf-8")
    print(f"Updated {INDEX_PATH}")
    print(f"Digest files indexed: {len(manifest['files'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
