#!/usr/bin/env python3
"""Offline SEO gate: HTML, real PNG dimensions, sitemap coverage and RSS XML."""
import json
import os
import re
import struct
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site" if (ROOT / "scripts/build.mjs").exists() else ROOT
SM = "http://www.sitemaps.org/schemas/sitemap/0.9"
IM = "http://www.google.com/schemas/sitemap-image/1.1"
ATOM = "http://www.w3.org/2005/Atom"


class Head(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.meta, self.links = {}, []
        self.feed(text.split("</head>", 1)[0])

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            self.meta.setdefault(a.get("name", a.get("property", "")), []).append(a.get("content", ""))
        elif tag == "link":
            self.links.append(a)

    def one(self, name):
        values = self.meta.get(name, [])
        assert len(values) == 1 and values[0], f"Missing or duplicate {name}"
        return values[0]


def local(url):
    relative = unquote(urlparse(url).path).removeprefix(base_path).lstrip("/")
    path = SITE / relative
    return path / "index.html" if path.is_dir() else path


if __name__ == "__main__":
    domain = (os.environ.get("CUSTOM_DOMAIN") or (ROOT / "CNAME").read_text(encoding="utf-8").strip()).removeprefix("https://").removeprefix("http://").rstrip("/") if SITE != ROOT else "axylusion.com"
    base = f"https://{domain}"
    base_path = urlparse(base).path
    expected, image_count = set(), 0
    for page in sorted(SITE.rglob("*.html")):
        if any(part.startswith(".") for part in page.relative_to(SITE).parts):
            continue
        text = page.read_text(encoding="utf-8")
        head = Head(text)
        if any("noindex" in value for value in head.meta.get("robots", [])) or re.search(r'http-equiv=["\']refresh', text, re.I):
            continue
        relative = page.relative_to(SITE).as_posix()
        if relative == "index.html":
            relative = ""
        elif relative.endswith("/index.html"):
            relative = relative[:-10]
        url = base + "/" + relative
        try:
            canonical = [a["href"] for a in head.links if a.get("rel") == "canonical"]
            assert canonical == [url], f"Wrong canonical: {canonical}"
            assert url not in expected, "Duplicate canonical"
            expected.add(url)
            assert head.one("og:url") == url
            for key in ("description", "og:title", "og:description", "og:type", "og:site_name", "twitter:title", "twitter:description", "og:image:alt", "twitter:image:alt"):
                head.one(key)
            assert head.one("twitter:card") == "summary_large_image"
            image = head.one("og:image")
            assert image == head.one("twitter:image") and image.startswith(base + "/") and image.endswith(".png")
            raw = local(image).read_bytes()
            assert raw[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", raw[16:24]) == (1200, 630), "Social image must be a 1200x630 PNG"
            assert head.one("og:image:width") == "1200" and head.one("og:image:height") == "630"
            assert head.one("og:image:type") == "image/png"
            assert [a["href"] for a in head.links if a.get("type") == "application/rss+xml"] == [base + "/feed.xml"]
            schemas = [json.loads(m) for m in re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', text, re.S)]
            assert schemas, "Missing JSON-LD"
            nodes = [node for schema in schemas for node in schema.get("@graph", [schema])]
            assert any(node.get("url") == url for node in nodes), "JSON-LD missing the page URL"
            if relative.startswith("posts/") and relative != "posts/":
                assert any(n.get("@type") == "BlogPosting" and n.get("headline") and n.get("author") and n.get("datePublished") for n in nodes), "Missing article metadata"
            if relative == "gallery.html":
                assert any(n.get("@type") == "ImageGallery" and n.get("image") for n in nodes)
                assert any(n.get("@type") == "ImageGallery" and n.get("hasPart") and all(isinstance(x, dict) and x.get("@type") == "VisualArtwork" for x in n["hasPart"]) for n in nodes), "Gallery artwork metadata was lost"
            if relative == "blog-welcome.html":
                assert any(n.get("@type") == "CreativeWork" for n in nodes)
        except (AssertionError, KeyError, ValueError) as error:
            raise SystemExit(f"{relative or 'index.html'}: {error}") from error
    sitemap = ET.parse(SITE / "sitemap.xml").getroot()
    assert sitemap.tag == f"{{{SM}}}urlset"
    urls = [node.text for node in sitemap.findall(f"{{{SM}}}url/{{{SM}}}loc")]
    assert len(urls) == len(set(urls)) and set(urls) == expected, f"Sitemap coverage mismatch: {set(urls) ^ expected}"
    for entry in sitemap:
        images = entry.findall(f"{{{IM}}}image/{{{IM}}}loc")
        assert len(images) <= 1000
        for image in images:
            assert image.text.startswith("https://") and "midjourney.com" not in image.text
        image_count += len(images)
    if SITE == ROOT:
        assert image_count > 0, "Missing gallery image sitemap entries"
    rss = ET.parse(SITE / "feed.xml").getroot()
    assert rss.tag == "rss" and rss.get("version") == "2.0"
    channel = rss.find("channel")
    for key in ("title", "link", "description", "language"):
        assert channel.findtext(key)
    assert channel.find(f"{{{ATOM}}}link").get("href") == base + "/feed.xml"
    items = channel.findall("item")
    assert items, "Empty RSS"
    guids, dates = set(), []
    for item in items:
        for key in ("title", "link", "guid", "description", "pubDate"):
            assert item.findtext(key), f"RSS item missing {key}"
        link, guid = item.findtext("link"), item.findtext("guid")
        assert guid not in guids and link.startswith("https://")
        guids.add(guid)
        dates.append(parsedate_to_datetime(item.findtext("pubDate")))
        if link.startswith(base + "/"):
            assert local(link).exists(), f"RSS link has no local target: {link}"
    assert dates == sorted(dates, reverse=True), "RSS dates are not newest first"
    robots = (SITE / "robots.txt").read_text(encoding="utf-8")
    assert f"Sitemap: {base}/sitemap.xml" in robots
    assert not re.search(r"^Disallow:\s*/\s*$", robots, re.M)
    print(f"SEO checks passed: {len(expected)} pages, {len(urls)} sitemap URLs, {image_count} gallery images, {len(items)} RSS items.")
