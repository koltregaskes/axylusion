"""Offline skip-link regressions, including previously accepted broken targets."""
from html.parser import HTMLParser
from urllib.parse import unquote
import unittest

from navigation import ensure_navigation
from public_files import ROOT, public_files


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids, self.skips = set(), []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        if tag == 'a' and 'skip-link' in attrs.get('class', '').split():
            self.skips.append(attrs.get('href', ''))


class NavigationTests(unittest.TestCase):
    def check_page(self, source):
        result = ensure_navigation(source)
        parsed = Page(result)
        self.assertTrue(parsed.skips)
        for href in parsed.skips:
            self.assertTrue(href.startswith('#'))
            self.assertIn(unquote(href[1:]), parsed.ids)
        self.assertEqual(ensure_navigation(result), result)
        return result

    def test_stale_skip_link_follows_main_id(self):
        self.check_page('<body><a class="skip-link" href="#old">Skip</a><main id="new"></main></body>')

    def test_data_id_is_not_a_landmark_id(self):
        result = self.check_page('<body><main data-id="record"></main></body>')
        self.assertIn('data-id="record"', result)
        self.assertIn('id="main-content"', result)

    def test_missing_empty_and_boolean_id(self):
        for attr in ('', 'id=""', 'id'):
            with self.subTest(attr=attr):
                self.check_page(f'<body><main {attr}></main></body>')

    def test_class_prefix_and_non_anchor_do_not_suppress_skip(self):
        for tag in ('<a class="skip-link-icon" href="#missing">Icon</a>', '<div class="skip-link">Label</div>'):
            with self.subTest(tag=tag):
                self.check_page(f'<body>{tag}<main></main></body>')

    def test_attribute_spellings_and_missing_href(self):
        self.check_page("<BODY><A CLASS = 'other skip-link active' data-href='old'>Skip</A><MAIN ID = 'actual'></MAIN></BODY>")

    def test_entities_and_fragment_delimiters(self):
        self.check_page('<body><a class="skip-link" href="#old">Skip</a><main id="a&amp;b?#%é"></main></body>')

    def test_attribute_looking_text_is_preserved(self):
        result = self.check_page('<body><a title="href=keep" class="skip-link" href="#old">Skip</a><main title="id=keep" data-id="x"></main></body>')
        self.assertIn('title="href=keep"', result)
        self.assertIn('title="id=keep"', result)

    def test_missing_landmarks_fail_explicitly(self):
        for source in ('<body></body>', '<main></main>'):
            with self.subTest(source=source), self.assertRaises(ValueError):
                ensure_navigation(source)

    def test_nested_privacy_link_and_existing_copy_preserved(self):
        source = '<body><main></main><nav aria-label="Footer main pages"><a href="../gallery.html">Gallery</a></nav></body>'
        self.assertIn('href="../privacy.html"', self.check_page(source))

    def test_current_public_html_is_unchanged(self):
        for name in public_files():
            if name.endswith('.html'):
                with self.subTest(name=name):
                    text = (ROOT / name).read_text(encoding='utf-8')
                    self.assertEqual(self.check_page(text), text)


if __name__ == '__main__':
    unittest.main()
