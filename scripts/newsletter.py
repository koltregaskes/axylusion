"""Deterministic daily editions from the same indexed digests as News.

No clock, fetch, credentials, subscriber store or provider is used at build time.
"""
import importlib.util
import json
import re
from datetime import date, datetime, timedelta, timezone
from html import escape
from urllib.parse import urlsplit

from site_config import ROOT, require_closed_newsletter

CATEGORY_MAP = json.loads((ROOT / "newsletter/categories.json").read_text(encoding="utf-8"))
CATEGORIES = CATEGORY_MAP["categories"]
WINDOW = 32  # Same archive window as the News page; old output is retained.


def renderer():
    spec = importlib.util.spec_from_file_location("newsletter_cinematic", ROOT / "scripts/render-cinematic-site.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return None


def fresh(source, edition):
    return bool(source and date.fromisoformat(edition) - timedelta(days=1)
                <= date.fromisoformat(source) <= date.fromisoformat(edition))


def safe_source(url):
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Edition sources must be public HTTPS URLs")
    return url


def load_editions():
    r = renderer()
    editions = {}
    for digest in r.load_digests(limit=WINDOW):
        raw = (ROOT / "news-digests" / digest["slug"]).read_text(encoding="utf-8")
        if not re.search(r"\*\*" + re.escape(digest["date"]) + r"\*\*", raw):
            raise ValueError("An edition requires an explicit digest date")
        day = date.fromisoformat(digest["date"]).isoformat()
        edition = editions.setdefault(day, {"date": day, "updated": day, "items": [], "digests": []})
        edition["digests"].append(digest["slug"])
        for story in digest["stories"]:
            edition["items"].append({
                "title": story["title"], "url": safe_source(story["href"]), "source": story["source"],
                "sourceDate": source_date(story.get("sourceDate")),
                "category": CATEGORY_MAP["topics"][story["topic"]],
            })
    # Include the routed snapshot even if empty. Its generation time is never
    # substituted for a story publication date or proof of editorial delivery.
    feed = json.loads((ROOT / "news-digests/news-feed-latest.json").read_text(encoding="utf-8"))
    stamp = datetime.fromisoformat(feed["generated"].replace("Z", "+00:00"))
    if stamp.utcoffset() is None:
        raise ValueError("Routed feed generation time needs a timezone")
    day = stamp.astimezone(timezone.utc).date().isoformat()
    edition = editions.setdefault(day, {"date": day, "updated": day, "items": [], "digests": []})
    edition["updated"] = feed["generated"]
    articles = feed["articles"]
    if feed["article_count"] != len(articles):
        raise ValueError("Routed feed article count mismatch")
    edition["feedStatus"] = {"articleCount": len(articles), "partial": bool(feed.get("partial")),
                             "failedSources": len(feed.get("failed_sources", []))}
    for article in articles:
        tags = [*(article.get("matching_tags") or []), *(article.get("tags") or [])]
        topic = next((CATEGORY_MAP["tags"][tag] for tag in tags if tag in CATEGORY_MAP["tags"]), "Tools")
        raw_date = article.get("date", "")
        parsed = datetime.fromisoformat(raw_date.replace("Z", "+00:00")) if raw_date else None
        edition["items"].append({"title": article["title"], "url": safe_source(article["url"]),
                                 "source": article["source"], "sourceDate": parsed.date().isoformat() if parsed else None,
                                 "category": CATEGORY_MAP["topics"][topic]})
    for edition in editions.values():
        seen = set()
        edition["items"] = [item for item in edition["items"] if not (item["url"] in seen or seen.add(item["url"]))]
        edition["url"] = f'https://axylusion.com/editions/{edition["date"]}.html'
    return sorted(editions.values(), key=lambda entry: entry["date"], reverse=True)


def category_html(edition, category):
    items = [item for item in edition["items"] if item["category"] == category]
    current = [item for item in items if fresh(item["sourceDate"], edition["date"])]
    rows = []
    for item in items:
        source = item["sourceDate"]
        dated = f'<time datetime="{source}">{source}</time>' if source else "unavailable"
        status = "Fresh for this edition" if item in current else "Outside the freshness window or undated"
        rows.append(f'<li><a href="{escape(item["url"], quote=True)}">{escape(item["title"])}</a>'
                    f'<p>{escape(item["source"])} · Source date: {dated}. {status}.</p></li>')
    empty = "" if current else "<p>No fresh items in this category for this edition.</p>"
    return f'<section aria-labelledby="{category.lower()}"><h2 id="{category.lower()}" class="cn-h2">{category}</h2>{empty}' + ("<ul>" + "".join(rows) + "</ul>" if rows else "") + "</section>"


def wrap(r, path, title, copy):
    body = f'<section class="cn-pagehead"><div class="cn-pagehead__inner cn-about-grid__body cn-privacy cn-edition"><h1 class="cn-h1">{escape(title)}</h1>{copy}</div></section>'
    return r.clean_page(r.page_shell(path, title + " | Axy Lusion", "Source-dated creative AI editions: Visuals, Video, Audio and Workflows. Email sign-ups open at launch.", "News", body))


def outputs():
    require_closed_newsletter()
    r = renderer()
    editions = load_editions()
    result = {}
    for edition in editions:
        day = edition["date"]
        updated = escape(edition["updated"])
        precision = "routed feed snapshot; not a story publication time" if "T" in updated else "digest date; exact update time unavailable"
        copy = f'<p>Last updated: <time datetime="{updated}">{updated}</time> ({precision}).</p>'
        copy += '<p>Fresh means a source date on the edition day or the preceding day. Older and undated items are labelled. These are archive snapshots; live freshness and email delivery have not been verified.</p>'
        status = edition.get("feedStatus")
        if status is not None:
            copy += f'<p>Routed feed: {status["articleCount"]} articles; {status["failedSources"]} failed sources; partial coverage: {str(status["partial"]).lower()}. Indexed digest items are shown separately from this feed status. An empty feed does not prove successful editorial delivery.</p>'
        copy += "".join(category_html(edition, category) for category in CATEGORIES)
        if edition["digests"]:
            copy += '<h2 class="cn-h2">Edition sources</h2><ul>' + "".join(f'<li><a href="../news-digests/{escape(slug)}">Digest {day}</a></li>' for slug in edition["digests"]) + '</ul>'
        copy += '<p><a href="../editions.html">All editions</a> · <a href="../newsletter.html">Newsletter</a> · <a href="../news.html">News archive</a></p>'
        result[ROOT / f"editions/{day}.html"] = wrap(r, f"editions/{day}.html", f"Creative edition: {day}", copy)
    latest = editions[0]
    links = "".join(f'<li><a href="editions/{entry["date"]}.html">Creative edition: {entry["date"]}</a></li>' for entry in editions)
    result[ROOT / "editions.html"] = wrap(r, "editions.html", "Daily creative editions",
        f'<p>Last updated: <time datetime="{escape(latest["updated"])}">{escape(latest["updated"])}</time> (latest source snapshot).</p><p>Visuals, Video, Audio and Workflows, drawn from the News archive and routed feed. Edition dates come from those sources, never the build clock. The latest 32 indexed digests are included; days with no indexed digest or routed snapshot are not invented.</p><p><a href="newsletter.html">Newsletter: sign-ups open at launch</a></p><ul>{links}</ul>')
    result[ROOT / "newsletter.html"] = wrap(r, "newsletter.html", "Newsletter",
        '<p class="cn-kicker">Sign-ups open at launch</p>'
        '<p>A daily creative AI edition, with your choice of Visuals, Video, Audio and Workflows.</p>'
        '<p>Email subscriptions are not available yet. This page does not collect or store your email address or preferences.</p>'
        '<h2 class="cn-h2">Read the daily edition</h2><p><a href="editions.html">Browse the source-dated editions</a>. Each edition shows source dates, its last update and categories with no fresh items.</p>'
        '<h2 class="cn-h2">Choose your categories at launch</h2><ul><li>Visuals: images and 3D.</li><li>Video: moving-image tools and stories.</li><li>Audio: music, sound and voice.</li><li>Workflows: creative tools and benchmarks.</li></ul>'
        '<h2 class="cn-h2">Consent and preferences</h2><p>At launch, we plan to store your email address, chosen categories and the time you give consent, plus confirmation, preference and unsubscribe records needed to manage your subscription. You will need to confirm your email before receiving editions. You will be able to change your categories through a private link.</p>'
        '<h2 class="cn-h2">Unsubscribe</h2><p>Every email will include an unsubscribe link and support your email app\'s one-click unsubscribe. Unsubscribing will stop future editions. No subscription is created on this page.</p>'
        '<p>Provider, retention and delivery details will be confirmed before sign-ups open. <a href="privacy.html">Read the current privacy notice</a>.</p>')
    result[ROOT / "data/newsletter-editions.json"] = json.dumps({"editions": editions}, indent=2, ensure_ascii=True) + "\n"
    return result


def generate(check=False):
    result = outputs()
    stale = [str(path.relative_to(ROOT)) for path, text in result.items()
             if not path.exists() or path.read_bytes() != text.encode("utf-8")]
    if check and stale:
        raise ValueError("Newsletter output stale: " + ", ".join(stale))
    if not check:
        for path, text in result.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
    return len(result)
