#!/usr/bin/env python3
"""Render the static Axy Lusion cinematic pages.

The public site is still static HTML. This script is a local authoring helper:
it reads the existing JSON/markdown payloads, adds the cinematic frame metadata
needed by the design, then writes the in-scope public pages.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
DOMAIN = "https://axylusion.com"
SCHEMA_NONCE = "axylusion-cinematic-schema"
TONES = [
    ["#1a3540", "#060606", "#c4851a"],
    ["#3a1f10", "#060606", "#d4a03a"],
    ["#2a0d2e", "#060606", "#c4851a"],
    ["#3d2c0a", "#060606", "#f5e6c8"],
    ["#1f1024", "#060606", "#d4a03a"],
    ["#0d2424", "#060606", "#c4851a"],
    ["#2a1810", "#060606", "#8a5d12"],
    ["#3a0d12", "#060606", "#d4a03a"],
    ["#0d1a2a", "#060606", "#c4851a"],
    ["#1c2a1a", "#060606", "#d4a03a"],
]
TOPIC_ALIASES = {
    "image": "Image",
    "image_gen": "Image",
    "video": "Video",
    "video_gen": "Video",
    "audio": "Audio",
    "music_gen": "Audio",
    "voice_synthesis": "Audio",
    "3d": "3D",
    "3d_gen": "3D",
    "creative": "Tools",
    "creative_tool": "Tools",
    "creative_workflow": "Tools",
    "art_ai": "Tools",
    "design": "Tools",
    "product": "Tools",
    "product_launch": "Tools",
    "api_update": "Tools",
    "model_release": "Tools",
    "benchmark": "Benchmarks",
    "evaluation": "Benchmarks",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def clean_page(html: str) -> str:
    return re.sub(r"[ \t]+(?=\r?\n)", "", html).rstrip() + "\n"


def write_page(path: Path, html: str) -> None:
    path.write_text(clean_page(html), encoding="utf-8")


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "item"


def tone_for(item_id: str) -> list[str]:
    digest = hashlib.sha1(item_id.encode("utf-8")).hexdigest()
    return TONES[int(digest[:2], 16) % len(TONES)]


def frame_ref(index: int) -> str:
    return f"F{index + 1:04d}"


def parse_date(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)


def fmt_date(value: str) -> str:
    parsed = parse_date(value)
    return f"{parsed.day} {parsed.strftime('%b')} {parsed.year}"


def fmt_date_long(value: str) -> str:
    parsed = parse_date(value)
    return f"{parsed.day} {parsed.strftime('%B')} {parsed.year}"


def frame_style(item: dict) -> str:
    tones = item.get("tones") or TONES[0]
    a, b, accent = [str(value) for value in tones[:3]]
    return (
        "background:"
        f"radial-gradient(ellipse 60% 80% at 30% 110%, {accent}55 0%, transparent 55%),"
        f"radial-gradient(ellipse 90% 60% at 80% 0%, {a}cc 0%, transparent 60%),"
        f"linear-gradient(160deg, {a} 0%, {b} 100%)"
    )


def prompt_for(item: dict) -> str:
    return str(item.get("prompt") or item.get("name") or "Prompt not logged").strip()


def page_url(path: str = "") -> str:
    if not path or path == "index.html":
        return f"{DOMAIN}/"
    return f"{DOMAIN}/{path}".rstrip("/") + ("" if path else "/")


def local_link(current: str, target: str) -> str:
    if current.startswith("a-list/") and not target.startswith(("http", "#", "mailto:")):
        return f"../{target}"
    return target


def normalize_item(item: dict, index: int, prompt_lookup: dict[str, str] | None = None) -> dict:
    item_id = str(item.get("id") or "").strip()
    if not item_id:
        item_id = slugify(str(item.get("name") or f"frame-{index + 1}"))
        item["id"] = item_id
    item.setdefault("ref", frame_ref(index))
    item.setdefault("tones", tone_for(item_id))
    if "prompt" not in item:
        lookup = prompt_lookup or {}
        item["prompt"] = lookup.get(item_id, str(item.get("name") or "Prompt not logged"))
    item.setdefault("type", "image")
    return item


def load_and_migrate_gallery() -> tuple[list[dict], list[dict]]:
    gallery_path = ROOT / "data" / "gallery.json"
    home_path = ROOT / "data" / "homepage-gallery.json"
    gallery_payload = read_json(gallery_path)
    gallery_items = gallery_payload.get("items", [])
    for index, item in enumerate(gallery_items):
        normalize_item(item, index)

    prompt_lookup = {str(item.get("id")): prompt_for(item) for item in gallery_items}
    ref_lookup = {str(item.get("id")): item.get("ref") for item in gallery_items}
    tone_lookup = {str(item.get("id")): item.get("tones") for item in gallery_items}

    home_payload = read_json(home_path)
    home_items = home_payload.get("items", [])
    for index, item in enumerate(home_items):
        normalize_item(item, index, prompt_lookup)
        item_id = str(item.get("id"))
        if item_id in ref_lookup:
            item["ref"] = ref_lookup[item_id]
        if item_id in tone_lookup:
            item["tones"] = tone_lookup[item_id]

    write_json(gallery_path, gallery_payload)
    write_json(home_path, home_payload)
    return gallery_items, home_items


def social_links(large: bool = False) -> str:
    socials = [
        ("X", "https://x.com/Axylusion", "X / @Axylusion"),
        ("IG", "https://www.instagram.com/axylusion", "Instagram / @axylusion"),
        ("YT", "https://www.youtube.com/@AxyLusion", "YouTube / @AxyLusion"),
        ("TT", "https://www.tiktok.com/@axylusion", "TikTok / @axylusion"),
        ("MJ", "https://www.midjourney.com/@axylusion", "Midjourney / @axylusion"),
        ("SU", "https://suno.com/@axylusion", "Suno / @axylusion"),
    ]
    cls = "cn-social cn-social--lg" if large else "cn-social"
    return (
        f'<div class="{cls}">'
        + "".join(
            f'<a href="{url}" target="_blank" rel="noopener noreferrer" aria-label="{escape(label)}">{escape(code)}</a>'
            for code, url, label in socials
        )
        + "</div>"
    )


def header(active: str, current_path: str = "") -> str:
    nav = [
        ("Gallery", "gallery.html"),
        ("Videos", "videos.html"),
        ("Music", "music.html"),
        ("Blog", "blog.html"),
        ("News", "news.html"),
        ("Tools", "tools.html"),
        ("A-List", "a-list.html"),
        ("About", "about.html"),
    ]
    links = []
    for label, href in nav:
        cls = ' class="is-active"' if label == active else ""
        links.append(f'<a{cls} href="{escape(local_link(current_path, href))}">{escape(label)}</a>')
    return f"""
    <header class="cn-header">
      <a class="cn-logo" href="{escape(local_link(current_path, 'index.html'))}">Axy Lusion</a>
      <nav class="cn-nav" aria-label="Primary navigation">{''.join(links)}</nav>
      {social_links()}
    </header>"""


def footer(current_path: str = "") -> str:
    prefix = "../" if current_path.startswith("a-list/") else ""
    return f"""
    <footer class="cn-footer">
      <div class="cn-footer__brand">
        <span class="cn-logo">Axy Lusion</span>
        <p>AI Art / Video / Music</p>
      </div>
      {social_links(large=True)}
      <p class="cn-footer__copy">&copy; 2026 <a href="https://koltregaskes.com" target="_blank" rel="noopener noreferrer">Kol Tregaskes</a></p>
    </footer>
    <script src="{prefix}scripts/cinematic.js" defer></script>
    <script src="{prefix}cross-site-nav.js" defer></script>"""


def untitled_note(compact: bool = False) -> str:
    cls = "cn-note cn-note--compact" if compact else "cn-note"
    return f"""
      <div class="{cls}">
        <span class="cn-note__dot" aria-hidden="true"></span>
        <p><strong>Untitled works.</strong> Frames are identified by date and queue reference rather than a title. Where the original prompt was logged, it is shown as caption.</p>
      </div>"""


def frame(item: dict, index: int, ratio: str = "3/4", mode: str = "plate", caption: bool = False, extra: str = "") -> str:
    ref = escape(str(item.get("ref") or frame_ref(index)))
    date = escape(fmt_date(str(item.get("created") or "")))
    prompt = escape(prompt_for(item))
    src = escape(str(item.get("src") or ""))
    img = f'<img class="cn-frame__img" src="{src}" alt="Frame {ref}, {date}" loading="lazy" decoding="async">' if src else ""
    cap = (
        f'<figcaption class="cn-frame__cap"><span class="cn-frame__cap-label">Prompt</span><span class="cn-frame__cap-text">{prompt}</span></figcaption>'
        if caption
        else f'<figcaption class="cn-frame__cap cn-frame__cap--optional" hidden><span class="cn-frame__cap-label">Prompt</span><span class="cn-frame__cap-text">{prompt}</span></figcaption>'
    )
    return f"""
      <figure class="cn-frame cn-frame--{mode} {extra}" style="aspect-ratio:{escape(ratio)}">
        <div class="cn-frame__bg" style="{escape(frame_style(item))}"></div>
        {img}
        <div class="cn-frame__grain" aria-hidden="true"></div>
        <div class="cn-frame__vignette" aria-hidden="true"></div>
        <div class="cn-frame__corner"><span>{ref}</span><span>/</span><span>{date}</span></div>
        {cap}
      </figure>"""


def base_schema() -> list[dict]:
    return [
        {
            "@type": "Organization",
            "@id": f"{DOMAIN}/#organization",
            "name": "Axy Lusion",
            "alternateName": "Axylusion",
            "url": DOMAIN,
            "logo": f"{DOMAIN}/favicon.svg",
            "description": "AI art portfolio and creative tool rankings by Kol Tregaskes.",
            "founder": {"@id": "https://koltregaskes.com/#person-kol"},
            "sameAs": ["https://x.com/Axylusion", "https://www.instagram.com/axylusion"],
        },
        {
            "@type": "WebSite",
            "@id": f"{DOMAIN}/#website",
            "name": "Axy Lusion",
            "url": DOMAIN,
            "publisher": {"@id": f"{DOMAIN}/#organization"},
        },
    ]


def page_shell(path: str, title: str, description: str, active: str, body: str, schema: list[dict] | None = None) -> str:
    prefix = "../" if path.startswith("a-list/") else ""
    graph = {"@context": "https://schema.org", "@graph": base_schema() + (schema or [])}
    canonical = page_url(path)
    return f"""<!doctype html>
