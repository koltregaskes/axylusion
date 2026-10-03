"""Regression checks for migrated homepage media and generated output."""
import importlib.util
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("renderer", ROOT / "scripts/render-cinematic-site.py")
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "img" and attrs.get("class") == "cn-frame__img":
            self.sources.append(attrs["src"])


class HomepageMediaTests(unittest.TestCase):
    def test_migrated_url_precedes_legacy_src(self):
        item = {"cdn_url": "https://assets.example/image.png", "src": "old.png"}
        self.assertEqual(renderer.image_source(item), item["cdn_url"])
        self.assertIn(item["cdn_url"], renderer.frame_style(item))
        self.assertIn(item["cdn_url"], renderer.frame(item, 0))

    def test_unavailable_media_keeps_gradient(self):
        for source in ("", "https://cdn.midjourney.com/id/0_0.png", "javascript:alert(1)"):
            item = {"cdn_url": source}
            self.assertEqual(renderer.image_source(item), "")
            self.assertNotIn("<img", renderer.frame(item, 0))
            self.assertIn("gradient", renderer.frame_style(item))
        self.assertEqual(renderer.image_source({"cdn_url": "https://cdn.midjourney.com/id/0_0.png", "src": "images/local.png"}), "images/local.png")

    def test_all_curated_images_are_rendered_and_output_is_current(self):
        home = json.loads((ROOT / "data/homepage-gallery.json").read_text(encoding="utf-8"))["items"]
        rendered = renderer.clean_page(renderer.render_home(renderer.load_gallery_for_render(), home))
        parser = Images()
        parser.feed(rendered)
        self.assertEqual(len(home), 18)
        self.assertEqual(parser.sources, [item["cdn_url"] for item in home])
        self.assertEqual(len(set(parser.sources)), 18)
        self.assertEqual(rendered, (ROOT / "index.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
