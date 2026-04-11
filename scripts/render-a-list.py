#!/usr/bin/env python3
"""
Render the Axy Lusion A-List overview page and category detail pages from the
local benchmark snapshot.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = PROJECT_DIR / "data" / "a-list-benchmarks.json"
OVERVIEW_PATH = PROJECT_DIR / "a-list.html"
DETAILS_DIR = PROJECT_DIR / "a-list"
DOMAIN = "https://axylusion.com"

NAV_LINKS = [
    ("Gallery", "gallery.html"),
    ("Videos", "videos.html"),
    ("Music", "music.html"),
    ("Blog", "blog.html"),
    ("News", "news.html"),
    ("Tools", "tools.html"),
    ("A-List", "a-list.html"),
    ("About", "about.html"),
]
SOCIAL_LINKS = [
    (
        "X / Twitter",
        "https://x.com/Axylusion",
        '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>',
    ),
    (
        "Instagram",
        "https://www.instagram.com/axylusion",
        '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>',
    ),
    (
        "YouTube",
        "https://www.youtube.com/@AxyLusion",
        '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>',
    ),
    (
        "TikTok",
        "https://www.tiktok.com/@axylusion",
        '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/></svg>',
    ),
    (
        "Midjourney",
        "https://www.midjourney.com/@axylusion",
        '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M3.653 2.026C6.073 3.06 8.69 4.941 10.8 7.258c2.46 2.7 4.109 5.828 4.637 9.149a.31.31 0 01-.421.335c-2.348-.945-4.54-1.258-6.59-1.02-1.739.2-3.337.792-4.816 1.703-.294.182-.62-.182-.405-.454 1.856-2.355 2.581-4.99 2.343-7.794-.195-2.292-1.031-4.61-2.284-6.709a.31.31 0 01.388-.442zm6.387 2.424c1.778.543 3.892 2.102 5.782 4.243 1.984 2.248 3.552 4.934 4.347 7.582a.31.31 0 01-.401.38l-.022-.01-.386-.154a10.6 10.6 0 00-.291-.112l-.016-.006c-.68-.247-1.199-.291-1.944-.101a.31.31 0 01-.375-.218C15.378 11.123 13.073 7.276 9.775 5c-.291-.201-.072-.653.266-.55z"/></svg>',
    ),
    (
        "Suno",
        "https://suno.com/@axylusion",
        '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm3.5 14.5c0 .83-.67 1.5-1.5 1.5h-4c-.83 0-1.5-.67-1.5-1.5v-1c0-.83.67-1.5 1.5-1.5H14v-2h-4v1H8v-1c0-.83.67-1.5 1.5-1.5h4c.83 0 1.5.67 1.5 1.5v1c0 .83-.67 1.5-1.5 1.5H10v2h4v-1h1.5v1z"/></svg>',
    ),
]
CATEGORY_ICONS = {
    "image_generation": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/></svg>',
    "image_editing": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>',
    "video_generation": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2"/></svg>',
    "music_generation": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>',
    "voice_tts": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 1v11"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><path d="M5 23h14"/></svg>',
    "3d_generation": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="m12 2 8 4.5v11L12 22 4 17.5v-11L12 2Z"/><path d="M12 22V11"/><path d="m20 6.5-8 4.5-8-4.5"/></svg>',
    "upscaling": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 10V3h7"/><path d="m21 3-8 8"/><path d="M10 14v7H3"/><path d="m3 21 8-8"/></svg>',
}
NAV_LABELS = {
    "image_generation": "Image Gen",
    "image_editing": "Editing",
    "video_generation": "Video",
    "music_generation": "Music",
    "voice_tts": "Voice",
    "3d_generation": "3D",
    "upscaling": "Upscaling",
}
SOURCE_LABELS = {
    "Artificial Analysis": "AA",
    "LM Arena": "LM Arena",
    "Expert Review": "Expert",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT_PATH)
    parser.add_argument("--check", action="store_true", help="Exit non-zero if rendered A-List pages are out of date")
    return parser.parse_args()


def format_date(value: str) -> str:
    if not value:
        return ""
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    return f"{parsed.day} {parsed.strftime('%B %Y')}"


def detail_filename(slug: str) -> str:
    return f"{slug.replace('_', '-')}.html"


def canonical_url(path: str) -> str:
    return f"{DOMAIN}/{path}"


def link_path(base_path: str, href: str) -> str:
    return f"{base_path}{href}"


def render_social_links() -> str:
    items = []
    for label, url, svg in SOCIAL_LINKS:
        items.append(
            f'<a href="{escape(url)}" target="_blank" rel="noopener noreferrer" title="{escape(label)}" aria-label="{escape(label)}">{svg}</a>'
        )
    return "\n                ".join(items)


def render_header(base_path: str, active_href: str) -> str:
    nav_links = []
    for label, href in NAV_LINKS:
        classes = "nav-link active" if href == active_href else "nav-link"
        nav_links.append(f'<a href="{link_path(base_path, href)}" class="{classes}">{escape(label)}</a>')
    return f"""<header id="header" class="sticky">
        <div class="header-content">
            <a href="{link_path(base_path, 'index.html')}" class="logo"><span class="logo-text">Axy Lusion</span></a>
            <nav class="main-nav">
                {' '.join(nav_links)}
            </nav>
            <div class="header-social">
                {render_social_links()}
            </div>
        </div>
    </header>"""


def render_footer(base_path: str) -> str:
    return f"""<footer>
        <div class="footer-content">
            <div class="footer-brand">
                <span class="footer-logo">Axy Lusion</span>
                <p class="footer-tagline">AI Art, Video &amp; Music</p>
            </div>
            <nav class="social-links">
                {render_social_links()}
            </nav>
            <p class="footer-copyright">&copy; 2026 <a href="https://koltregaskes.com" target="_blank" rel="noopener noreferrer">Kol Tregaskes</a></p>
        </div>
    </footer>
    <script src="{link_path(base_path, 'cross-site-nav.js')}" defer></script>"""


def score_bar(score: float, small: bool = False) -> str:
    width = max(0.0, min(100.0, score))
    small_class = " small" if small else ""
    return (
        f'<div class="alist-score-bar{small_class}">'
        f'<div class="alist-score-fill" style="width: {width:.2f}%"></div>'
        f'<span class="alist-score-value">{score:.2f}</span>'
        "</div>"
    )


def source_badges(model: dict[str, Any]) -> str:
    badges = []
    for source in model.get("sources", []):
        label = SOURCE_LABELS.get(source["source_name"], source["source_name"])
        raw_score = source.get("raw_score")
        if raw_score is None:
            continue
        if source.get("score_type") == "elo":
            score_text = f"{raw_score:.0f}"
        else:
            score_text = f"{raw_score:.0f}/100"
        badges.append(f'<span class="alist-arena-score">{escape(label)}: {escape(score_text)}</span>')
    return "".join(badges)


def strengths_list(model: dict[str, Any], limit: int) -> str:
    strengths = model.get("strengths", [])[:limit]
    return "".join(f'<span class="alist-strength{" small" if limit == 2 else ""}">{escape(item)}</span>' for item in strengths)


def page_shell(*, title: str, description: str, canonical: str, stylesheet_path: str, favicon_path: str, manifest_path: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)}</title>
    <meta name="description" content="{escape(description)}">
    <meta property="og:title" content="{escape(title)}">
    <meta property="og:description" content="{escape(description)}">
    <meta property="og:type" content="website">
    <link rel="canonical" href="{escape(canonical)}">
    <meta name="theme-color" content="#0a0a0a">
    <meta name="color-scheme" content="dark">
    <meta name="referrer" content="strict-origin-when-cross-origin">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="{escape(stylesheet_path)}">
    <link rel="manifest" href="{escape(manifest_path)}">
    <link rel="icon" href="{escape(favicon_path)}" type="image/svg+xml">
</head>
<body>
{body}
</body>
</html>
"""