<html lang="en-GB">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description)}">
  <meta name="theme-color" content="#060606">
  <meta name="color-scheme" content="dark">
  <meta name="referrer" content="strict-origin-when-cross-origin">
  <meta http-equiv="Content-Security-Policy" content="default-src 'self'; img-src 'self' data: https:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; script-src 'self' 'nonce-{SCHEMA_NONCE}'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; upgrade-insecure-requests">
  <meta property="og:title" content="{escape(title)}">
  <meta property="og:description" content="{escape(description)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{escape(canonical)}">
  <link rel="canonical" href="{escape(canonical)}">
  <link rel="manifest" href="{prefix}site.webmanifest">
  <link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{prefix}cinematic.css">
  <script type="application/ld+json" nonce="{SCHEMA_NONCE}">{json.dumps(graph, ensure_ascii=True)}</script>
</head>
<body>
  <a class="skip-link" href="#main-content">Skip to content</a>
  <div class="cn-page">
    {header(active, path)}
    <main id="main-content">
{body}
    </main>
    {footer(path)}
  </div>
</body>
</html>
"""


def render_home(gallery_items: list[dict], home_items: list[dict]) -> str:
    items = home_items[:14] or gallery_items[:14]
    hero = items[0]
    reel = items[:8]
    strip = "".join(
        f'<button class="cn-strip__cell{" is-on" if i == 0 else ""}" style="{escape(frame_style(item))}" data-hero-index="{i}" aria-label="Show {escape(str(item.get("ref")))}"><span class="cn-strip__ref">{escape(str(item.get("ref")))}</span></button>'
        for i, item in enumerate(items[:8])
    )
    rows = []
    for index, item in enumerate(reel):
        rows.append(
            f"""
            <article class="cn-reel__row">
              <div class="cn-reel__num">{index + 1:02d}</div>
              <div class="cn-reel__frame">{frame(item, index, ratio='16/9', mode='full')}</div>
              <div class="cn-reel__meta">
                <span class="cn-kicker cn-kicker--sm">{escape(str(item.get('ref')))} / {escape(fmt_date(str(item.get('created'))))}</span>
                <p class="cn-reel__prompt">&quot;{escape(prompt_for(item))}&quot;</p>
                <p class="cn-reel__status">Durable image host pending / gradient frame is intentional fallback</p>
              </div>
            </article>"""
        )
    hero_payload = json.dumps(
        [
            {
                "ref": item.get("ref"),
                "date": fmt_date_long(str(item.get("created") or "")),
                "prompt": prompt_for(item),
                "style": frame_style(item),
            }
            for item in items[:8]
        ],
        ensure_ascii=True,
    )
    body = f"""
      <section class="cn-hero">
        <div class="cn-hero__bg" data-hero-bg style="{escape(frame_style(hero))}">
          <div class="cn-frame__grain" aria-hidden="true"></div>
          <div class="cn-frame__vignette" aria-hidden="true"></div>
        </div>
        <div class="cn-hero__inner">
          <div class="cn-hero__meta"><span class="cn-tick" aria-hidden="true"></span><span>Archive / <span data-hero-ref>{escape(str(hero.get('ref')))}</span> of {len(gallery_items):04d}</span><span class="cn-rule"></span><span data-hero-date>{escape(fmt_date_long(str(hero.get('created'))))}</span></div>
          <h1 class="cn-display">Axy Lusion</h1>
          <p class="cn-display-sub">AI Art / Video / Music</p>
          <p class="cn-pull" data-hero-prompt>&quot;{escape(prompt_for(hero))}&quot;</p>
          <div class="cn-cta-row"><a class="cn-cta cn-cta--primary" href="gallery.html">Enter the gallery</a><a class="cn-cta cn-cta--ghost" href="about.html">About the artist</a></div>
        </div>
        <div class="cn-strip" data-hero-strip data-hero-items='{escape(hero_payload)}'>{strip}</div>
      </section>
      <section class="cn-reel">
        <div class="cn-reel__intro"><span class="cn-kicker">Reel / {len(reel)} frames</span><h2 class="cn-h2">Recent image journey</h2>{untitled_note()}</div>
        {''.join(rows)}
        <div class="cn-reel__foot"><a class="cn-cta cn-cta--primary" href="gallery.html">View full gallery</a></div>
      </section>
      <section class="cn-about">
        <div class="cn-about__inner">
          <div class="cn-avatar-frame" aria-hidden="true">KT</div>
          <div class="cn-about__copy">
            <span class="cn-kicker">About the artist</span>
            <h2 class="cn-h2">Kol Tregaskes</h2>
            <p>A creative explorer at the intersection of art and artificial intelligence. Through Midjourney, Suno, video models, and careful sequencing, Axy Lusion becomes a cinematic archive of images, sound, and moving-image experiments.</p>
            <p>Every frame is a collaboration between human direction and model capability: prompts refined through iteration, then indexed here by date and frame reference.</p>
            <div class="cn-cta-row"><a class="cn-cta cn-cta--ghost" href="https://koltregaskes.com">Kol's Korner</a><a class="cn-cta cn-cta--ghost" href="https://x.com/Axylusion">Follow on X</a></div>
          </div>
        </div>
      </section>"""
    return page_shell(
        "index.html",
        "Axy Lusion | AI Art, Video and Music",
        "Cinematic AI art, video, music, and creative tool coverage by Kol Tregaskes.",
        "",
        body,
    )


def render_gallery(gallery_items: list[dict]) -> str:
    cards = []
    for index, item in enumerate(gallery_items):
        prompt = prompt_for(item)
        model = str(item.get("model") or item.get("source") or "Unknown")
        type_label = str(item.get("type") or "image").title()
        haystack = " ".join([prompt, str(item.get("id")), str(item.get("ref")), fmt_date(str(item.get("created")))]).lower()
        cards.append(
            f"""
            <article class="cn-gallery-card" id="frame-{escape(str(item.get('ref')).lower())}" data-index="{index}" data-search="{escape(haystack)}" data-type="{escape(type_label)}" data-model="{escape(model)}" data-date="{escape(str(item.get('created') or ''))}">
              {frame(item, index, caption=False)}
            </article>"""
        )
    models = sorted({str(item.get("model") or item.get("source") or "Unknown") for item in gallery_items})
    model_options = "".join(f'<option value="{escape(model)}">{escape(model)}</option>' for model in models)
    artwork = [
        {
            "@type": "VisualArtwork",
            "@id": f"{DOMAIN}/gallery.html#frame-{str(item.get('ref')).lower()}",
            "name": f"{item.get('ref')} / {fmt_date(str(item.get('created') or ''))}",
            "identifier": item.get("ref"),
            "description": prompt_for(item),
            "creator": {"@id": "https://koltregaskes.com/#person-kol"},
            "artMedium": f"AI image generation ({item.get('model') or item.get('source') or 'Midjourney'})",
            "artform": "Digital art",
            "dateCreated": item.get("created"),
            "url": f"{DOMAIN}/gallery.html#frame-{str(item.get('ref')).lower()}",
            "isPartOf": {"@id": f"{DOMAIN}/gallery.html#gallery"},
        }
        for item in gallery_items
    ]
    schema = [
        {
            "@type": "ImageGallery",
            "@id": f"{DOMAIN}/gallery.html#gallery",
            "name": "Axy Lusion Gallery",
            "description": "Untitled AI-generated frames by Kol Tregaskes, indexed by frame reference and date.",
            "image": artwork,
        }
    ]
    body = f"""
      <section class="cn-pagehead">
        <div class="cn-pagehead__inner"><span class="cn-kicker">Archive / {len(gallery_items):04d} frames</span><h1 class="cn-h1">Gallery</h1><p class="cn-lede">The complete image archive. Search by prompt fragment, frame ref, ID, date, type, or model.</p>{untitled_note()}</div>
      </section>
      <section class="cn-controls" aria-label="Gallery controls">
        <label class="cn-search" for="gallery-search"><span class="cn-search__icon" aria-hidden="true">Search</span><input id="gallery-search" type="search" placeholder="Search prompts, frame refs, IDs or dates" data-gallery-search><span class="cn-search__hint">/</span></label>
        <div class="cn-filters" data-gallery-controls>
          <button type="button" class="is-on" data-gallery-type="All" aria-pressed="true">All types</button><button type="button" data-gallery-type="Image" aria-pressed="false">Image</button><button type="button" data-gallery-type="Video" aria-pressed="false">Video</button><button type="button" data-gallery-type="Music" aria-pressed="false">Music</button>
          <span class="cn-rule"></span>
          <button type="button" class="is-on" data-gallery-sort="newest" aria-pressed="true">Newest</button><button type="button" data-gallery-sort="oldest" aria-pressed="false">Oldest</button><button type="button" data-gallery-sort="random" aria-pressed="false">Random</button>
          <span class="cn-rule"></span>
          <label class="sr-only" for="gallery-model">Model</label><select id="gallery-model" data-gallery-model><option value="All">All models</option>{model_options}</select>
          <button type="button" data-caption-toggle aria-pressed="false">Show prompt captions</button>
          <button type="button" data-gallery-reset>Reset</button>
        </div>
      </section>
      <section class="cn-grid" data-gallery-grid aria-live="polite">{''.join(cards)}</section>
      <div class="cn-news-empty cn-hidden" data-gallery-empty><span class="cn-kicker">No matches</span><p>No frames match the current filters.</p><button class="cn-cta cn-cta--ghost cn-cta--sm" type="button" data-gallery-reset>Reset filters</button></div>
      <div class="cn-pager"><button class="cn-cta cn-cta--ghost" type="button" data-gallery-more>Load 24 more</button><span data-gallery-count>0001 - 0024 of {len(gallery_items):04d}</span></div>"""
    return page_shell("gallery.html", "Gallery | Axy Lusion", "Untitled AI-generated frames by Kol Tregaskes, indexed by frame reference and date.", "Gallery", body, schema)


def parse_digest(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")
    date_match = re.search(r"\*\*(\d{4}-\d{2}-\d{2})\*\*", text)
    date = date_match.group(1) if date_match else "1970-01-01"
    stories = []
    for match in re.finditer(r"^## \[(?P<title>[^\]]+)\]\((?P<href>[^)]+)\)\s*\n(?P<meta>[\s\S]*?)(?=\n---|\Z)", text, re.MULTILINE):
        meta = match.group("meta")
        tags_match = re.search(r"Tags:\s*([^\n]+)", meta)
        raw_tags = [tag.strip() for tag in (tags_match.group(1) if tags_match else "creative_tool").split(",")]
        topic = "Tools"
        for tag in raw_tags:
            if tag in TOPIC_ALIASES:
                topic = TOPIC_ALIASES[tag]
                break
        source_match = re.search(r"\*([^*]+)\*", meta)
        stories.append(
            {
                "title": match.group("title").strip(),
                "href": match.group("href").strip(),
                "topic": topic,
                "source": source_match.group(1).strip() if source_match else "Source",
            }
        )
    return {"date": date, "stories": stories, "slug": path.name}


def load_digests(limit: int = 32) -> list[dict]:
    manifest = read_json(ROOT / "news-digests" / "index.json")
    digests = []
    for filename in manifest.get("files", [])[:limit]:
        path = ROOT / "news-digests" / filename
        if path.exists():
            digest = parse_digest(path)
            if digest["stories"]:
                digests.append(digest)
    return digests


def render_news(gallery_items: list[dict]) -> str:
    digests = load_digests()
    latest = digests[0]
    lead = latest["stories"][0]
    digest_rows = []
    for digest in digests:
        date = parse_date(digest["date"])
        items = "".join(
            f'<li data-topic="{escape(story["topic"])}"><a href="{escape(story["href"])}" target="_blank" rel="noopener noreferrer">{escape(story["title"])}</a><span class="cn-digest__topic">{escape(story["topic"])}</span></li>'
            for story in digest["stories"]
        )
        digest_rows.append(
            f"""
            <article class="cn-digest" data-digest-date="{escape(digest['date'])}" data-digest-search="{escape(' '.join(story['title'] for story in digest['stories']).lower())}">
              <div class="cn-digest__date"><span class="cn-digest__day">{date.day}</span><span class="cn-digest__mon">{date.strftime('%b')}</span><span class="cn-digest__yr">{date.year}</span></div>
              <ul class="cn-digest__heads">{items}</ul>
              <a class="cn-cta cn-cta--ghost cn-cta--sm" href="news-digests/{escape(digest['slug'])}">Open</a>
            </article>"""
        )
    art = gallery_items[8] if len(gallery_items) > 8 else gallery_items[0]
    topics = ["All", "Image", "Video", "Audio", "3D", "Tools", "Benchmarks"]
    chips = "".join(f'<button type="button" class="cn-chip{" is-on" if topic == "All" else ""}" data-news-topic="{topic}" aria-pressed="{"true" if topic == "All" else "false"}">{topic}</button>' for topic in topics)
    body = f"""
      <section class="cn-pagehead"><div class="cn-pagehead__inner"><span class="cn-kicker">Dated digest archive / {escape(fmt_date(latest['date']))}</span><h1 class="cn-h1">News</h1><p class="cn-lede">Creative-AI headlines for image, video, audio, tools, 3D, and benchmarks. The lead story is fixed; filters apply to the digest list below.</p></div></section>
      <section class="cn-news-lead"><div class="cn-news-lead__bg" style="{escape(frame_style(art))}"><div class="cn-frame__grain"></div><div class="cn-frame__vignette"></div></div><div class="cn-news-lead__copy"><span class="cn-kicker">Lead / {escape(fmt_date_long(latest['date']))} / {escape(lead['topic'])}</span><h2 class="cn-h2">{escape(lead['title'])}</h2><p>Most recent indexed creative-AI signal from the Axy Lusion digest archive.</p><div class="cn-cta-row"><a class="cn-cta cn-cta--primary" href="{escape(lead['href'])}" target="_blank" rel="noopener noreferrer">Open source</a><a class="cn-cta cn-cta--ghost" href="news-digests/{escape(latest['slug'])}">Read digest</a></div></div></section>
      <section class="cn-news-filters" aria-label="News filters">
        <div class="cn-news-filters__row"><label class="cn-search" for="news-search"><span class="cn-search__icon" aria-hidden="true">Search</span><input id="news-search" type="search" placeholder="Search headlines" data-news-search></label><div class="cn-news-filters__range"><button type="button" data-news-range="day" aria-pressed="false">Issue day</button><button type="button" data-news-range="week" aria-pressed="false">7-day window</button><button type="button" class="is-on" data-news-range="all" aria-pressed="true">All</button></div></div>
        <div class="cn-news-filters__chips"><span class="cn-kicker cn-kicker--sm">Topic</span>{chips}<button class="cn-news-filters__clear cn-hidden" type="button" data-news-clear>Clear all</button></div>
      </section>
      <section class="cn-digests" data-news-list><div class="cn-digests__head"><span class="cn-kicker">Digest list</span><h2 class="cn-h2">By the day</h2>{untitled_note(True)}</div>{''.join(digest_rows)}<div class="cn-news-empty cn-hidden" data-news-empty><span class="cn-kicker">No matches</span><p>No stories match the current filters.</p><button class="cn-cta cn-cta--ghost cn-cta--sm" type="button" data-news-empty-reset>Clear filters</button></div></section>"""
    return page_shell("news.html", "News | Axy Lusion", "Dated creative-AI digest archive for image, video, audio, tools, 3D, and benchmarks.", "News", body)


def render_blog(gallery_items: list[dict]) -> str:
    cover = gallery_items[3]
    body = f"""
      <section class="cn-pagehead"><div class="cn-pagehead__inner"><span class="cn-kicker">Journal</span><h1 class="cn-h1">Blog</h1><p class="cn-lede">Notes behind the images, tools, videos, and decisions. Slower posts for process and project context.</p>{untitled_note(True)}</div></section>
      <section class="cn-blog-hero"><div class="cn-blog-hero__cover">{frame(cover, 3, ratio='3/2', mode='full')}</div><div class="cn-blog-hero__copy"><span class="cn-kicker">Featured / 2 April 2026</span><h2 class="cn-h2">Welcome to Axy Lusion</h2><p>A short introduction to the site, what lives on it, and why the project exists.</p><div class="cn-blog-hero__meta"><span>5 min read</span><span class="cn-rule"></span><span>Welcome / Intro</span></div><a class="cn-cta cn-cta--primary" href="blog-welcome.html">Read the post</a></div></section>
      <section class="cn-blog-list"><div class="cn-blog-list__head"><span class="cn-kicker">All posts / 1</span><h2 class="cn-h2">Archive</h2></div><a class="cn-blog-row" href="blog-welcome.html"><span class="cn-blog-row__date">02 / 04 / 26</span><span class="cn-blog-row__body"><strong>Welcome to Axy Lusion</strong><span>Hello, this is me, this is what lives on the site, and this is what you can expect from the project going forward.</span><span class="cn-tags"><span>Welcome</span><span>Intro</span></span></span><span class="cn-blog-row__arrow">-&gt;</span></a><div class="cn-blog-empty"><span class="cn-kicker">Coming soon</span><p>Process notes on the comic series, the upcoming Suno EP, and a deeper writeup on how the news pipeline is built.</p></div></section>"""
    return page_shell("blog.html", "Blog | Axy Lusion", "Process notes and updates from the Axy Lusion archive.", "Blog", body, [{"@type": "Blog", "@id": f"{DOMAIN}/blog.html#blog", "name": "Axy Lusion Blog", "publisher": {"@id": f"{DOMAIN}/#organization"}}])


def render_about(gallery_items: list[dict]) -> str:
    portrait = gallery_items[5]
    body = f"""
      <section class="cn-pagehead cn-pagehead--lg"><div class="cn-pagehead__inner"><span class="cn-kicker">About</span><h1 class="cn-h1">Kol Tregaskes / the work behind the archive</h1><p class="cn-lede">A creative explorer at the intersection of art and artificial intelligence. Axy Lusion is the public creative identity for image, music, and moving-image work.</p></div></section>
      <section class="cn-about-grid"><div class="cn-about-grid__portrait">{frame(portrait, 5, ratio='3/4', mode='full')}<div class="cn-about-grid__name"><span class="cn-kicker cn-kicker--sm">The artist</span><h3>Kol Tregaskes</h3><p>Cornwall, UK</p></div></div><div class="cn-about-grid__body"><p class="cn-lead-para">Every frame is a collaboration between human direction and AI capability: prompts refined through iteration, archived here by date, with the original prompt preserved as caption where available.</p><h2 class="cn-h3">Practice</h2><p>Cinematic portraits, dark fantasy scenes, cyberpunk visions, music sketches, and moving-image studies are the running threads. Tools rotate, but the archive is the constant.</p><h2 class="cn-h3">Why no titles?</h2><p>Titling a 5,000-frame Midjourney archive retroactively is the kind of task that sounds easy and quietly never gets done. Instead the archive uses what is actually reliable: a date, a queue reference, and the prompt where it was logged. Less invented, more honest, faster to build, easier to search.</p><h2 class="cn-h3">Elsewhere</h2><div class="cn-about-grid__links"><a href="https://koltregaskes.com">koltregaskes.com</a><a href="https://x.com/Axylusion">X / @Axylusion</a><a href="https://www.midjourney.com/@axylusion">Midjourney / @axylusion</a><a href="https://suno.com/@axylusion">Suno / @axylusion</a></div></div></section>"""
    schema = [{"@type": "AboutPage", "@id": f"{DOMAIN}/about.html#about", "name": "About Axy Lusion", "mainEntity": {"@id": "https://koltregaskes.com/#person-kol"}}]
    return page_shell("about.html", "About | Axy Lusion", "About Kol Tregaskes and the Axy Lusion creative archive.", "About", body, schema)


def render_alist(snapshot: dict) -> str:
    categories = snapshot.get("categories", [])
    sections = []
    nav = "".join(f'<a href="#{escape(cat["slug"].replace("_", "-"))}" class="{"is-on" if i == 0 else ""}">{escape(cat.get("title") or cat["slug"])}</a>' for i, cat in enumerate(categories))
    for index, cat in enumerate(categories):
        models = cat.get("models", [])
        if not models:
            continue
        leader = models[0]
        runners = models[1:5]
        def strengths(model, limit=4):
            return "".join(f'<span>{escape(str(s))}</span>' for s in model.get("strengths", [])[:limit])
        def bar(score, small=False):
            score = float(score or 0)
            return f'<div class="cn-alist__bar{" cn-alist__bar--sm" if small else ""}"><div class="cn-alist__fill" style="width:{max(0, min(100, score)):.2f}%"></div><span>{score:.2f}</span></div>'
        arena = "".join(f'<span><strong>{escape(src.get("source_name", ""))}</strong> {escape(str(src.get("raw_score", "")))}</span>' for src in leader.get("sources", [])[:3])
        runner_html = "".join(
            f'<article class="cn-alist__runner"><span class="cn-alist__rrank">#{escape(str(model.get("meta_rank", i + 2)))}</span><div><h3>{escape(model.get("model_name", ""))}</h3><span class="cn-alist__maker">{escape(model.get("model_maker", ""))}</span></div>{bar(model.get("meta_score"), True)}<div class="cn-alist__tags">{strengths(model, 3)}</div></article>'
            for i, model in enumerate(runners)
        )
        sections.append(
            f"""
            <section class="cn-alist" id="{escape(cat['slug'].replace('_', '-'))}">
              <div class="cn-alist__head"><span class="cn-kicker">Category {index + 1}</span><h2 class="cn-h2">{escape(cat.get('title') or cat['slug'])}</h2><p>{escape(cat.get('note') or snapshot.get('methodology_note') or '')}</p></div>
              <article class="cn-alist__leader"><div class="cn-alist__rank">#1</div><div class="cn-alist__leader-body"><h3>{escape(leader.get('model_name', ''))}</h3><span class="cn-alist__maker">{escape(leader.get('model_maker', ''))}</span>{bar(leader.get('meta_score'))}<div class="cn-alist__tags">{strengths(leader)}</div><div class="cn-alist__arena">{arena}</div><p class="cn-alist__note">{escape(leader.get('coverage_label', 'Signal'))} / Coverage {float(leader.get('coverage_percent') or 0):.0f}%. {escape(leader.get('considerations') or '')}</p></div></article>
              <div class="cn-alist__runners">{runner_html}</div>
            </section>"""
        )
    software_items = []
    pos = 1
    for cat in categories:
        for model in cat.get("models", []):
            software_items.append({"@type": "ListItem", "position": pos, "item": {"@type": "SoftwareApplication", "name": model.get("model_name"), "url": model.get("model_url"), "applicationCategory": "DesignApplication", "operatingSystem": "Web"}})
            pos += 1
    schema = [{"@type": "ItemList", "@id": f"{DOMAIN}/a-list.html#list", "name": "Axy Lusion A-List", "numberOfItems": len(software_items), "itemListElement": software_items}]
    body = f"""
      <section class="cn-pagehead"><div class="cn-pagehead__inner"><span class="cn-kicker">Vol. 04 / May 2026</span><h1 class="cn-h1">The A-List</h1><p class="cn-lede">{escape(snapshot.get('methodology_note') or 'Benchmark-led rankings for creative AI.')}</p><div class="cn-method"><span class="cn-method__chip">Artificial Analysis</span><span class="cn-method__chip">LM Arena</span><span class="cn-method__chip">Expert Review</span></div>{untitled_note(True)}</div></section>
      <nav class="cn-alist-nav" aria-label="A-List categories">{nav}</nav>
      {''.join(sections)}"""
    return page_shell("a-list.html", "The A-List | Axy Lusion", "Creative AI tool rankings from Axy Lusion, blending benchmark signals and editorial judgement.", "A-List", body, schema)


def main() -> None:
    gallery_items, home_items = load_and_migrate_gallery()
    snapshot = read_json(ROOT / "data" / "a-list-benchmarks.json")
    write_page(ROOT / "index.html", render_home(gallery_items, home_items))
    write_page(ROOT / "gallery.html", render_gallery(gallery_items))
    write_page(ROOT / "news.html", render_news(gallery_items))
    write_page(ROOT / "blog.html", render_blog(gallery_items))
    write_page(ROOT / "about.html", render_about(gallery_items))
    write_page(ROOT / "a-list.html", render_alist(snapshot))
    print("Rendered cinematic pages and migrated gallery metadata.")


if __name__ == "__main__":
    main()
