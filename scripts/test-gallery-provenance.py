"""Offline regressions for collection credits and honest image schema."""
import importlib.util
import json
import re
import unittest
from html.parser import HTMLParser

from provenance import (CREATOR, COPYRIGHT_NOTICE, PRODUCTION, RIGHTS_NOTE,
                        credit_text, provenance_fields)
from seo import ROOT, RenderedImages, enhance_html, rendered_image_objects

spec = importlib.util.spec_from_file_location("cinematic", ROOT / "scripts/render-cinematic-site.py")
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class CreditParser(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.credits = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "cn-provenance" in attrs.get("class", "").split():
            self.credits.append(attrs)


class ProvenanceTests(unittest.TestCase):
    def test_one_item_before_batch(self):
        item = {"id": "example", "model": "Midjourney v7", "created": "2025-12-13"}
        fields = provenance_fields(item)
        self.assertEqual(fields["creator"], CREATOR)
        self.assertEqual(credit_text({**item, **fields}),
                         "Kol Tregaskes / Midjourney v7 / 13 Dec 2025 / AI-generated")

    def test_missing_dates_and_tools_are_not_invented(self):
        self.assertIn("Date not recorded", credit_text({"source": "midjourney"}))
        with self.assertRaisesRegex(ValueError, "Missing tool/model evidence"):
            provenance_fields({"id": "no-tool"})

    def test_export_and_homepage_rebuild_keep_provenance(self):
        def load(name):
            spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        source = {"id": "example", "source": "midjourney", "model": "Midjourney v6",
                  "created": "2024-03-10", "cdn_url": "https://example.invalid/image.png"}
        exported = load("export-published-gallery").merge_item(source, {"media_status": "unavailable"}, [])
        self.assertEqual(exported["media_status"], "unavailable")
        self.assertEqual(exported["tool"], source["model"])
        rebuilt, missing = load("rebuild-homepage-gallery").rebuild_items([{"id": source["id"]}], {source["id"]: source})
        self.assertEqual(missing, [])
        self.assertEqual(rebuilt[0]["production"], PRODUCTION)
        self.assertEqual(rebuilt[0]["tool"], source["model"])

    def test_every_record_has_evidence_backed_provenance(self):
        gallery = json.loads((ROOT / "data/gallery.json").read_text(encoding="utf-8"))["items"]
        lookup = {item["id"]: item for item in gallery}
        home = json.loads((ROOT / "data/homepage-gallery.json").read_text(encoding="utf-8"))["items"]
        for item in gallery + home:
            with self.subTest(item=item["id"]):
                self.assertEqual(item["tool"], lookup[item["id"]].get("model") or lookup[item["id"]]["source"])
                self.assertEqual(item["creator"], CREATOR)
                self.assertEqual(item["production"], PRODUCTION)
                self.assertEqual(item["copyright_notice"], COPYRIGHT_NOTICE)
                self.assertEqual(item["rights_note"], RIGHTS_NOTE)

    def test_schema_matches_rendered_images_and_has_no_reuse_licence(self):
        for relative in ("gallery.html", "index.html"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            objects = rendered_image_objects(text, relative)
            self.assertTrue(objects)
            self.assertEqual({obj["contentUrl"] for obj in objects}, RenderedImages(text).sources)
            for obj in objects:
                self.assertEqual(obj["@type"], "ImageObject")
                self.assertEqual(obj["creator"], {"@type": "Person", "name": CREATOR})
                self.assertIn("AI-generated", obj["creditText"])
                self.assertEqual(obj["copyrightNotice"], COPYRIGHT_NOTICE)
                self.assertNotIn("license", obj)
            # A data record alone must never create image schema.
            without_images = re.sub(r"<img\b[^>]*>", "", text)
            self.assertEqual(rendered_image_objects(without_images, relative), [])
            self.assertEqual(enhance_html(text, relative), text)
            if relative == "gallery.html":
                graph = json.loads(re.search(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', text, re.S)[1])["@graph"]
                page = next(node for node in graph if node.get("@type") == "ImageGallery")
                self.assertEqual(len(page["hasPart"]), len(objects))

    def test_credits_stay_visible_without_prompt_captions(self):
        item = json.loads((ROOT / "data/homepage-gallery.json").read_text(encoding="utf-8"))["items"][0]
        text = renderer.frame(item, 0, caption=False)
        credits = CreditParser(text).credits
        self.assertEqual(len(credits), 1)
        self.assertNotIn("hidden", credits[0])
        self.assertNotIn("aria-hidden", credits[0])
        self.assertNotIn("cn-frame__cap--optional", credits[0]["class"])
        self.assertIn("about.html#image-rights", text)
        self.assertIn('alt="' + renderer.escape(renderer.image_alt(item)) + '"', text)

    def test_hero_credit_is_in_payload_for_every_selection(self):
        text = (ROOT / "index.html").read_text(encoding="utf-8")
        from html import unescape
        items = json.loads(unescape(re.search(r"data-hero-items='([^']+)'", text)[1]))
        self.assertEqual(len(items), 8)
        for item in items:
            self.assertIn(CREATOR, item["credit"])
            self.assertIn("AI-generated", item["credit"])
        self.assertIn('data-hero-credit aria-live="polite"', text)

    def test_rights_statement_has_one_target(self):
        text = (ROOT / "about.html").read_text(encoding="utf-8")
        self.assertEqual(text.count('id="image-rights"'), 1)
        self.assertIn("Rights in AI-generated images are uncertain.", text)
        self.assertIn("Terms-of-Service", text)


if __name__ == "__main__":
    unittest.main()
