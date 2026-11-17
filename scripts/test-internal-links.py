"""Artifact-only link failures must not be hidden by source-tree files."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('links', Path(__file__).with_name('check-internal-links.py'))
links = importlib.util.module_from_spec(spec)
spec.loader.exec_module(links)

class ArtifactLinks(unittest.TestCase):
    def test_artifact_isolation_and_fragments(self):
        # Retain fixtures; never delete files during launch preparation.
        root = Path(tempfile.mkdtemp(prefix='axy-links-'))
        source, artifact = root / 'source', root / 'artifact'
        source.mkdir()
        artifact.mkdir()
        html = '<a href="draft.html#target">Draft</a><a href="/#home">Home</a><main id="home"></main>'
        for directory in (source, artifact):
            (directory / 'index.html').write_text(html, encoding='utf-8')
        (source / 'draft.html').write_text('<main id="target"></main>', encoding='utf-8')
        self.assertEqual(links.check(source), (2, []))
        self.assertEqual(links.check(artifact)[1], ['index.html: missing draft.html#target'])
        (artifact / 'draft.html').write_text('<main></main>', encoding='utf-8')
        self.assertEqual(links.check(artifact)[1], ['index.html: missing fragment draft.html#target'])
        (artifact / 'draft.html').write_text('<main id="target"></main>', encoding='utf-8')
        self.assertEqual(links.check(artifact), (2, []))
        with self.assertRaises(ValueError):
            links.check(root / 'missing')
        (artifact / 'index.html').write_text('<a href="../source/draft.html">Escape</a>', encoding='utf-8')
        self.assertEqual(links.check(artifact)[1], ['index.html: missing ../source/draft.html'])
        print(f'Retained fixtures: {root}')

if __name__ == '__main__':
    unittest.main()
