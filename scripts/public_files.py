"""Explicit public artifact boundary. Source paths are never copied recursively."""
import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parent.parent


def public_files(root=ROOT):
    config = json.loads((root / 'data/public-files.json').read_text(encoding='utf-8'))
    names = list(config['files'])
    # Only the named digest manifest extends the fixed allowlist, never content/.
    if config['digest_manifest'] != 'news-digests/index.json':
        raise ValueError('Only the public digest index can extend the allowlist')
    manifest = json.loads((root / config['digest_manifest']).read_text(encoding='utf-8'))
    for name in manifest['files']:
        if not re.fullmatch(r'(?:\d{4}-\d{2}-\d{2}-digest|digest-\d{4}-\d{2}-\d{2})\.md', name):
            raise ValueError('Invalid public digest filename')
        names.append('news-digests/' + name)
    if not names or len(names) != len(set(names)):
        raise ValueError('Empty or duplicate public allowlist')
    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
            raise ValueError('Unsafe public path: ' + name)
        if any(part.startswith('.') for part in path.parts) and name not in ('.nojekyll', '.well-known/security.txt'):
            raise ValueError('Hidden source cannot be published: ' + name)
        if name.startswith(('content/', 'docs/', 'tests/', 'design/')) or path.suffix in ('.py', '.ps1', '.yml', '.yaml'):
            raise ValueError('Authoring source cannot be published: ' + name)
        source = root / name
        if any(p.is_symlink() for p in [source, *source.parents]) or not source.is_file():
            raise ValueError('Missing file or symlink in public allowlist: ' + name)
        if not source.resolve().is_relative_to(root.resolve()):
            raise ValueError('Public file escapes source tree: ' + name)
    return sorted(names)
