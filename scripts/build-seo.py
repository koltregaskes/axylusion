#!/usr/bin/env python3
"""Generate metadata, the page/image sitemap and RSS from checked-in content."""
import argparse
import importlib.util
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime
from urllib.parse import urljoin

from seo import ROOT, DOMAIN, canonical, enhance_html, public_pages, gallery_images

SM = "http://www.sitemaps.org/schemas/sitemap/0.9"
IM = "http://www.google.com/schemas/sitemap-image/1.1"
ATOM = "http://www.w3.org/2005/Atom"
for prefix, namespace in (("", SM), ("image", IM), ("atom", ATOM)):
    ET.register_namespace(prefix, namespace)


def xml(tree):
    ET.indent(tree, space="  ")
    return ET.tostring(tree, encoding="utf-8", xml_declaration=True).decode() + "\n"


def outputs():
    pages = public_pages()
    result = {p: enhance_html(p.read_text(encoding="utf-8"), p.relative_to(ROOT).as_posix()) for p in pages}
    sitemap = ET.Element(f"{{{SM}}}urlset")
    images = list(dict.fromkeys(gallery_images().values()))
    if len(images) > 1000:
        raise ValueError("Gallery exceeds 1,000 images: split the gallery into crawlable pages before expanding its image sitemap.")
    for p in pages:
        relative = p.relative_to(ROOT).as_posix()
        entry = ET.SubElement(sitemap, f"{{{SM}}}url")
        ET.SubElement(entry, f"{{{SM}}}loc").text = canonical(relative)
        if relative == "gallery.html":
            for image in images:
                ET.SubElement(ET.SubElement(entry, f"{{{IM}}}image"), f"{{{IM}}}loc").text = image
    result[ROOT / "sitemap.xml"] = xml(sitemap)
    spec = importlib.util.spec_from_file_location("cinematic", ROOT / "scripts/render-cinematic-site.py")
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    digests = renderer.load_digests(limit=50)
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    for name, value in (("title", "Axy Lusion news and digests"), ("link", DOMAIN + "/news.html"),
                        ("description", "Creative AI news: image, video, music, audio and tools."), ("language", "en-gb")):
        ET.SubElement(channel, name).text = value
    ET.SubElement(channel, f"{{{ATOM}}}link", {"href": DOMAIN + "/feed.xml", "rel": "self", "type": "application/rss+xml"})
    seen = set()
    for digest in digests:
        date = format_datetime(datetime.fromisoformat(digest["date"]).replace(tzinfo=timezone.utc))
        digest_url = urljoin(DOMAIN + "/news-digests/", digest["slug"])
        entries = [("Creative AI digest: " + digest["date"], digest_url,
                    "\n".join(story["title"] + ": " + story["href"] for story in digest["stories"]), "Digest")]
        entries += [(s["title"], s["href"], s["source"], s["topic"]) for s in digest["stories"] if s["href"].startswith("https://")]
        for title, link, description, category in entries:
            if link in seen:
                continue
            seen.add(link)
            item = ET.SubElement(channel, "item")
            for name, value in (("title", title), ("link", link), ("pubDate", date), ("description", description), ("category", category)):
                ET.SubElement(item, name).text = value
            ET.SubElement(item, "guid", {"isPermaLink": "true"}).text = link
    result[ROOT / "feed.xml"] = xml(rss)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    stale = []
    for path, content in outputs().items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.write_text(content, encoding="utf-8")
    if stale:
        raise SystemExit("SEO output is stale. Run python scripts/build-seo.py: " + ", ".join(stale))
    print("SEO output is current." if args.check else "Generated SEO metadata, sitemap and RSS.")
