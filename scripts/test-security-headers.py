"""Offline admission controls for the launch header consistency gate."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import meta_csp


class SecurityHeaderTests(unittest.TestCase):
    def setUp(self):
        # Keep synthetic fixtures in the ignored local cache for inspection.
        cache = meta_csp.ROOT / '.cache'
        cache.mkdir(exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix='security-headers-', dir=cache))
        self.payload = json.loads((meta_csp.ROOT / 'cloudflare-response-headers.json').read_text(encoding='utf-8'))
        self.patch = patch.object(meta_csp, 'ROOT', self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.save_payload()
        (self.root / '_headers').write_text(meta_csp.headers_mirror(), encoding='utf-8')
        (self.root / 'index.html').write_text(meta_csp.apply('<html><head><meta charset="utf-8"></head><body></body></html>'), encoding='utf-8')

    def save_payload(self):
        text = json.dumps(self.payload)
        (self.root / 'cloudflare-response-headers.json').write_text(text, encoding='utf-8')
        (self.root / 'docs').mkdir(exist_ok=True)
        (self.root / 'docs/HOSTING-SECURITY.md').write_text('```json\n' + text + '\n```\n', encoding='utf-8')

    def run_check(self):
        with contextlib.redirect_stdout(io.StringIO()):
            meta_csp.check()

    def test_consistent_tree_passes(self):
        self.run_check()

    def test_stale_mirror_fails(self):
        path = self.root / '_headers'
        path.write_text(path.read_text(encoding='utf-8').replace('nosniff', 'different'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, '_headers is stale'):
            self.run_check()

    def test_stale_documentation_fails(self):
        path = self.root / 'docs/HOSTING-SECURITY.md'
        path.write_text(path.read_text(encoding='utf-8').replace('nosniff', 'different'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'example is stale'):
            self.run_check()

    def test_intended_csp_change_requires_page_regeneration(self):
        entry = self.payload['rules'][0]['action_parameters']['headers']['Content-Security-Policy']
        entry['value'] = entry['value'].replace("connect-src 'self'", "connect-src 'none'")
        self.save_payload()
        (self.root / '_headers').write_text(meta_csp.headers_mirror(), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'index.html:'):
            self.run_check()

    def test_each_nested_page_is_checked(self):
        (self.root / 'nested').mkdir()
        (self.root / 'nested/page.html').write_text('<meta charset="utf-8">', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'page.html:'):
            self.run_check()

    def test_missing_duplicate_and_late_meta_fail(self):
        page = self.root / 'index.html'
        tag = meta_csp.apply('<meta charset="utf-8">').split('\n', 1)[1]
        for text in ('<meta charset="utf-8">', tag + tag, '<script src="app.js"></script>' + tag):
            with self.subTest(text=text):
                page.write_text(text, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'index.html:'):
                    self.run_check()

    def test_hsts_preload_and_subdomains_are_rejected(self):
        entry = self.payload['rules'][0]['action_parameters']['headers']['Strict-Transport-Security']
        for suffix in ('; preload', '; includeSubDomains'):
            with self.subTest(suffix=suffix):
                entry['value'] = 'max-age=31536000' + suffix
                self.save_payload()
                with self.assertRaisesRegex(ValueError, 'HSTS must omit'):
                    meta_csp.intended_headers()

    def test_report_only_is_not_enforcement(self):
        headers = self.payload['rules'][0]['action_parameters']['headers']
        headers['Content-Security-Policy-Report-Only'] = headers.pop('Content-Security-Policy')
        self.save_payload()
        with self.assertRaisesRegex(ValueError, 'six intended security headers'):
            meta_csp.intended_headers()

    def test_framing_headers_agree(self):
        headers = self.payload['rules'][0]['action_parameters']['headers']
        for name, value in (('X-Frame-Options', 'SAMEORIGIN'),
                            ('Content-Security-Policy', "default-src 'self'; script-src 'self'; frame-ancestors 'self'")):
            with self.subTest(name=name):
                original = headers[name]['value']
                headers[name]['value'] = value
                self.save_payload()
                with self.assertRaisesRegex(ValueError, 'frame-ancestors'):
                    meta_csp.intended_headers()
                headers[name]['value'] = original

    def test_meta_omits_only_frame_ancestors(self):
        header = meta_csp.intended_headers()['Content-Security-Policy']
        self.assertEqual(meta_csp.policy(), header.replace("; frame-ancestors 'none'", ''))


if __name__ == '__main__':
    unittest.main()
