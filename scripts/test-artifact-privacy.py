"""Retained exact-artifact privacy fault controls; never delete fixtures."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from privacy_check import inventory
from public_files import ROOT
spec = importlib.util.spec_from_file_location('builder', ROOT / 'scripts/build-public.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
class ArtifactPrivacy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cache = ROOT / '.cache'
        cache.mkdir(exist_ok=True)
        cls.fixture = Path(tempfile.mkdtemp(prefix='privacy-artifact-', dir=cache))
        cls.site = cls.fixture / 'public'
        builder.build(cls.site)
        print('Retained fixture:', cls.fixture)
    def test_exact_artifact(self):
        self.assertEqual(inventory(self.site, ROOT)[1], [])
    def test_artifact_only_tracker_fails_source_still_passes(self):
        path = self.site / 'scripts/cinematic.js'
        original = path.read_bytes()
        try:
            path.write_bytes(original + b'\nfetch("https://undisclosed.example/event"); localStorage.setItem("id", "fixture");')
            errors = '\n'.join(inventory(self.site, ROOT)[1])
            self.assertIn('Undisclosed request host undisclosed.example', errors)
            self.assertIn('browser storage added', errors)
            self.assertEqual(inventory()[1], [])
        finally:
            path.write_bytes(original)
        self.assertEqual(inventory(self.site, ROOT)[1], [])
    def test_missing_artifact_file_fails(self):
        path = self.site / 'privacy.html'
        archived = path.with_suffix('.html.fixture-backup')
        path.rename(archived)
        try:
            self.assertIn('Missing or unsafe public artifact file: privacy.html', inventory(self.site, ROOT)[1])
        finally:
            archived.rename(path)
    def test_missing_directory_cli_fails(self):
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/privacy_check.py'), '--site', str(self.fixture / 'missing')], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Site directory does not exist', result.stderr)
if __name__ == '__main__': unittest.main()
