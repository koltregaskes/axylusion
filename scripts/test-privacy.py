"""Offline positive/negative controls for request disclosure and public bytes."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from privacy_check import inventory
from public_files import ROOT, public_files

spec = importlib.util.spec_from_file_location('build_public', ROOT / 'scripts/build-public.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class PrivacyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'source'
        # Copy only named, inspected public inputs. Never traverse private files.
        for name in [*public_files(), 'data/public-files.json', 'data/privacy-inventory.json', 'news-digests/index.json']:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def append(self, name, text):
        path = self.root / name
        path.write_text(path.read_text(encoding='utf-8') + text, encoding='utf-8', newline='\n')

    def test_current_tree(self):
        hosts, errors = inventory(self.root)
        self.assertEqual(errors, [])
        self.assertEqual(set(hosts), {'fonts.googleapis.com', 'fonts.gstatic.com', 'pub-7bea5d72ad544bb685e1335d2e6bdd10.r2.dev'})

    def test_generated_notice_is_current(self):
        spec = importlib.util.spec_from_file_location('cinematic_privacy', ROOT / 'scripts/render-cinematic-site.py')
        renderer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(renderer)
        expected = renderer.ensure_navigation(renderer.clean_page(renderer.render_privacy()))
        self.assertEqual((ROOT / 'privacy.html').read_text(encoding='utf-8'), expected)

    def test_new_html_resource_is_rejected(self):
        for fragment in ('<img src="https://new.example/image.png">',
                         '<source srcset="//new.example/image.png 2x">',
                         '<link rel="preconnect" href="https://new.example">',
                         '<div style="background: url(https://new.example/a.png)"></div>'):
            with self.subTest(fragment=fragment):
                original = (self.root / 'privacy.html').read_text(encoding='utf-8')
                self.append('privacy.html', fragment)
                self.assertTrue(any('new.example' in error for error in inventory(self.root)[1]))
                (self.root / 'privacy.html').write_text(original, encoding='utf-8')

    def test_new_page_is_not_silently_ignored(self):
        (self.root / 'new.html').write_text('<img src="https://new.example/a.png">', encoding='utf-8')
        self.assertIn('Built HTML route missing from public allowlist: new.html', inventory(self.root)[1])

    def test_every_current_newsletter_route_is_allowlisted(self):
        names = public_files(self.root)
        self.assertIn('newsletter.html', names)
        self.assertIn('editions.html', names)
        editions = {p.relative_to(self.root).as_posix() for p in (self.root / 'editions').glob('*.html')}
        self.assertGreater(len(editions), 0)
        self.assertTrue(editions.issubset(names))
        self.assertFalse(any(name.startswith('newsletter/') or name == 'data/newsletter-editions.json' for name in names))

    def test_future_generated_edition_is_included_checked_and_copied(self):
        name = 'editions/2099-01-02.html'  # Synthetic future file, never a real news item.
        source = self.root / name
        source.write_bytes((self.root / 'editions/2026-11-15.html').read_bytes())
        self.assertIn(name, public_files(self.root))
        self.assertEqual(inventory(self.root)[1], [])
        destination = Path(self.temp.name) / 'future-public'
        self.assertIn(name, builder.build(destination, self.root))
        self.assertEqual(source.read_bytes(), (destination / name).read_bytes())
        self.append(name, '<img src="https://new.example/future.png">')
        self.assertTrue(any('new.example' in error for error in inventory(self.root)[1]))

    def test_unapproved_nested_edition_page_is_rejected(self):
        name = 'editions/draft.html'
        (self.root / name).write_text('<p>Fixture draft</p>', encoding='utf-8')
        self.assertNotIn(name, public_files(self.root))
        self.assertIn('Built HTML route missing from public allowlist: ' + name, inventory(self.root)[1])

    def test_invalid_edition_date_and_broadened_pattern_are_rejected(self):
        (self.root / 'editions/2099-02-30.html').write_text('<p>Invalid fixture date</p>', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Invalid public edition date'):
            public_files(self.root)
        path = self.root / 'data/public-files.json'
        config = json.loads(path.read_text(encoding='utf-8'))
        config['edition_pattern'] = '**/*.html'
        path.write_text(json.dumps(config), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Only dated public editions'):
            public_files(self.root)

    def test_css_import_and_url_are_rejected(self):
        self.append('cinematic.css', '\n@import "https://styles.example/a.css";\na {background:url(//images.example/a.png)}')
        errors = '\n'.join(inventory(self.root)[1])
        self.assertIn('styles.example', errors)
        self.assertIn('images.example', errors)

    def test_js_request_and_literal_are_rejected(self):
        self.append('scripts/cinematic.js', '\nfetch("https://collector.example/event"); const endpoint = "//cdn.example/app.js";')
        errors = '\n'.join(inventory(self.root)[1])
        self.assertIn('collector.example', errors)
        self.assertIn('cdn.example', errors)

    def test_new_runtime_json_media_is_rejected(self):
        path = self.root / 'news-digests/news-feed-latest.json'
        path.write_text('{"articles": [{"image": "https://media.example/a.png"}]}', encoding='utf-8')
        self.assertTrue(any('media.example' in error for error in inventory(self.root)[1]))

    def test_new_storage_is_rejected(self):
        self.append('scripts/cinematic.js', '\nlocalStorage.setItem("choice", "yes");')
        self.assertTrue(any('browser storage added' in error for error in inventory(self.root)[1]))

    def test_outbound_link_and_json_ld_are_not_trackers(self):
        self.append('privacy.html', '<a href="https://link.example">Link</a><script type="application/ld+json">{"url":"https://schema.example"}</script>')
        self.assertEqual(inventory(self.root)[1], [])

    def test_notice_must_disclose_host_and_policy(self):
        path = self.root / 'privacy.html'
        path.write_text(path.read_text(encoding='utf-8').replace('<code>fonts.gstatic.com</code>', '').replace('href="https://policies.google.com/privacy"', ''), encoding='utf-8')
        errors = '\n'.join(inventory(self.root)[1])
        self.assertIn('does not name provider host: fonts.gstatic.com', errors)
        self.assertIn('Missing provider privacy policy: Google Fonts', errors)

    def test_artifact_matches_bytes_and_excludes_source(self):
        draft = self.root / 'content/blog/draft.md'
        draft.parent.mkdir(parents=True)
        draft.write_text('publish: false\nDraft must remain outside the artifact.', encoding='utf-8')
        destination = Path(self.temp.name) / 'public'
        names = builder.build(destination, self.root)
        self.assertNotIn('content/blog/draft.md', names)
        self.assertFalse((destination / 'content').exists())
        for name in names:
            self.assertEqual((self.root / name).read_bytes(), (destination / name).read_bytes())
        with self.assertRaisesRegex(ValueError, 'Output already exists'):
            builder.build(destination, self.root)

    def test_link_to_excluded_source_is_rejected(self):
        self.append('privacy.html', '<a href="content/blog/draft.md">Draft</a>')
        self.assertTrue(any('outside public artifact' in error for error in inventory(self.root)[1]))

    def test_traversal_in_digest_manifest_is_rejected(self):
        path = self.root / 'news-digests/index.json'
        path.write_text(json.dumps({'files': ['../content/blog/draft.md']}), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Invalid public digest filename'):
            public_files(self.root)

    def test_authoring_source_cannot_be_allowlisted(self):
        path = self.root / 'data/public-files.json'
        config = json.loads(path.read_text(encoding='utf-8'))
        config['files'].append('content/blog/draft.md')
        path.write_text(json.dumps(config), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Authoring source cannot be published'):
            public_files(self.root)

    def test_backend_contract_cannot_be_allowlisted(self):
        path = self.root / 'data/public-files.json'
        config = json.loads(path.read_text(encoding='utf-8'))
        config['files'].append('newsletter/contract.mjs')
        path.write_text(json.dumps(config), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Authoring source cannot be published'):
            public_files(self.root)


if __name__ == '__main__':
    unittest.main()