def render_overview(snapshot: dict[str, Any]) -> str:
    categories = snapshot["categories"]
    updated_text = format_date(snapshot.get("generated_at", "")) or format_date(categories[0].get("updated_at", ""))
    nav = "\n        ".join(
        f'<a href="#{escape(category["slug"].replace("_", "-"))}" class="alist-nav-link">{escape(NAV_LABELS.get(category["slug"], category["title"]))}</a>'
        for category in categories
    )
    sections: list[str] = []
    for category in categories:
        models = category["models"]
        if not models:
            continue
        leader = models[0]
        runners = models[1:5]
        runner_html = []
        for model in runners:
            runner_html.append(
                f"""<div class="alist-runner">
                    <span class="alist-runner-rank">#{model['meta_rank']}</span>
                    <div class="alist-runner-info">
                        <h4><a href="{escape(model['model_url'] or '#')}" target="_blank" rel="noopener noreferrer">{escape(model['model_name'])}</a></h4>
                        <span class="alist-maker">{escape(model['model_maker'])}</span>
                    </div>
                    <div class="alist-runner-score">
                        {score_bar(float(model['meta_score']), small=True)}
                    </div>
                    <div class="alist-runner-strengths">
                        {strengths_list(model, 2)}
                    </div>
                </div>"""
            )

        detail_href = f"a-list/{detail_filename(category['slug'])}"
        status_line = ""
        if leader.get("status_note"):
            status_line = f'<p class="alist-status-note">{escape(leader["status_note"])}</p>'
        sections.append(
            f"""<section class="alist-category" id="{escape(category['slug'].replace('_', '-'))}">
            <div class="alist-category-header">
                <div class="alist-category-icon">{CATEGORY_ICONS.get(category['slug'], '')}</div>
                <div>
                    <h2>{escape(category['title'])}</h2>
                    <p>{escape(category.get('note', ''))}</p>
                </div>
                <a href="{escape(detail_href)}" class="alist-detail-link" title="Full breakdown">View detail &rarr;</a>
            </div>

            <div class="alist-leader">
                <div class="alist-leader-badge">#{leader['meta_rank']}</div>
                <div class="alist-leader-info">
                    <h3><a href="{escape(leader['model_url'] or '#')}" target="_blank" rel="noopener noreferrer">{escape(leader['model_name'])}</a></h3>
                    <span class="alist-maker">{escape(leader['model_maker'])}</span>
                    {score_bar(float(leader['meta_score']))}
                    <div class="alist-strengths">{strengths_list(leader, 3)}</div>
                    <p class="alist-category-note"><strong>{escape(leader['coverage_label'])}</strong> &middot; Coverage {leader['coverage_percent']:.0f}%</p>
                    <p class="alist-considerations">{escape(leader.get('considerations') or '')}</p>
                    {status_line}
                    <div class="alist-arena-scores">{source_badges(leader)}</div>
                </div>
            </div>

            <div class="alist-runners">
                {''.join(runner_html)}
            </div>
        </section>"""
        )

    body = f"""
    {render_header('', 'a-list.html')}

    <section class="page-header">
        <div class="page-header-content">
            <h1 class="page-title stagger-load delay-1">The A-List</h1>
            <p class="page-subtitle stagger-load delay-2">Benchmark-led rankings for creative AI, with studio judgement where public coverage is thin.</p>
            <p class="alist-updated stagger-load delay-3">Last updated: {escape(updated_text)}</p>
        </div>
    </section>

    <section class="alist-methodology">
        <div class="alist-methodology-content">
            <h3>How we rank</h3>
            <p>{escape(snapshot.get('methodology_note', ''))}</p>
            <div class="alist-sources">
                <span class="alist-source-badge"><a href="https://artificialanalysis.ai" target="_blank" rel="noopener noreferrer">Artificial Analysis</a></span>
                <span class="alist-source-badge"><a href="https://lmarena.ai/?arena=image" target="_blank" rel="noopener noreferrer">LM Arena</a></span>
                <span class="alist-source-badge">Expert Review</span>
            </div>
            <p class="alist-method-note">The shared benchmark feed is maintained in the AI Resource Hub. Axy Lusion only reshapes that shared data for this site&apos;s delivery and editorial emphasis.</p>
            <p class="alist-method-note">Expert Review is the studio/editorial score: hands-on testing, creator reputation, creative fit, and how usable a tool actually feels in real work.</p>
        </div>
    </section>

    <nav class="alist-category-nav">
        {nav}
    </nav>

    <main class="alist-main">
        {''.join(sections)}
    </main>

    {render_footer('')}
    """
    return page_shell(
        title="The A-List | Axy Lusion",
        description="Top AI creative tools ranked with benchmark data and studio judgement where public coverage is sparse.",
        canonical=canonical_url("a-list.html"),
        stylesheet_path="styles.css",
        favicon_path="favicon.svg",
        manifest_path="site.webmanifest",
        body=body,
    )


