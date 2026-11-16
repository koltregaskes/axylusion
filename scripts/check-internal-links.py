"""Check static HTML internal href/src targets, optionally in a built artifact."""
import argparse
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parent.parent

class Links(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.refs, self.ids = [], set()
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        for key in ('href', 'src'):
            if attrs.get(key):
                self.refs.append(attrs[key])


def check(root):
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError(f'Site directory does not exist: {root}')
    pages = {p: Links(p.read_text(encoding='utf-8')) for p in root.rglob('*.html')
             if not any(x.startswith('.') or x == 'node_modules' for x in p.relative_to(root).parts)}
    errors = []
    for page, parsed in pages.items():
        for ref in parsed.refs:
            url = urlsplit(ref)
            if url.scheme and (url.scheme != 'https' or url.netloc != 'axylusion.com'):
                continue
            if url.netloc and url.netloc != 'axylusion.com':
                continue
            target = ((root / unquote(url.path).lstrip('/') if url.path.startswith('/')
                       else page.parent / unquote(url.path)).resolve() if url.path else page)
            if target.is_dir():
                target = target / 'index.html'
            if not target.is_relative_to(root) or not target.is_file():
                errors.append(f'{page.relative_to(root)}: missing {ref}')
            elif url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:
                errors.append(f'{page.relative_to(root)}: missing fragment {ref}')
    if not pages:
        errors.append('No HTML routes found')
    return len(pages), errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path, default=ROOT, help='Source or exact built artifact directory')
    args = parser.parse_args()
    try:
        count, errors = check(args.site)
    except ValueError as error:
        parser.error(str(error))
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'Internal links passed: {count} HTML routes in {args.site.resolve()}')


if __name__ == '__main__':
    main()
