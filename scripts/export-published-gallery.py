#!/usr/bin/env python3
"""
Rebuild the Axy Lusion website gallery export from the published Midjourney archive.

The current upstream inventory lives in universal.db. The current site export still
contains richer display metadata for created dates, model labels, and tags, so this
script merges rather than blindly overwrites.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = Path(r"W:\Agent Workspace\System\Data\universal.db")
GALLERY_JSON_PATH = PROJECT_DIR / "data" / "gallery.json"
GALLERY_JS_PATH = PROJECT_DIR / "gallery.js"
REPORT_PATH = PROJECT_DIR / "data" / "published-gallery-sync-report.json"


def load_existing_export(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return list(payload.get("items", []))
    return list(payload)


def run_checkpoint(connection: sqlite3.Connection) -> list[Any] | None:
    try:
        row = connection.execute("PRAGMA wal_checkpoint(FULL)").fetchone()
        return list(row) if row is not None else None
    except sqlite3.DatabaseError:
        return None


def load_db_items(db_path: Path, checkpoint: bool) -> tuple[list[dict[str, Any]], dict[str, list[str]], list[Any] | None]:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    checkpoint_result = run_checkpoint(connection) if checkpoint else None

    item_rows = connection.execute(
        """
        SELECT
            id,
            name,
            type,
            source,
            model,
            url,
            cdn_url,
            thumbnail_url,
            prompt,
            parameters,
            dimensions,
            status,
            created,
            created_at,
            updated_at,
            deleted_at
        FROM gallery_items
        WHERE source = 'midjourney'
          AND status = 'published'
          AND deleted_at IS NULL
        ORDER BY created_at ASC, id ASC
        """
    ).fetchall()

    tag_rows = connection.execute(
        """
        SELECT item_id, tag
        FROM gallery_tags
        ORDER BY item_id ASC, tag ASC
        """
    ).fetchall()
    connection.close()

    tags_by_item: dict[str, list[str]] = {}
    for row in tag_rows:
        tags_by_item.setdefault(row["item_id"], []).append(row["tag"])

    return [dict(row) for row in item_rows], tags_by_item, checkpoint_result


def unique_strings(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        cleaned = value.strip()
        if not cleaned:
            continue
        lowered = cleaned.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        output.append(cleaned)
    return output


def infer_model(parameters: str) -> str:
    match = re.search(r"--v(?:ersion)?\s+([0-9.]+)", parameters)
    if not match:
        return ""
    return f"Midjourney v{match.group(1)}"


def choose_model(db_item: dict[str, Any], existing_item: dict[str, Any]) -> str:
    db_model = str(db_item.get("model") or "").strip()
    if db_model:
        return db_model

    inferred = infer_model(str(db_item.get("parameters") or ""))
    if inferred:
        return inferred

    existing_model = str(existing_item.get("model") or "").strip()
    if existing_model:
        return existing_model

    return ""


def choose_created(db_item: dict[str, Any], existing_item: dict[str, Any]) -> str:
    db_created = str(db_item.get("created") or "").strip()
    if db_created:
        return db_created
    return str(existing_item.get("created") or "").strip()


def choose_tags(existing_item: dict[str, Any], db_tags: list[str]) -> list[str]:
    existing_tags = existing_item.get("tags") or []
    return unique_strings(list(existing_tags) + list(db_tags))


def merge_item(db_item: dict[str, Any], existing_item: dict[str, Any], db_tags: list[str]) -> dict[str, Any]:
    existing_item = existing_item or {}
    existing_name = existing_item.get("name")
    if isinstance(existing_name, str) and existing_name:
        name = existing_name
    else:
        name = str(db_item.get("name") or "").strip()

    merged: dict[str, Any] = {
        "id": db_item["id"],
        "name": name,
        "type": str(db_item.get("type") or existing_item.get("type") or "").strip(),
        "source": str(db_item.get("source") or existing_item.get("source") or "").strip(),
        "model": choose_model(db_item, existing_item),
        "url": str(db_item.get("url") or existing_item.get("url") or "").strip(),
        "cdn_url": str(db_item.get("cdn_url") or existing_item.get("cdn_url") or "").strip(),
        "prompt": str(db_item.get("prompt") or existing_item.get("prompt") or "").strip(),
        "parameters": str(db_item.get("parameters") or existing_item.get("parameters") or "").strip(),
        "dimensions": str(db_item.get("dimensions") or existing_item.get("dimensions") or "").strip(),
        "created": choose_created(db_item, existing_item),
        "tags": choose_tags(existing_item, db_tags),
    }

    thumbnail_url = str(db_item.get("thumbnail_url") or existing_item.get("thumbnail_url") or "").strip()
    if thumbnail_url or "thumbnail_url" in existing_item:
        merged["thumbnail_url"] = thumbnail_url

    for key, value in existing_item.items():
        if key not in merged:
            merged[key] = value

    return merged


def render_gallery_json(items: list[dict[str, Any]]) -> str:
    return json.dumps({"items": items}, indent=2, ensure_ascii=False) + "\n"


def update_gallery_js(items: list[dict[str, Any]], path: Path, apply_changes: bool) -> bool:
    content = path.read_text(encoding="utf-8")
    start_marker = "const embeddedData = {"
    start_index = content.find(start_marker)
    if start_index == -1:
        raise RuntimeError("Could not find embeddedData block in gallery.js")

    brace_index = start_index + len(start_marker) - 1
    brace_count = 0
    end_index = brace_index
    for index in range(brace_index, len(content)):
        if content[index] == "{":
            brace_count += 1
        elif content[index] == "}":
            brace_count -= 1
            if brace_count == 0:
                end_index = index + 1
                break

    if end_index < len(content) and content[end_index] == ";":
        end_index += 1

    replacement = f"const embeddedData = {json.dumps({'items': items}, indent=2, ensure_ascii=False)};"
    new_content = content[:start_index] + replacement + content[end_index:]

    changed = new_content != content
    if apply_changes and changed:
        path.write_text(new_content, encoding="utf-8")
    return changed


def write_if_changed(path: Path, content: str, apply_changes: bool) -> bool:
    existing = path.read_text(encoding="utf-8")
    changed = existing != content
    if apply_changes and changed:
        path.write_text(content, encoding="utf-8")
    return changed


def build_report(
    db_path: Path,
    checkpoint_result: list[Any] | None,
    existing_items: list[dict[str, Any]],
    db_items: list[dict[str, Any]],
    merged_items: list[dict[str, Any]],
    tags_by_item: dict[str, list[str]],
    json_changed: bool,
    js_changed: bool,
    apply_changes: bool,
) -> dict[str, Any]:
    existing_by_id = {item["id"]: item for item in existing_items}
    db_by_id = {item["id"]: item for item in db_items}

    json_only = sorted(set(existing_by_id) - set(db_by_id))
    db_only = sorted(set(db_by_id) - set(existing_by_id))
    merged_tag_counter = Counter(tag for item in merged_items for tag in (item.get("tags") or []))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db_path": str(db_path),
        "checkpoint_result": checkpoint_result,
        "apply_changes": apply_changes,
        "membership": {
            "existing_export_items": len(existing_items),
            "db_items": len(db_items),
            "merged_items": len(merged_items),
            "json_only": len(json_only),
            "db_only": len(db_only),
        },
        "drift": {
            "db_missing_model": sum(1 for item in db_items if not str(item.get("model") or "").strip()),
            "db_nonempty_created": sum(1 for item in db_items if str(item.get("created") or "").strip()),
            "db_missing_parameters": sum(1 for item in db_items if not str(item.get("parameters") or "").strip()),
            "db_tagged_items": len(tags_by_item),
            "export_nonempty_created": sum(1 for item in merged_items if str(item.get("created") or "").strip()),
            "export_placeholder_created_2026_02_10": sum(1 for item in merged_items if item.get("created") == "2026-02-10"),
            "export_missing_parameters": sum(1 for item in merged_items if not str(item.get("parameters") or "").strip()),
            "export_tagged_items": sum(1 for item in merged_items if item.get("tags")),
        },
        "top_models": Counter((item.get("model") or "__EMPTY__") for item in merged_items).most_common(8),
        "top_created": Counter((item.get("created") or "__EMPTY__") for item in merged_items).most_common(8),
        "top_tags": merged_tag_counter.most_common(12),
        "file_actions": {
            "gallery_json_would_change": json_changed,
            "gallery_js_would_change": js_changed,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild the published Midjourney gallery export for Axy Lusion.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Path to universal.db")
    parser.add_argument("--apply", action="store_true", help="Write gallery.json and gallery.js")
    parser.add_argument("--skip-checkpoint", action="store_true", help="Skip PRAGMA wal_checkpoint(FULL)")
    parser.add_argument("--report-path", type=Path, default=REPORT_PATH, help="Where to write the sync report JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    existing_items = load_existing_export(GALLERY_JSON_PATH)
    db_items, tags_by_item, checkpoint_result = load_db_items(args.db, checkpoint=not args.skip_checkpoint)

    existing_by_id = {item["id"]: item for item in existing_items}
    ordered_ids = [item["id"] for item in existing_items if item["id"] in {row["id"] for row in db_items}]
    ordered_ids.extend(row["id"] for row in db_items if row["id"] not in existing_by_id)

    db_by_id = {item["id"]: item for item in db_items}
    merged_items = [
        merge_item(db_by_id[item_id], existing_by_id.get(item_id, {}), tags_by_item.get(item_id, []))
        for item_id in ordered_ids
    ]

    gallery_json_changed = write_if_changed(
        GALLERY_JSON_PATH,
        render_gallery_json(merged_items),
        apply_changes=args.apply,
    )
    gallery_js_changed = update_gallery_js(merged_items, GALLERY_JS_PATH, apply_changes=args.apply)

    report = build_report(
        db_path=args.db,
        checkpoint_result=checkpoint_result,
        existing_items=existing_items,
        db_items=db_items,
        merged_items=merged_items,
        tags_by_item=tags_by_item,
        json_changed=gallery_json_changed,
        js_changed=gallery_js_changed,
        apply_changes=args.apply,
    )
    args.report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("Published gallery sync summary")
    print("=" * 40)
    print(f"DB path: {args.db}")
    print(f"Items in DB: {report['membership']['db_items']}")
    print(f"Items in export: {report['membership']['merged_items']}")
    print(f"DB tagged items: {report['drift']['db_tagged_items']}")
    print(f"Export tagged items: {report['drift']['export_tagged_items']}")
    print(f"Export placeholder date count (2026-02-10): {report['drift']['export_placeholder_created_2026_02_10']}")
    print(f"gallery.json would change: {report['file_actions']['gallery_json_would_change']}")
    print(f"gallery.js would change: {report['file_actions']['gallery_js_would_change']}")
    print(f"Report written to: {args.report_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