def source_columns(category: dict[str, Any]) -> list[str]:
    columns: list[str] = []
    for source_name in ("Artificial Analysis", "LM Arena", "Expert Review"):
        if any(source["source_name"] == source_name for model in category["models"] for source in model.get("sources", [])):
            columns.append(source_name)
    return columns


def source_cell(model: dict[str, Any], source_name: str) -> str:
    for source in model.get("sources", []):
        if source["source_name"] == source_name:
            raw_score = source.get("raw_score")
            if raw_score is None:
                return "&mdash;"
            if source.get("score_type") == "elo":
                return f"{raw_score:.0f}"
            return f"{raw_score:.0f}"
    return "&mdash;"


def render_detail_page(category: dict[str, Any]) -> str:
    base_path = "../"
    source_cols = source_columns(category)
    header_cells = "".join(f"<th>{escape(SOURCE_LABELS.get(source, source))}</th>" for source in source_cols)
    body_rows = []
    for model in category["models"]:
        source_cells = "".join(f"<td>{source_cell(model, source)}</td>" for source in source_cols)
        body_rows.append(
            f"""<tr{' class="alist-table-leader"' if model['meta_rank'] == 1 else ''}>
                <td>{model['meta_rank']}</td>
                <td><a href="{escape(model['model_url'] or '#')}" target="_blank" rel="noopener noreferrer">{escape(model['model_name'])}</a> <span class="alist-maker">{escape(model['model_maker'])}</span></td>
                <td><strong>{float(model['meta_score']):.2f}</strong></td>
                <td>{model['coverage_percent']:.0f}%</td>
                {source_cells}
            </tr>"""
        )

    model_cards = []
    for model in category["models"]:
        status_line = f'<p class="alist-status-note">{escape(model["status_note"])}</p>' if model.get("status_note") else ""
        model_cards.append(
            f"""<div class="alist-model-card">
                <div class="alist-model-card-header">
                    <span class="alist-leader-badge">#{model['meta_rank']}</span>
                    <div>
                        <h3><a href="{escape(model['model_url'] or '#')}" target="_blank" rel="noopener noreferrer">{escape(model['model_name'])}</a></h3>
                        <span class="alist-maker">{escape(model['model_maker'])}</span>
                    </div>
                    {score_bar(float(model['meta_score']))}
                </div>
                <div class="alist-model-card-body">
                    <div class="alist-model-detail-grid">
                        <div>
                            <h4>Strengths</h4>
                            <ul>
                                {''.join(f'<li>{escape(item)}</li>' for item in model.get('strengths', [])[:4])}
                            </ul>
                        </div>
                        <div>
                            <h4>Considerations</h4>
                            <ul>
                                <li>{escape(model.get('considerations') or 'No major caveat recorded yet.')}</li>
                                <li>Coverage: {model['coverage_percent']:.0f}% ({escape(model['coverage_label'])})</li>
                                <li>{escape(model.get('pricing_note') or 'Pricing varies by plan and surface.')}</li>
                            </ul>
                        </div>
                    </div>
                    {status_line}
                    <div class="alist-model-sources">
                        <h4>Source scores</h4>
                        <div class="alist-arena-scores">{source_badges(model)}</div>
                    </div>
                </div>
            </div>"""
        )

    weight_cards = []
    for source_name, weight in category.get("weights", {}).items():
        description = {
            "Artificial Analysis": "Public blind preference or arena-style benchmark data where available.",
            "LM Arena": "Crowd preference data, used where we have clean category-relevant coverage.",
            "Expert Review": "Studio/editorial judgement from hands-on use, creator reputation, and practical fit.",
        }.get(source_name, "Weighted input.")
        weight_cards.append(
            f"""<div class="alist-source-card">
                <h4>{escape(source_name)}</h4>
                <span class="alist-source-weight">Weight: {weight}%</span>
                <p>{escape(description)}</p>
            </div>"""
        )

    body = f"""
    {render_header(base_path, 'a-list.html')}

    <section class="page-header">
        <div class="page-header-content">
            <p class="alist-breadcrumb"><a href="../a-list.html">&larr; The A-List</a></p>
            <h1 class="page-title stagger-load delay-1">{escape(category['title'])}</h1>
            <p class="page-subtitle stagger-load delay-2">{escape(category.get('note', ''))}</p>
        </div>
    </section>

    <main class="alist-detail-main">
        <section class="alist-detail-section">
            <h2>Rankings at a glance</h2>
            <div class="alist-comparison-table">
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Model</th>
                            <th>Score</th>
                            <th>Coverage</th>
                            {header_cells}
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(body_rows)}
                    </tbody>
                </table>
            </div>
        </section>

        <section class="alist-detail-section">
            <h2>Model details</h2>
            {''.join(model_cards)}
        </section>

        <section class="alist-detail-section">
            <h2>How we judge this category</h2>
            <p class="alist-method-note">{escape(category.get('note', ''))}</p>
            <div class="alist-source-cards">
                {''.join(weight_cards)}
            </div>
        </section>

        <div class="alist-back-link"><a href="../a-list.html">&larr; Back to The A-List</a></div>
    </main>

    {render_footer(base_path)}
    """
    file_name = detail_filename(category["slug"])
    return page_shell(
        title=f"{category['title']} | The A-List | Axy Lusion",
        description=f"Benchmark-led breakdown of {category['title'].lower()} tools on the Axy Lusion A-List.",
        canonical=canonical_url(f"a-list/{file_name}"),
        stylesheet_path="../styles.css",
        favicon_path="../favicon.svg",
        manifest_path="../site.webmanifest",
        body=body,
    )


def build_outputs(snapshot: dict[str, Any]) -> dict[Path, str]:
    outputs: dict[Path, str] = {OVERVIEW_PATH: render_overview(snapshot)}
    for category in snapshot.get("categories", []):
        outputs[DETAILS_DIR / detail_filename(category["slug"])] = render_detail_page(category)
    return outputs


def main() -> int:
    args = parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    outputs = build_outputs(snapshot)

    if args.check:
        outdated_paths: list[Path] = []
        for output_path, rendered in outputs.items():
            if not output_path.exists() or output_path.read_text(encoding="utf-8") != rendered:
                outdated_paths.append(output_path)

        if outdated_paths:
            print("Rendered A-List pages are out of date:")
            for path in outdated_paths:
                print(f"- {path}")
            return 1

        print(f"Rendered A-List pages are current: {len(outputs)} files checked")
        return 0

    DETAILS_DIR.mkdir(parents=True, exist_ok=True)
    for output_path, rendered in outputs.items():
        output_path.write_text(rendered, encoding="utf-8")

    print(f"Rendered A-List overview: {OVERVIEW_PATH}")
    print(f"Rendered A-List detail pages: {len(snapshot.get('categories', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
