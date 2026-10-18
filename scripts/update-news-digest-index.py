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


# Header written by the shared news router, e.g. "**2026-10-18** | 0 stories | ...".
EMPTY_DIGEST_PATTERN = re.compile(r"^\*\*\d{4}-\d{2}-\d{2}\*\*\s*\|\s*0\s+stories\b", re.MULTILINE)


def is_empty_digest(path: Path) -> bool:
    """True only when the routed digest header explicitly reports 0 stories."""
    text = path.read_text(encoding="utf-8-sig", errors="ignore")
    return bool(EMPTY_DIGEST_PATTERN.search(text))


def build_manifest(log_skips: bool = False) -> dict[str, list[str]]:
    all_digest_files = [
        path for path in NEWS_DIGESTS_DIR.glob("*.md") if DIGEST_PATTERN.match(path.name)
    ]
    # The scheduled shared news filter writes new local digest files before
    # publication, so the live preview manifest must reflect files on disk.
    # Digests whose header reports 0 stories stay on disk but are not indexed,
    # so an empty upstream route never surfaces on news.html.
    digest_files = []
    for path in all_digest_files:
        if is_empty_digest(path):
            if log_skips:
                print(f"Skipping empty digest (0 stories), not indexed: news-digests/{path.name}")
            continue
        digest_files.append(path)
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

    manifest = build_manifest(log_skips=not args.check)
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
