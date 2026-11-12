"""Shared, deterministic metadata for hand-written and generated public pages."""
import json
import re
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from functools import cache

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = "https://axylusion.com"
IMAGE = f"{DOMAIN}/images/social-default.png"
NONCE = "axylusion-cinematic-schema"


class Head(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.meta, self.links = {}, []
        self.feed(text.split("</head>", 1)[0])

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "meta":
            self.meta[attrs.get("name", attrs.get("property", ""))] = attrs.get("content", "")
        if tag == "link":
            self.links.append(attrs)


def canonical(relative):
    return DOMAIN + ("/" if relative == "index.html" else "/" + relative)


def public_pages():
    return sorted(p for p in [*ROOT.glob("*.html"), *ROOT.joinpath("a-list").glob("*.html")]
                  if "noindex" not in Head(p.read_text(encoding="utf-8")).meta.get("robots", ""))


@cache
def gallery_images():
    """Use durable URLs already present in the site, never invent CDN paths."""
    home = json.loads((ROOT / "data/homepage-gallery.json").read_text(encoding="utf-8"))["items"]
    durable = {str(x.get("id")): x.get("cdn_url", "") for x in home}
    gallery = json.loads((ROOT / "data/gallery.json").read_text(encoding="utf-8"))["items"]
    result = {}
    for item in gallery:
        if item.get("media_status") == "unavailable" or item.get("type", "image") != "image":
            continue
        for value in (item.get("cdn_url"), item.get("src"), durable.get(str(item.get("id")))):
            if not value or "midjourney.com" in value:
                continue
            absolute = urljoin(DOMAIN + "/", value)
            if absolute.startswith("https://"):
                result[str(item["id"])] = absolute
                break
    return result


def enhance_html(text, relative):
    head = Head(text)
    title = unescape(re.search(r"<title>(.*?)</title>", text, re.S | re.I).group(1))
    description = head.meta.get("description", title)
    url = canonical(relative)
    # Replace our block and legacy social tags without touching page content or CSP.
    text = re.sub(r"\s*<!-- SEO:start -->.*?<!-- SEO:end -->", "", text, flags=re.S)
    text = re.sub(r'\s*<meta\b(?=[^>]*(?:name|property)=[\"\'](?:og:|twitter:))[^>]*>', "", text, flags=re.I)
    text = re.sub(r'\s*<link\b(?=[^>]*rel=[\"\']canonical[\"\'])[^>]*>', "", text, flags=re.I)
    text = re.sub(r'\s*<link\b(?=[^>]*type=[\"\']application/rss\+xml[\"\'])[^>]*>', "", text, flags=re.I)
    values = {"og:title": title, "og:description": description, "og:type": "article" if relative == "blog-welcome.html" else "website",
              "og:url": url, "og:site_name": "Axy Lusion", "og:locale": "en_GB", "og:image": IMAGE,
              "og:image:type": "image/png", "og:image:width": "1200", "og:image:height": "630",
              "og:image:alt": "Axy Lusion: AI art, music and motion",
              "twitter:card": "summary_large_image", "twitter:site": "@Axylusion",
              "twitter:title": title, "twitter:description": description, "twitter:image": IMAGE,
              "twitter:image:alt": "Axy Lusion: AI art, music and motion"}
    tags = [f'<link rel="canonical" href="{escape(url)}">',
            f'<link rel="alternate" type="application/rss+xml" title="Axy Lusion news and digests" href="{DOMAIN}/feed.xml">']
    tags += [f'<meta {"property" if key.startswith("og:") else "name"}="{key}" content="{escape(value)}">' for key, value in values.items()]
    schema = {"@context": "https://schema.org", "@type": "CreativeWork" if relative == "blog-welcome.html" else "WebPage",
              "@id": url + "#page", "url": url, "name": title, "description": description,
              "image": IMAGE, "inLanguage": "en-GB", "isPartOf": {"@id": DOMAIN + "/#website"}}
    if relative == "blog-welcome.html":
        schema["creator"] = {"@type": "Person", "name": "Kol Tregaskes"}
    if relative == "gallery.html":
        schema["@type"] = "ImageGallery"
        schema["image"] = list(gallery_images().values())
        # Older output puts VisualArtwork in ImageGallery.image (which expects images).
        def fix_gallery(match):
            payload = json.loads(match.group(1))
            for node in payload.get("@graph", []):
                if node.get("@type") == "ImageGallery":
                    if "hasPart" not in node:
                        node["hasPart"] = node.get("image", [])
                    node["image"] = list(gallery_images().values())
            return f'<script type="application/ld+json" nonce="{NONCE}">{json.dumps(payload, ensure_ascii=True)}</script>'
        text = re.sub(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', fix_gallery, text, flags=re.S)
    tags.append(f'<script type="application/ld+json" nonce="{NONCE}">{json.dumps(schema, ensure_ascii=True).replace("<", chr(92) + "u003c")}</script>')
    block = "\n  <!-- SEO:start -->\n  " + "\n  ".join(tags) + "\n  <!-- SEO:end -->\n"
    return text.replace("</head>", block + "</head>")
