#!/usr/bin/env python3
"""Copy the public A-List from current Artificial Analysis leaderboards.

The shared AI Resource Hub cache is only a score source when its measurements
are current. This script reads the published Elo values from the public
leaderboard payloads. It does not invent scores, and it does not keep studio
or editorial scores in the public snapshot.
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent.parent
CAPTURE_PATH = PROJECT_DIR / "data" / "aa-leaderboard-capture.json"
SNAPSHOT_PATH = PROJECT_DIR / "data" / "a-list-benchmarks.json"
USER_AGENT = "AxyLusion-AList/1.0 (public leaderboard refresh)"
AA_ORIGIN = "https://artificialanalysis.ai"

BOARDS: list[dict[str, str]] = [
    {
        "slug": "image_generation",
        "title": "Image Generation",
        "url": f"{AA_ORIGIN}/image/leaderboard/text-to-image",
        "fallback_board_name": "AA-Image-T2I v2.1",
        "note": (
            "Overall text-to-image Elo from the Artificial Analysis leaderboard. "
            "The number shown is the published Elo. No studio score is added."
        ),
    },
    {
        "slug": "image_editing",
        "title": "Image Editing",
        "url": f"{AA_ORIGIN}/image/leaderboard/editing",
        "fallback_board_name": "AA-Image-Editing v2.1",
        "note": (
            "Overall image-editing Elo from the Artificial Analysis leaderboard. "
            "The number shown is the published Elo. No studio score is added."
        ),
    },
    {
        "slug": "video_generation",
        "title": "Video Generation",
        "url": f"{AA_ORIGIN}/video/leaderboard/text-to-video",
        "fallback_board_name": "AA-Video-T2V v2.1",
        "note": (
            "Text-to-video Elo from the Artificial Analysis leaderboard. "
            "Image-to-video is a separate board and is not mixed into these scores. "
            "No studio score is added."
        ),
    },
    {
        "slug": "voice_tts",
        "title": "Voice & TTS",
        "url": f"{AA_ORIGIN}/text-to-speech/leaderboard/provider-voice",
        "fallback_board_name": "Text to Speech",
        "note": (
            "Text-to-speech Elo from the Artificial Analysis provider-voice leaderboard. "
            "The number shown is the published Elo. No studio score is added."
        ),
    },
]

OMITTED_CATEGORIES = [
    {
        "slug": "music_generation",
        "title": "Music Generation",
        "reason": (
            "The Artificial Analysis music arena did not publish an Elo leaderboard "
            "on this retrieval. Older editorial music scores are not shown."
        ),
    },
    {
        "slug": "3d_generation",
        "title": "3D Generation",
        "reason": (
            "No current public Elo leaderboard was available. Older editorial 3D scores are not shown."
        ),
    },
    {
        "slug": "upscaling",
        "title": "Upscaling",
        "reason": (
            "No current public Elo leaderboard was available. Older editorial upscaling scores are not shown."
        ),
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare the snapshot with the committed capture. Does not fetch.")
    parser.add_argument("--capture", type=Path, default=CAPTURE_PATH)
    parser.add_argument("--output", type=Path, default=SNAPSHOT_PATH)
    return parser.parse_args()


def fetch_text(url: str, accept: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": accept,
            "RSC": "1",
        },
    )
    with urllib.request.urlopen(request, timeout=40) as response:
        return response.read().decode("utf-8", "replace")


def fetch_title(url: str) -> str:
    html = fetch_text(url, "text/html")
    match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()


def board_name_from_title(title: str, fallback: str) -> str:
    if " Leaderboard" in title:
        name = title.split(" Leaderboard", 1)[0].strip()
        if name:
            return name
    return fallback


def parse_object(text: str, start: int) -> tuple[Any, int]:
    if start < 0 or start >= len(text) or text[start] != "{":
        raise ValueError("JSON object did not start at the expected position")
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : index + 1]), index + 1
    raise ValueError("Unterminated JSON object in leaderboard payload")


def extract_overall_models(body: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    marker = "[[null,["
    start = body.find(marker)
    if start < 0:
        raise ValueError("Overall leaderboard payload was not found")
    rest = body[start:]
    boundary = re.search(r'\]\],\["[a-z0-9-]+",\[', rest)
    chunk = rest[: boundary.start()] if boundary else rest
    models: list[tuple[dict[str, Any], dict[str, Any]]] = []
    cursor = 0
    while True:
        formatted_at = chunk.find('"formatted":', cursor)
        if formatted_at < 0:
            break
        formatted_brace = chunk.find("{", formatted_at)
        formatted, formatted_end = parse_object(chunk, formatted_brace)
        values_at = chunk.find('"values":', formatted_end)
        if values_at < 0 or values_at > formatted_end + 30:
            cursor = formatted_end
            continue
        values_brace = chunk.find("{", values_at)
        values, values_end = parse_object(chunk, values_brace)
        if isinstance(formatted, dict) and isinstance(values, dict):
            models.append((formatted, values))
        cursor = values_end
    if not models:
        raise ValueError("Overall leaderboard payload contained no models")
    return models


def as_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(round(value))
    if isinstance(value, str):
        stripped = value.replace(",", "").strip()
        if re.fullmatch(r"-?\d+", stripped):
            return int(stripped)
    return None


def display_elo(formatted: dict[str, Any], values: dict[str, Any]) -> int:
    displayed = as_int(formatted.get("elo"))
    if displayed is not None:
        return displayed
    exact = values.get("elo")
    if isinstance(exact, (int, float)) and not isinstance(exact, bool):
        return int(round(float(exact)))
    raise ValueError(f"Model {values.get('name')!r} has no published Elo")


def display_rank(formatted: dict[str, Any], index: int) -> int:
    rank = as_int(formatted.get("rank"))
    if rank is not None and rank > 0:
        return rank
    return index + 1


def clean_price(formatted: dict[str, Any], values: dict[str, Any]) -> str:
    pricing = formatted.get("apiPricing")
    if isinstance(pricing, str):
        text = pricing.strip()
        if text.startswith("$$"):
            text = "$" + text[2:]
        if text.startswith("$") and not text.startswith("$L"):
            return text
    per_image = values.get("pricePer1kImages")
    if isinstance(per_image, (int, float)) and not isinstance(per_image, bool):
        return f"${per_image:g} /1k imgs"
    per_minute = values.get("pricePerMinute")
    if isinstance(per_minute, (int, float)) and not isinstance(per_minute, bool):
        return f"${per_minute:g} /min"
    per_million = values.get("pricePer1mCharacters")
    if isinstance(per_million, (int, float)) and not isinstance(per_million, bool):
        return f"${per_million:g} /1M chars"
    return ""


def absolute_url(path: Any, fallback: str) -> str:
    if not isinstance(path, str) or not path.strip():
        return fallback
    value = path.strip()
    if value.startswith("https://"):
        return value
    if value.startswith("/"):
        return f"{AA_ORIGIN}{value}"
    return fallback


def round_exact(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return round(float(value), 2)


def normalize_models(pairs: list[tuple[dict[str, Any], dict[str, Any]]], source_url: str) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, (formatted, values) in enumerate(pairs):
        name = str(values.get("name") or "").strip()
        if not name:
            raise ValueError("Leaderboard row is missing a model name")
        elo = display_elo(formatted, values)
        if elo < 200 or elo > 5000:
            raise ValueError(f"Published Elo for {name} is outside the expected arena range: {elo}")
        creator = values.get("creator")
        maker = ""
        if isinstance(creator, dict):
            maker = str(creator.get("name") or "").strip()
        samples = as_int(values.get("appearances"))
        ci_delta = round_exact(values.get("ciDelta"))
        if ci_delta is not None and float(ci_delta).is_integer():
            ci_delta = int(ci_delta)
        released = str(values.get("releaseDate") or "").strip()
        normalized.append(
            {
                "rank": display_rank(formatted, index),
                "name": name,
                "maker": maker,
                "url": absolute_url(values.get("url"), source_url),
                "elo": elo,
                "elo_exact": round_exact(values.get("elo")),
                "ci_delta": ci_delta,
                "samples": samples,
                "released": released,
                "pricing": clean_price(formatted, values),
            }
        )
    normalized.sort(key=lambda item: (item["rank"], item["name"].lower()))
    ranks = [item["rank"] for item in normalized]
    if ranks != list(range(1, len(normalized) + 1)):
        raise ValueError(f"Leaderboard ranks were not contiguous: {ranks[:8]} ...")
    if len({item["name"] for item in normalized}) != len(normalized):
        raise ValueError("Leaderboard repeated a model name")
    return normalized


def english_date(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return f"{parsed.day} {parsed.strftime('%B %Y')}"


def format_release(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value
    return f"{parsed.day} {parsed.strftime('%b %Y')}"


def build_capture(retrieved_at: str) -> dict[str, Any]:
    boards: list[dict[str, Any]] = []
    for board in BOARDS:
        payload = fetch_text(board["url"], "text/x-component")
        title = fetch_title(board["url"])
        models = normalize_models(extract_overall_models(payload), board["url"])
        boards.append(
            {
                "slug": board["slug"],
                "title": board["title"],
                "board_name": board_name_from_title(title, board["fallback_board_name"]),
                "page_title": title,
                "source_url": board["url"],
                "note": board["note"],
                "model_count": len(models),
                "models": models,
            }
        )
    return {
        "retrieved_at": retrieved_at,
        "publisher": "Artificial Analysis",
        "boards": boards,
        "omitted_categories": OMITTED_CATEGORIES,
    }


def model_note(model: dict[str, Any]) -> str:
    parts: list[str] = []
    released = format_release(str(model.get("released") or ""))
    if released:
        parts.append(f"Released {released}")
    samples = model.get("samples")
    if isinstance(samples, int):
        parts.append(f"{samples:,} samples")
    ci_delta = model.get("ci_delta")
    if ci_delta is not None:
        parts.append(f"95% interval ±{ci_delta}")
    pricing = str(model.get("pricing") or "").strip()
    if pricing:
        parts.append(pricing)
    return ". ".join(parts) + ("." if parts else "")


def build_snapshot(capture: dict[str, Any]) -> dict[str, Any]:
    retrieved_at = str(capture.get("retrieved_at") or "")
    if not retrieved_at:
        raise ValueError("Capture is missing retrieved_at")
    categories: list[dict[str, Any]] = []
    for board in capture.get("boards", []):
        models_in = board.get("models") or []
        if not models_in:
            raise ValueError(f"Capture board {board.get('slug')} has no models")
        leader_elo = float(models_in[0]["elo"])
        models: list[dict[str, Any]] = []
        for model in models_in:
            elo = int(model["elo"])
            bar_percent = round((elo / leader_elo) * 100.0, 2) if leader_elo else 0.0
            source = {
                "source_name": "Artificial Analysis",
                "source_url": board["source_url"],
                "raw_score": elo,
                "score_type": "elo",
                "elo_exact": model.get("elo_exact"),
                "ci_delta": model.get("ci_delta"),
            }
            facts = [item for item in (format_release(str(model.get("released") or "")), str(model.get("pricing") or "")) if item]
            models.append(
                {
                    "model_name": model["name"],
                    "model_maker": model.get("maker") or "",
                    "model_url": model.get("url") or board["source_url"],
                    "pricing_note": model.get("pricing") or "",
                    "considerations": model_note(model),
                    "public_note": model_note(model),
                    "status_note": "",
                    "strengths": facts[:2],
                    "meta_rank": model["rank"],
                    "meta_score": elo,
                    "bar_percent": bar_percent,
                    "score_unit": "elo",
                    "coverage_weight": 100.0,
                    "coverage_percent": 100.0,
                    "coverage_label": "Arena Elo",
                    "updated_at": retrieved_at,
                    "sources": [source],
                }
            )
        categories.append(
            {
                "slug": board["slug"],
                "title": board["title"],
                "model_count": len(models),
                "updated_at": retrieved_at,
                "note": board.get("note") or "",
                "board_name": board.get("board_name") or "",
                "source_url": board["source_url"],
                "score_unit": "elo",
                "weights": {"Artificial Analysis": 100},
                "models": models,
            }
        )
    dated = english_date(retrieved_at)
    return {
        "generated_at": retrieved_at,
        "retrieved_at": retrieved_at,
        "publication_status": "current",
        "score_basis": "artificial_analysis_elo",
        "source_path": "data/aa-leaderboard-capture.json",
        "source_row_count": sum(category["model_count"] for category in categories),
        "category_count": len(categories),
        "model_count": sum(category["model_count"] for category in categories),
        "methodology_note": (
            f"Scores are the Elo published by Artificial Analysis, copied from the public leaderboards on {dated}. "
            "Each number is the board's displayed Elo. This page does not add a studio score, and it does not reuse "
            "the 24 August 2026 snapshot. Music, 3D, and upscaling are omitted because no current public Elo board was available."
        ),
        "categories": categories,
        "omitted_categories": capture.get("omitted_categories") or [],
    }


def render_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    args = parse_args()
    if args.check:
        if not args.capture.exists():
            print(f"A-List arena capture is missing: {args.capture}")
            return 1
        if not args.output.exists():
            print(f"A-List snapshot is missing: {args.output}")
            return 1
        capture = json.loads(args.capture.read_text(encoding="utf-8"))
        expected = build_snapshot(capture)
        actual = json.loads(args.output.read_text(encoding="utf-8"))
        if expected != actual:
            print(f"A-List snapshot does not match the arena capture: {args.output}")
            return 1
        print(f"A-List snapshot matches the arena capture: {args.output}")
        return 0

    retrieved_at = datetime.now(timezone.utc).isoformat()
    try:
        capture = build_capture(retrieved_at)
    except Exception as exc:
        print(f"Artificial Analysis refresh failed: {exc}")
        if args.capture.exists() and args.output.exists():
            print("Left the last captured leaderboard snapshot in place.")
            return 0
        return 1

    snapshot = build_snapshot(capture)
    args.capture.parent.mkdir(parents=True, exist_ok=True)
    args.capture.write_text(render_json(capture), encoding="utf-8")
    args.output.write_text(render_json(snapshot), encoding="utf-8")
    print(f"Wrote {args.capture}")
    print(f"Wrote {args.output}")
    for category in snapshot["categories"]:
        leader = category["models"][0]
        print(
            f"{category['title']}: {category['model_count']} models, "
            f"#{leader['meta_rank']} {leader['model_name']} Elo {leader['meta_score']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
