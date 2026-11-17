"""Offline acceptance checks for edition provenance, closed signups and build output."""
import hashlib
import json
import subprocess
import sys
import unittest
from datetime import date
from html.parser import HTMLParser
from unittest.mock import patch
from types import SimpleNamespace

import newsletter
from site_config import ROOT, require_closed_newsletter


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class NewsletterTests(unittest.TestCase):
    def test_false_is_the_only_allowed_flag(self):
        require_closed_newsletter({"newsletter": {"signupsOpen": False}})
        for value in [True, 0, "false", None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                require_closed_newsletter({"newsletter": {"signupsOpen": value}})
        with self.assertRaises(ValueError):
            require_closed_newsletter({})

    def test_cli_build_rejects_open_signup_before_writing(self):
        config = ROOT / "data/site-config.json"
        original = config.read_bytes()
        outputs = newsletter.outputs()
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs}
        try:
            value = json.loads(original)
            value["newsletter"]["signupsOpen"] = True
            config.write_text(json.dumps(value), encoding="utf-8", newline="\n")
            result = subprocess.run([sys.executable, "-B", "scripts/build-seo.py"], cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("sign-ups must stay closed", result.stderr)
            self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs})
        finally:
            config.write_bytes(original)

    def test_signup_page_collects_nothing(self):
        text = newsletter.outputs()[ROOT / "newsletter.html"]
        page = Page(text)
        for tag, attrs in page.tags:
            self.assertNotIn(tag, ["form", "input", "button", "iframe"])
            self.assertNotIn("action", attrs)
            self.assertFalse(any(key.startswith("on") for key in attrs))
        self.assertIn("Sign-ups open at launch", text)
        for phrase in ["email address, chosen categories", "time you give consent", "consent version", "consent source", "confirm your email", "one-click unsubscribe", "change your categories"]:
            self.assertIn(phrase, text)
        notice = (ROOT / 'privacy.html').read_text(encoding='utf-8')
        for phrase in ['Planned, not active:', 'email address, chosen categories, consent time, consent version and consent source', 'double opt-in', 'one-click unsubscribe']:
            self.assertIn(phrase, notice)
        for forbidden in ["fetch(", "XMLHttpRequest", "sendBeacon", "mailto:"]:
            self.assertNotIn(forbidden, text)

    def test_mapping_is_shared_with_news_and_complete(self):
        renderer = newsletter.renderer()
        self.assertEqual(renderer.TOPIC_ALIASES, newsletter.CATEGORY_MAP["tags"])
        self.assertEqual(set(newsletter.CATEGORY_MAP["tags"].values()), set(newsletter.CATEGORY_MAP["topics"]))
        self.assertEqual(newsletter.CATEGORY_MAP["topics"]["Image"], "Visuals")
        self.assertEqual(newsletter.CATEGORY_MAP["topics"]["Tools"], "Workflows")
        self.assertEqual(newsletter.CATEGORY_MAP["topics"]["3D"], "Visuals")
        self.assertEqual(newsletter.CATEGORY_MAP["topics"]["Benchmarks"], "Workflows")
        news = Page((ROOT / "news.html").read_text(encoding="utf-8"))
        embedded = [attrs["data-news-topics"] for _, attrs in news.tags if "data-news-topics" in attrs]
        self.assertEqual(len(embedded), 1)
        self.assertEqual(json.loads(embedded[0]), newsletter.CATEGORY_MAP["tags"])

    def test_actual_source_date_is_not_digest_date(self):
        r = newsletter.renderer()
        fixture = "**2026-11-15** | 1 stories\n\n## [Fixture](https://example.invalid)\n*Fixture source* | 14/11/2026 | Score: 1\nTags: music_gen\n\n---\n"
        with patch("pathlib.Path.read_text", return_value=fixture):
            digest = r.parse_digest(ROOT / "fixture.md")
        self.assertEqual(digest["date"], "2026-11-15")
        self.assertEqual(digest["stories"][0]["sourceDate"], "2026-11-14")
        feed = json.loads((ROOT / "news-digests/news-feed-latest.json").read_text(encoding="utf-8"))
        actual = next(entry for entry in newsletter.load_editions() if entry.get("feedStatus") is not None)
        self.assertEqual(actual["updated"], feed["generated"])
        self.assertEqual(actual["feedStatus"]["articleCount"], len(feed["articles"]))
        text = newsletter.outputs()[ROOT / f'editions/{actual["date"]}.html']
        self.assertIn(f'Routed feed: {len(feed["articles"])} articles', text)
        self.assertIn(feed["generated"], text)

    def test_every_item_has_a_dated_or_explicit_unknown_source(self):
        for edition in newsletter.load_editions():
            urls = [item["url"] for item in edition["items"]]
            self.assertEqual(len(urls), len(set(urls)))
            for item in edition["items"]:
                self.assertIn(item["category"], newsletter.CATEGORIES)
                self.assertTrue(item["sourceDate"] is None or date.fromisoformat(item["sourceDate"]))
                self.assertTrue(item["url"].startswith("https://"))

    def test_empty_feed_creates_an_honest_empty_edition(self):
        feed = {"generated": "2026-11-16T05:15:00Z", "article_count": 0, "articles": [], "failed_sources": ["fixture failure"], "partial": True}
        with patch.object(newsletter, "renderer", return_value=SimpleNamespace(load_digests=lambda **kw: [])), patch("pathlib.Path.read_text", return_value=json.dumps(feed)):
            editions = newsletter.load_editions()
        self.assertEqual(len(editions), 1)
        self.assertEqual(editions[0]["date"], "2026-11-16")
        self.assertEqual(editions[0]["items"], [])
        self.assertEqual(editions[0]["feedStatus"], {"articleCount": 0, "failedSources": 1, "partial": True})
        self.assertIn("No fresh items", newsletter.category_html(editions[0], "Audio"))

    def test_missing_digest_date_never_becomes_a_1970_edition(self):
        digest = {"date": "1970-01-01", "slug": "undated.md", "stories": []}
        with patch.object(newsletter, "renderer", return_value=SimpleNamespace(load_digests=lambda **kw: [digest])), patch("pathlib.Path.read_text", return_value="No date recorded"), self.assertRaisesRegex(ValueError, "explicit digest date"):
            newsletter.load_editions()

    def test_empty_old_future_and_unknown_dates_are_not_fresh(self):
        for source in [None, "2026-11-12", "2026-11-16"]:
            item = {"sourceDate": source, "category": "Audio", "url": "https://example.invalid", "title": "Fixture", "source": "Fixture"}
            text = newsletter.category_html({"date": "2026-11-15", "items": [item]}, "Audio")
            self.assertIn("No fresh items", text)
            self.assertNotIn("Fresh for this edition", text)
        self.assertTrue(newsletter.fresh("2026-11-14", "2026-11-15"))
        self.assertTrue(newsletter.fresh("2026-11-15", "2026-11-15"))
        self.assertIsNone(newsletter.source_date("bad"))
        self.assertIsNone(newsletter.source_date("2026-02-30"))

    def test_every_category_has_a_section_and_empty_state(self):
        for edition in newsletter.load_editions():
            for category in newsletter.CATEGORIES:
                text = newsletter.category_html(edition, category)
                self.assertIn(f'id="{category.lower()}"', text)
                if not any(item["category"] == category and newsletter.fresh(item["sourceDate"], edition["date"]) for item in edition["items"]):
                    self.assertIn("No fresh items", text)

    def test_source_text_is_escaped_and_urls_are_restricted(self):
        item = {"sourceDate": None, "category": "Audio", "url": "https://example.invalid/?x=1&y=2", "title": "<script>fixture</script>", "source": "<b>fixture</b>"}
        text = newsletter.category_html({"date": "2026-11-15", "items": [item]}, "Audio")
        self.assertNotIn("<script>", text)
        self.assertIn("&lt;script&gt;", text)
        self.assertIn("Source date: unavailable", text)
        for url in ["javascript:alert(1)", "http://example.invalid", "https://user:pass@example.invalid"]:
            with self.assertRaises(ValueError):
                newsletter.safe_source(url)

    def test_generated_html_has_landmarks_relative_assets_and_csp(self):
        for path, text in newsletter.outputs().items():
            if path.suffix != ".html":
                continue
            page = Page(text)
            self.assertEqual(sum(tag == "main" for tag, _ in page.tags), 1)
            self.assertEqual(sum(tag == "h1" for tag, _ in page.tags), 1)
            self.assertIn('lang="en-GB"', text)
            self.assertIn('class="skip-link"', text)
            self.assertEqual(sum(tag == "meta" and attrs.get("http-equiv") == "Content-Security-Policy" for tag, attrs in page.tags), 1)
            if path.parent.name == "editions":
                self.assertIn('href="../cinematic.css"', text)
                self.assertIn('src="../scripts/cinematic.js"', text)
                self.assertIn('href="../privacy.html"', text)

    def test_generation_is_byte_stable_lf_and_bom_free(self):
        first = newsletter.outputs()
        self.assertEqual(first, newsletter.outputs())
        for path, text in first.items():
            self.assertEqual(path.read_bytes(), text.encode("utf-8"), str(path))
            self.assertNotIn(b"\r", path.read_bytes())
            self.assertFalse(path.read_bytes().startswith(b"\xef\xbb\xbf"))
        self.assertGreater(len(first), 2)


if __name__ == "__main__":
    unittest.main()
