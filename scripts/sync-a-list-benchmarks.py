#!/usr/bin/env python3
"""
Sync the Axy Lusion A-List benchmark snapshot from the shared AI Resource Hub cache.

This keeps a structured, machine-readable copy of the shared creative benchmarks
inside the Axy Lusion repo without overwriting the current hand-tuned HTML pages.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = Path(r"W:\Websites\sites\ai-resource-hub\data\pg-cache\creative_benchmarks.json")
DEFAULT_OUTPUT = PROJECT_DIR / "data" / "a-list-benchmarks.json"
CATEGORY_ORDER = [
    "image_generation",
    "image_editing",
    "video_generation",
    "music_generation",
    "voice_tts",
    "3d_generation",
    "upscaling",
]
CATEGORY_TITLES = {
    "image_generation": "Image Generation",
    "image_editing": "Image Editing",
    "video_generation": "Video Generation",
    "music_generation": "Music Generation",
    "voice_tts": "Voice & TTS",
    "3d_generation": "3D Generation",
    "upscaling": "Upscaling",
}
SOURCE_ORDER = {
    "Artificial Analysis": 0,
    "LM Arena": 1,
    "LLM Stats": 2,
    "Expert Review": 3,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Path to creative_benchmarks.json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Path to write the normalized A-List snapshot")
    parser.add_argument("--check", action="store_true", help="Exit non-zero if the output file is out of date")
    return parser.parse_args()


def to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None


def take_text(current: str, new_value: Any) -> str:
    if current:
        return current
    if isinstance(new_value, str):
        return new_value.strip()
    return current


def take_list(current: list[str], new_value: Any) -> list[str]:
    if current:
        return current
    if isinstance(new_value, list):
        values = [str(item).strip() for item in new_value if str(item).strip()]
        return values
    return current


def sort_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        sources,
        key=lambda source: (
            SOURCE_ORDER.get(str(source.get("source_name") or ""), 99),
            -(to_float(source.get("raw_score")) or 0.0),
            str(source.get("source_name") or ""),
        ),
    )


def build_snapshot(rows: list[dict[str, Any]], source_path: Path) -> dict[str, Any]:
    grouped_models: dict[tuple[str, str], dict[str, Any]] = {}

    for row in rows:
        category = str(row.get("category") or "").strip()
        model_name = str(row.get("model_name") or "").strip()
        if not category or not model_name:
            continue

        key = (category, model_name)
        model = grouped_models.setdefault(
            key,
            {
                "model_name": model_name,
                "model_maker": "",
                "model_url": "",
                "pricing_note": "",
                "considerations": "",
                "strengths": [],
                "meta_rank": None,
                "meta_score": None,
                "updated_at": "",
                "sources": [],
            },
        )

        model["model_maker"] = take_text(model["model_maker"], row.get("model_maker"))
        model["model_url"] = take_text(model["model_url"], row.get("model_url"))
        model["pricing_note"] = take_text(model["pricing_note"], row.get("pricing_note"))
        model["considerations"] = take_text(model["considerations"], row.get("considerations"))
        model["strengths"] = take_list(model["strengths"], row.get("strengths"))

        meta_rank = to_int(row.get("meta_rank"))
        if model["meta_rank"] is None and meta_rank is not None:
            model["meta_rank"] = meta_rank

        meta_score = to_float(row.get("meta_score"))
        if model["meta_score"] is None and meta_score is not None:
            model["meta_score"] = meta_score

        updated_at = str(row.get("updated_at") or "").strip()
        if updated_at and updated_at > model["updated_at"]:
            model["updated_at"] = updated_at

        source_entry = {
            "source_name": str(row.get("source_name") or "").strip(),
            "source_url": str(row.get("source_url") or "").strip(),
            "raw_score": to_float(row.get("raw_score")),
            "score_type": str(row.get("score_type") or "").strip(),
        }
        if source_entry not in model["sources"]:
            model["sources"].append(source_entry)

    categories: list[dict[str, Any]] = []
    known_categories = {category for category, _model_name in grouped_models}
    for category in sorted(
        known_categories,
        key=lambda item: (CATEGORY_ORDER.index(item) if item in CATEGORY_ORDER else 999, item),
    ):
        models = []
        for (model_category, _model_name), model in grouped_models.items():
            if model_category != category:
                continue

            model_copy = dict(model)
            model_copy["sources"] = sort_sources(model_copy["sources"])
            models.append(model_copy)

        models.sort(
            key=lambda item: (
                item["meta_rank"] is None,
                item["meta_rank"] if item["meta_rank"] is not None else 999,
                -(item["meta_score"] if item["meta_score"] is not None else 0.0),
                item["model_name"].lower(),
            )
        )

        categories.append(
            {
                "slug": category,
                "title": CATEGORY_TITLES.get(category, category.replace("_", " ").title()),
                "model_count": len(models),
                "updated_at": max((model["updated_at"] for model in models), default=""),
                "models": models,
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_path": str(source_path),
        "source_row_count": len(rows),
        "category_count": len(categories),
        "model_count": sum(category["model_count"] for category in categories),
        "categories": categories,
    }


def render_snapshot(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def comparable_payload(payload: dict[str, Any]) -> dict[str, Any]:
    comparable = json.loads(json.dumps(payload))
    comparable.pop("generated_at", None)
    return comparable


def main() -> int:
    args = parse_args()
    if not args.source.exists():
        raise SystemExit(f"Shared benchmark cache not found: {args.source}")

    rows = json.loads(args.source.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise SystemExit(f"Expected a JSON array at {args.source}")

    payload = build_snapshot(rows, args.source)
    rendered = render_snapshot(payload)
    existing = args.output.read_text(encoding="utf-8") if args.output.exists() else ""

    if args.check:
        if not args.output.exists():
            print(f"A-List benchmark snapshot is missing: {args.output}")
            return 1

        existing_payload = json.loads(existing)
        if comparable_payload(existing_payload) != comparable_payload(payload):
            print(f"A-List benchmark snapshot is out of date: {args.output}")
            return 1
        print(f"A-List benchmark snapshot is current: {args.output}")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"Wrote {args.output}")
    print(f"Categories: {payload['category_count']}")
    print(f"Models: {payload['model_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
