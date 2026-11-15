"""Offline regression checks for withdrawal, hub #615 and #1508."""
import contextlib
import importlib.util
import io
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

from alist_status import ROOT, ROUTES, holding_page, publication_issues


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WithdrawalTests(unittest.TestCase):
    def test_published_tree(self):
        self.assertEqual(publication_issues(), [])

    def test_all_old_routes_are_data_free(self):
        for route in ROUTES:
            with self.subTest(route=route):
                text = (ROOT / route).read_text(encoding='utf-8')
                self.assertEqual(text, holding_page(route))
                self.assertIn('noindex, follow', text)
                for forbidden in ('application/ld+json', 'Elo', 'meta_score', 'raw_score', 'Artificial Analysis'):
                    self.assertNotIn(forbidden, text)

    def test_acquisition_does_not_read_or_fetch_or_write(self):
        for name in ('refresh-a-list-benchmarks', 'sync-a-list-benchmarks'):
            module = load(name)
            for args in ([], ['--check']):
                with self.subTest(script=name, args=args), patch.object(sys, 'argv', [name, *args]), \
                     patch('urllib.request.urlopen', side_effect=AssertionError('Network attempted')), \
                     patch.object(Path, 'read_text', side_effect=AssertionError('Data read attempted')), \
                     patch.object(Path, 'write_text', side_effect=AssertionError('Data write attempted')), \
                     contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(module.main(), 0)
                    self.assertIn('SKIP:', output.getvalue())

    def test_imported_fetch_is_disabled(self):
        module = load('refresh-a-list-benchmarks')
        with patch('urllib.request.urlopen', side_effect=AssertionError('Network attempted')):
            with self.assertRaisesRegex(RuntimeError, 'disabled'):
                module.fetch_text('https://example.invalid', 'text/html')

    def test_cinematic_renderer_ignores_snapshot(self):
        module = load('render-cinematic-site')
        self.assertEqual(module.render_alist({'categories': [{'models': [{'meta_score': 999}]}]}), holding_page('a-list.html'))
        source = (ROOT / 'scripts/render-cinematic-site.py').read_text(encoding='utf-8')
        self.assertNotIn('read_json(ROOT / "data" / "a-list-benchmarks.json")', source)

    def test_scheduled_pipeline_never_invokes_acquisition(self):
        source = (ROOT / 'scripts/refresh-site-data.ps1').read_text(encoding='utf-8')
        for name in ('refresh-a-list-benchmarks.py', 'sync-a-list-benchmarks.py', 'render-a-list.py'):
            self.assertNotIn('python scripts/' + name, source)

    def test_absent_data_is_enforced(self):
        original = Path.exists
        def exists(path):
            return True if path == ROOT / 'data/a-list-benchmarks.json' else original(path)
        with patch.object(Path, 'exists', exists):
            self.assertTrue(any('data must stay absent' in issue for issue in publication_issues()))

    def test_privacy_is_linked_from_every_static_footer(self):
        pages = [*ROOT.glob('*.html'), *(ROOT / 'a-list').glob('*.html')]
        for page in pages:
            with self.subTest(page=page.relative_to(ROOT)):
                footers = re.findall(r'<footer\b[^>]*>.*?</footer>', page.read_text(encoding='utf-8'), re.S | re.I)
                self.assertTrue(footers, 'Missing footer')
                for footer in footers:
                    links = re.findall(r'href=["\']([^"\']*privacy\.html)["\']', footer)
                    self.assertTrue(links, 'Missing Privacy link')
                    for link in links:
                        self.assertEqual((ROOT / link.lstrip('/') if link.startswith('/') else page.parent / link).resolve(), ROOT / 'privacy.html')

    def test_privacy_notice_does_not_advertise_withdrawn_rankings(self):
        text = (ROOT / 'privacy.html').read_text(encoding='utf-8')
        self.assertNotRegex(text, r'(?i)a-list|artificial\s*analysis|artificialanalysis|arena Elo|tool rankings')
        self.assertIn('No analytics or newsletter yet', text)


if __name__ == '__main__':
    unittest.main()
