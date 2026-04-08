#!/usr/bin/env python3
"""
Static validation checks for the Axy Lusion repo.

Checks:
  - required JSON data files load and contain items
  - local href/src references resolve
  - digest manifest matches the files on disk

Warnings:
  - gallery/homepage payloads still reference Midjourney CDN URLs
"""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


PROJECT_DIR = Path(__file__).resolve().parent.parent
ROOT_HTML_FILES = sorted(PROJECT_DIR.glob("*.html"))
ADMIN_HTML_FILES = sorted((PROJECT_DIR / "admin").glob("*.html"))
ALIST_HTML_FILES = sorted((PROJECT_DIR / "a-list").glob("*.html"))
HTML_FILES = ROOT_HTML_FILES + ADMIN_HTML_FILES + ALIST_HTML_FILES
NEWS_DIGESTS_DIR = PROJECT_DIR / "news-digests"
INDEX_PATH = NEWS_DIGESTS_DIR / "index.json"
ALIST_DATA_PATH = PROJECT_DIR / "data" / "a-list-benchmarks.json"
DIGEST_PATTERN = re.compile(
    r"(?:(\d{4})-(\d{2})-(\d{2})-digest|digest-(\d{4})-(\d{2})-(\d{2}))\.md$"
)


class RefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[tuple[str, str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = dict(attrs)
        for key in ("href", "src"):
            value = attr_map.get(key)
            if value:
                self.refs.append((tag, key, value))


def load_json_items(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        items = payload.get("items", [])
    else:
        items = payload
    if not isinstance(items, list):
        raise ValueError(f"{path} does not contain a list of items")
    return items


def load_alist_snapshot(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} does not contain an object payload")

    categories = payload.get("categories", [])
    if not isinstance(categories, list):
        raise ValueError(f"{path} categories payload is not a list")

    return payload


def rel_path(path: Path) -> str:
    return str(path.relative_to(PROJECT_DIR)).replace("\\", "/")


def check_local_refs() -> list[str]:
    issues: list[str] = []

    for html_path in HTML_FILES:
        parser = RefParser()
        parser.feed(html_path.read_text(encoding="utf-8", errors="ignore"))

        for _tag, _attr, value in parser.refs:
            if value.startswith(("http://", "https://", "mailto:", "tel:", "javascript:", "#", "data:")):
                continue

            parsed = urlparse(value)
            path_part = parsed.path
            if path_part.startswith("/"):
                target = PROJECT_DIR / path_part.lstrip("/")
            else:
                target = (html_path.parent / path_part).resolve()

            if not target.exists():
                issues.append(
                    f"Missing local asset in {rel_path(html_path)}: {value}"
                )

    return issues


def build_digest_manifest() -> dict[str, list[str]]:
    digest_files = [
        path.name
        for path in NEWS_DIGESTS_DIR.glob("*.md")
        if DIGEST_PATTERN.match(path.name)
    ]
    digest_files.sort(
        key=lambda name: (
            int((match := DIGEST_PATTERN.match(name)).group(1) or match.group(4)),
            int(match.group(2) or match.group(5)),
            int(match.group(3) or match.group(6)),
            name,
        ),
        reverse=True,
    )
    return {"files": digest_files}


def check_digest_manifest() -> list[str]:
    issues: list[str] = []
    if not INDEX_PATH.exists():
        return [f"Missing digest manifest: {rel_path(INDEX_PATH)}"]

    expected = build_digest_manifest()
    try:
        actual = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"Invalid digest manifest JSON: {exc}"]

    if actual != expected:
        issues.append("news-digests/index.json is out of sync with the digest files on disk.")

    listed_files = actual.get("files", []) if isinstance(actual, dict) else []
    for filename in listed_files:
        if not (NEWS_DIGESTS_DIR / filename).exists():
            issues.append(f"Manifest entry does not exist on disk: news-digests/{filename}")

    return issues


def summarize_hosts(items: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        for key in ("cdn_url", "url", "image", "src"):
            value = item.get(key)
            if isinstance(value, str) and value.startswith("http"):
                host = value.split("/")[2]
                counts[host] = counts.get(host, 0) + 1
                break
    return counts


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []
    alist_category_count: int | None = None

    try:
        gallery_items = load_json_items(PROJECT_DIR / "data" / "gallery.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"Unable to load data/gallery.json: {exc}")
        gallery_items = []

    try:
        homepage_items = load_json_items(PROJECT_DIR / "data" / "homepage-gallery.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"Unable to load data/homepage-gallery.json: {exc}")
        homepage_items = []

    if ALIST_DATA_PATH.exists():
        try:
            alist_snapshot = load_alist_snapshot(ALIST_DATA_PATH)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            failures.append(f"Unable to load data/a-list-benchmarks.json: {exc}")
        else:
            categories = alist_snapshot.get("categories", [])
            alist_category_count = len(categories)
            if not categories:
                failures.append("data/a-list-benchmarks.json has no categories.")

    if not gallery_items:
        failures.append("data/gallery.json has no items.")
    if not homepage_items:
        failures.append("data/homepage-gallery.json has no items.")

    failures.extend(check_local_refs())
    failures.extend(check_digest_manifest())

    gallery_hosts = summarize_hosts(gallery_items)
    homepage_hosts = summarize_hosts(homepage_items)

    midjourney_gallery = gallery_hosts.get("cdn.midjourney.com", 0)
    midjourney_homepage = homepage_hosts.get("cdn.midjourney.com", 0)
    if midjourney_gallery:
        warnings.append(
            f"Gallery payload still references {midjourney_gallery} Midjourney CDN URLs."
        )
    if midjourney_homepage:
        warnings.append(
            f"Homepage payload still references {midjourney_homepage} Midjourney CDN URLs."
        )

    print("Axy Lusion validation summary")
    print("=" * 32)
    print(f"HTML files checked: {len(HTML_FILES)}")
    print(f"Gallery items: {len(gallery_items)}")
    print(f"Homepage items: {len(homepage_items)}")
    print(f"Digest files indexed: {len(build_digest_manifest()['files'])}")
    if alist_category_count is not None:
        print(f"A-List categories: {alist_category_count}")

    if warnings:
        print("\nWarnings")
        print("-" * 8)
        for warning in warnings:
            print(f"- {warning}")

    if failures:
        print("\nFailures")
        print("-" * 8)
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nAll structural checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
