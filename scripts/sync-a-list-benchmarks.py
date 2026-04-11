#!/usr/bin/env python3
"""
Sync the Axy Lusion A-List benchmark snapshot from the shared AI Resource Hub cache.

This snapshot is intentionally presentation-layer only:
  - the shared AI Resource Hub cache remains the source of truth
  - Axy Lusion normalizes names and notes for its own public delivery
  - we recompute the local meta-score so the rendered HTML stays explainable
  - no live scraping happens here; upstream acquisition belongs in AI Resource Hub
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from html import unescape


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
    "Expert Review": 2,
}
CATEGORY_CONFIG: dict[str, dict[str, Any]] = {
    "image_generation": {
        "weights": {"Artificial Analysis": 60, "LM Arena": 15, "Expert Review": 25},
        "note": (
            "Public arenas reward instruction following and pairwise preference voting. "
            "Web-only tools like Midjourney are still shown, but limited benchmark coverage "
            "reduces their composite score."
        ),
    },
    "image_editing": {
        "weights": {"Artificial Analysis": 70, "Expert Review": 30},
        "note": (
            "This category is benchmark-led. Studio/editorial tools can still appear, "
            "but models without public arena coverage are marked as limited-signal picks."
        ),
    },
    "video_generation": {
        "weights": {"Artificial Analysis": 70, "Expert Review": 30},
        "note": (
            "Video rankings still blend public arena results with studio judgement because "
            "provider access and feature sets move faster than stable public comparisons."
        ),
    },
    "music_generation": {
        "weights": {"Artificial Analysis": 80, "Expert Review": 20},
        "note": (
            "Public music leaderboards can lag behind provider version labels. For example, "
            "Suno has since announced v5.5, while benchmark pages still reference v4.5 and v5."
        ),
    },
    "voice_tts": {
        "weights": {"Artificial Analysis": 70, "Expert Review": 30},
        "note": "Voice rankings use public arena scores where available, then layer in studio judgement.",
    },
    "3d_generation": {
        "weights": {"Expert Review": 100},
        "note": "3D tools remain editorially ranked because public arena coverage is still thin.",
    },
    "upscaling": {
        "weights": {"Expert Review": 100},
        "note": "Upscaling remains an editorial category focused on practical creative output.",
    },
}
MODEL_ALIASES = {
    "GPT Image 1.5 (high)": "GPT Image 1.5",
    "Gemini 3 Pro Image": "Nano Banana Pro",
    "Nano Banana Pro (Gemini 3 Pro Image)": "Nano Banana Pro",
    "Gemini 3.1 Flash Image Preview": "Nano Banana 2",
    "Nano Banana 2 (Gemini 3.1 Flash Image Preview)": "Nano Banana 2",
    "FLUX.2 [max]": "Flux 2 Max",
    "Suno v4.5": "Suno V4.5",
    "Suno v5": "Suno V5",
    "grok-imagine-image": "Grok Imagine",
    "HunyuanImage 3.0 Instruct (Fal)": "HunyuanImage 3.0 Instruct",
    "Runway Gen-4.5": "Runway Gen-4.5",
}
MODEL_METADATA: dict[str, dict[str, Any]] = {
    "GPT Image 1.5": {
        "model_maker": "OpenAI",
        "model_url": "https://openai.com/chatgpt",
        "pricing_note": "ChatGPT plans",
        "strengths": ["Instruction following", "Text rendering", "Editing depth"],
        "considerations": "Best quality sits behind paid ChatGPT tiers.",
    },
    "Nano Banana 2": {
        "model_maker": "Google",
        "model_url": "https://deepmind.google/technologies/gemini/",
        "pricing_note": "Gemini surfaces / API access",
        "strengths": ["Fast prompt following", "Image generation", "Editing agility"],
        "considerations": "Branding varies across Google surfaces; public benchmarks often use the Nano Banana name.",
    },
    "Nano Banana Pro": {
        "model_maker": "Google",
        "model_url": "https://deepmind.google/technologies/gemini/",
        "pricing_note": "Gemini surfaces / API access",
        "strengths": ["Precise edits", "Prompt fidelity", "Fast iteration"],
        "considerations": "Often referred to publicly as Gemini 3 Pro Image or Nano Banana Pro.",
    },
    "Flux 2 Max": {
        "model_maker": "Black Forest Labs",
        "model_url": "https://blackforestlabs.ai",
        "pricing_note": "API / partner access",
        "strengths": ["Photorealism", "Flexible workflows", "Strong benchmark showings"],
        "considerations": "Experience varies by host platform.",
    },
    "Midjourney v7": {
        "model_maker": "Midjourney",
        "model_url": "https://www.midjourney.com",
        "pricing_note": "From $10/mo",
        "strengths": ["Aesthetic quality", "Cinematic style", "Distinctive taste"],
        "considerations": "Web-only workflow with limited benchmark participation and no public API.",
    },
    "Seedream 4.0": {
        "model_maker": "ByteDance",
        "model_url": "https://dreamina.capcut.com/",
        "pricing_note": "Platform pricing varies",
        "strengths": ["Strong public benchmark momentum", "General-purpose generation"],
        "considerations": "Availability depends on platform region and host product.",
    },
    "Reve Image": {
        "model_maker": "Reve",
        "model_url": "https://www.reveimage.com",
        "pricing_note": "Pay per generation",
        "strengths": ["Fast rise", "Strong realism"],
        "considerations": "Position is still stabilizing as the product matures.",
    },
    "Grok Imagine": {
        "model_maker": "xAI",
        "model_url": "https://x.ai",
        "pricing_note": "xAI / X plan access",
        "strengths": ["Editing momentum", "Fast iterations"],
        "considerations": "Availability depends on xAI product access.",
    },
    "HunyuanImage 3.0 Instruct": {
        "model_maker": "Tencent",
        "model_url": "https://www.tencent.com",
        "pricing_note": "Partner / hosted access",
        "strengths": ["Editing fidelity", "Instruction following"],
        "considerations": "Most creators encounter it through third-party hosts.",
    },
    "Runway Gen-4.5": {
        "model_maker": "Runway",
        "model_url": "https://runwayml.com",
        "pricing_note": "Free tier / paid plans",
        "strengths": ["Cinematic motion", "Control", "Creator familiarity"],
        "considerations": "Credits can disappear quickly on heavier workflows.",
    },
    "Seedance 2.0": {
        "model_maker": "ByteDance",
        "model_url": "https://dreamina.capcut.com/",
        "pricing_note": "Platform pricing varies",
        "strengths": ["Motion quality", "Audio-aware generation"],
        "considerations": "Naming and access vary by host platform.",
    },
    "Kling 3.0": {
        "model_maker": "Kuaishou",
        "model_url": "https://klingai.com",
        "pricing_note": "Credits / plans",
        "strengths": ["Duration", "Value", "Popular creator workflow"],
        "considerations": "Model lineup changes quickly and naming is crowded.",
    },
    "Veo 3.1": {
        "model_maker": "Google",
        "model_url": "https://deepmind.google/technologies/veo/",
        "pricing_note": "Google ecosystem access",
        "strengths": ["Video quality", "Audio features"],
        "considerations": "Availability depends on Google surface and region.",
    },
    "Sora 2": {
        "model_maker": "OpenAI",
        "model_url": "https://openai.com/sora",
        "pricing_note": "OpenAI product access",
        "strengths": ["Cinematic coherence", "Brand recognition"],
        "considerations": (
            "OpenAI says Sora access on the web and in ChatGPT ends on April 26, 2026; "
            "Sora API access continues until September 24, 2026. Consumer availability also varies by region and plan."
        ),
    },
    "Mureka V8": {
        "model_maker": "Mureka",
        "model_url": "https://www.mureka.ai",
        "pricing_note": "Platform pricing varies",
        "strengths": ["Benchmark-leading vocals", "Fresh public momentum"],
        "considerations": "Less established in everyday creator conversations than Suno or Udio.",
    },
    "MiniMax Music 2.5": {
        "model_maker": "MiniMax",
        "model_url": "https://www.minimax.io",
        "pricing_note": "Platform pricing varies",
        "strengths": ["Benchmark strength", "Strong vocal output"],
        "considerations": "Discovery and access are less mainstream than Suno/Udio.",
    },
    "Lyria 3 Pro": {
        "model_maker": "Google DeepMind",
        "model_url": "https://deepmind.google/technologies/lyria/",
        "pricing_note": "Google ecosystem access",
        "strengths": ["Benchmark quality", "Google audio stack"],
        "considerations": "Availability depends on Google rollout and product surface.",
    },
    "Suno V4.5": {
        "model_maker": "Suno",
        "model_url": "https://suno.com",
        "pricing_note": "Free tier / paid plans",
        "strengths": ["Creator familiarity", "Song completeness"],
        "considerations": "Public benchmarks still reference V4.5 while Suno has since announced V5.5.",
    },
    "Suno V5": {
        "model_maker": "Suno",
        "model_url": "https://suno.com",
        "pricing_note": "Free tier / paid plans",
        "strengths": ["Updated Suno line", "Song workflow"],
        "considerations": "Public benchmarks still trail the latest Suno branding and version cadence.",
    },
    "Udio": {
        "model_maker": "Udio",
        "model_url": "https://www.udio.com",
        "pricing_note": "Free tier / paid plans",
        "strengths": ["Vocals", "Stylistic control"],
        "considerations": "Public arena coverage is still patchier than its creator reputation.",
    },
    "AIVA": {
        "model_maker": "AIVA",
        "model_url": "https://www.aiva.ai",
        "pricing_note": "Paid plans",
        "strengths": ["Instrumentals", "Composition support"],
        "considerations": "Feels more niche than current mainstream AI song tools.",
    },
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


def canonicalize_model_name(name: Any) -> str:
    if not isinstance(name, str):
        return ""
    stripped = unescape(name).strip()
    return MODEL_ALIASES.get(stripped, stripped)


def merge_metadata(row: dict[str, Any]) -> dict[str, Any]:
    model_name = canonicalize_model_name(row.get("model_name"))
    row["model_name"] = model_name
    metadata = MODEL_METADATA.get(model_name, {})

    if metadata.get("model_maker"):
        row["model_maker"] = metadata["model_maker"]
    elif isinstance(row.get("model_maker"), str):
        row["model_maker"] = row["model_maker"].strip()
    else:
        row["model_maker"] = ""

    if metadata.get("model_url"):
        row["model_url"] = metadata["model_url"]
    else:
        row["model_url"] = take_text(str(row.get("model_url") or ""), row.get("model_url"))

    if metadata.get("pricing_note") and not str(row.get("pricing_note") or "").strip():
        row["pricing_note"] = metadata["pricing_note"]
    else:
        row["pricing_note"] = str(row.get("pricing_note") or "").strip()

    row["considerations"] = str(row.get("considerations") or "").strip() or metadata.get("considerations", "")
    row["strengths"] = take_list([], row.get("strengths")) or list(metadata.get("strengths", []))
    row["status_note"] = str(row.get("status_note") or "").strip() or metadata.get("status_note", "")

    return row


def normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized_rows: list[dict[str, Any]] = []
    for raw_row in rows:
        row = dict(raw_row)
        row = merge_metadata(row)
        normalized_rows.append(row)
    return normalized_rows


def sort_sources(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        sources,
        key=lambda source: (
            SOURCE_ORDER.get(str(source.get("source_name") or ""), 99),
            -(to_float(source.get("raw_score")) or 0.0),
            str(source.get("source_name") or ""),
        ),
    )


def normalize_source_score(raw_score: float | None, score_type: str, source_values: list[float]) -> float | None:
    if raw_score is None:
        return None
    if score_type == "score_100":
        return max(0.0, min(100.0, raw_score))
    if score_type == "elo":
        if not source_values:
            return None
        ranked_values = sorted({round(value, 6) for value in source_values}, reverse=True)
        if len(ranked_values) == 1:
            return 100.0
        try:
            rank_index = ranked_values.index(round(raw_score, 6))
        except ValueError:
            return None
        return 100.0 - (rank_index * (50.0 / (len(ranked_values) - 1)))
    return raw_score


def coverage_label(percent: float) -> str:
    if percent >= 95:
        return "Full signal"
    if percent >= 70:
        return "Strong signal"
    if percent >= 45:
        return "Partial signal"
    return "Editorial signal"


def rank_category_models(models: list[dict[str, Any]], weights: dict[str, int]) -> list[dict[str, Any]]:
    source_values: dict[str, list[float]] = {}
    total_weight = float(sum(weights.values()) or 100)

    for model in models:
        for source in model["sources"]:
            score = to_float(source.get("raw_score"))
            if score is None:
                continue
            source_name = str(source.get("source_name") or "")
            source_values.setdefault(source_name, []).append(score)

    ranked_models: list[dict[str, Any]] = []
    for model in models:
        weighted_sum = 0.0
        present_weight = 0.0

        for source in model["sources"]:
            source_name = str(source.get("source_name") or "")
            if source_name not in weights:
                continue
            raw_score = to_float(source.get("raw_score"))
            normalized_score = normalize_source_score(
                raw_score=raw_score,
                score_type=str(source.get("score_type") or ""),
                source_values=source_values.get(source_name, []),
            )
            source["normalized_score"] = round(normalized_score, 2) if normalized_score is not None else None
            if normalized_score is None:
                continue
            source_weight = float(weights[source_name])
            weighted_sum += normalized_score * source_weight
            present_weight += source_weight

        if present_weight:
            average_score = weighted_sum / present_weight
            coverage_factor = 0.45 + 0.55 * (present_weight / total_weight)
            meta_score = round(average_score * coverage_factor, 2)
        else:
            meta_score = 0.0

        coverage_percent = round((present_weight / total_weight) * 100.0, 2) if total_weight else 0.0
        model["meta_score"] = meta_score
        model["coverage_weight"] = round(present_weight, 2)
        model["coverage_percent"] = coverage_percent
        model["coverage_label"] = coverage_label(coverage_percent)
        ranked_models.append(model)

    ranked_models.sort(
        key=lambda item: (
            -(item.get("meta_score") or 0.0),
            -(item.get("coverage_percent") or 0.0),
            item["model_name"].lower(),
        )
    )
    for index, model in enumerate(ranked_models, start=1):
        model["meta_rank"] = index
    return ranked_models


def build_snapshot(rows: list[dict[str, Any]], source_path: Path) -> dict[str, Any]:
    grouped_models: dict[tuple[str, str], dict[str, Any]] = {}

    for row in rows:
        category = str(row.get("category") or "").strip()
        model_name = canonicalize_model_name(row.get("model_name"))
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
                "status_note": "",
                "strengths": [],
                "meta_rank": None,
                "meta_score": None,
                "coverage_weight": 0.0,
                "coverage_percent": 0.0,
                "coverage_label": "",
                "updated_at": "",
                "sources": [],
            },
        )

        model["model_maker"] = take_text(model["model_maker"], row.get("model_maker"))
        model["model_url"] = take_text(model["model_url"], row.get("model_url"))
        model["pricing_note"] = take_text(model["pricing_note"], row.get("pricing_note"))
        model["considerations"] = take_text(model["considerations"], row.get("considerations"))
        model["status_note"] = take_text(model["status_note"], row.get("status_note"))
        model["strengths"] = take_list(model["strengths"], row.get("strengths"))

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

        ranked_models = rank_category_models(models, CATEGORY_CONFIG.get(category, {}).get("weights", {"Expert Review": 100}))
        categories.append(
            {
                "slug": category,
                "title": CATEGORY_TITLES.get(category, category.replace("_", " ").title()),
                "model_count": len(ranked_models),
                "updated_at": max((model["updated_at"] for model in ranked_models), default=""),
                "note": CATEGORY_CONFIG.get(category, {}).get("note", ""),
                "weights": CATEGORY_CONFIG.get(category, {}).get("weights", {}),
                "models": ranked_models,
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_path": str(source_path),
        "source_row_count": len(rows),
        "category_count": len(categories),
        "model_count": sum(category["model_count"] for category in categories),
        "methodology_note": (
            "This snapshot blends public benchmark signals where we can verify them and editorial "
            "studio scoring where public coverage is sparse. Coverage is shown per model so the "
            "page stays honest about what is benchmark-led versus curated."
        ),
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

    normalized_rows = normalize_rows(rows)
    payload = build_snapshot(normalized_rows, args.source)
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

    if args.output.exists():
        existing_payload = json.loads(existing)
        if comparable_payload(existing_payload) == comparable_payload(payload):
            print(f"No benchmark changes detected: {args.output}")
            return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"Wrote {args.output}")
    print(f"Categories: {payload['category_count']}")
    print(f"Models: {payload['model_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
