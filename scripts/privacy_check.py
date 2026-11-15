"""Offline request inventory for the allowlisted static artifact, not a JS interpreter.

HTML navigation/JSON-LD/CSP URLs are not requests. CSS URLs, resource attributes,
executable JS URL literals and JSON-fed media are checked. New dynamic request
construction still needs browser review before deployment.
"""
from collections import defaultdict
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from public_files import ROOT, public_files

URL = re.compile(r'(?:https?://|(?<=["\'`])//)[A-Za-z0-9][^\s<>"\'`\\)}]*')
CSS_URL = re.compile(r'''url\(\s*(?:"([^"]*)"|'([^']*)'|([^\s)]+))\s*\)|@import\s+["']([^"']+)''', re.I)
STORAGE = re.compile(r'\b(?:localStorage|sessionStorage|indexedDB)\b|document\s*(?:\.\s*cookie|\[\s*["\']cookie["\']\s*\])|\bcookieStore\b|serviceWorker', re.I)


def inventory(root=ROOT):
    config = json.loads((root / 'data/privacy-inventory.json').read_text(encoding='utf-8'))
    allowed = {host for provider in config['providers'] for host in provider['hosts']}
    names = public_files(root)
    name_set = set(names)
    evidence, errors = defaultdict(list), []
    for page in [*root.glob('*.html'), *(root / 'a-list').glob('*.html')]:
        name = page.relative_to(root).as_posix()
        if name not in name_set:
            errors.append('Built HTML route missing from public allowlist: ' + name)

    def reference(value, page, line, kind, navigation=False, document_relative=False):
        value = unescape(value.strip())
        parsed = urlsplit(value)
        if parsed.hostname and parsed.hostname != 'axylusion.com':
            if not navigation:
                evidence[parsed.hostname].append(f'{page}:{line} ({kind})')
            return
        if parsed.scheme in ('data', 'blob', 'mailto', 'tel', 'javascript') or value.startswith('#'):
            return
        relative = unquote(parsed.path)
        target = (root / relative.lstrip('/') if relative.startswith('/') or document_relative else root / Path(page).parent / relative).resolve()
        if target.is_dir():
            target /= 'index.html'
        if not target.is_relative_to(root.resolve()) or target.relative_to(root.resolve()).as_posix() not in name_set:
            errors.append(f'{page}:{line}: reference outside public artifact: {value}')

    def css(text, page, line=1):
        for match in CSS_URL.finditer(text):
            reference(next(group for group in match.groups() if group is not None), page,
                      line + text.count('\n', 0, match.start()), 'CSS resource')

    def js(text, page, line=1):
        # Conservative URL-literal check, including template strings and import URLs.
        # The existing navigation module has five reviewed link-only destinations.
        for match in URL.finditer(text):
            host = urlsplit(match[0]).hostname
            nav = page == 'cross-site-nav.js' and host in config['link_only_js_hosts']
            reference(match[0], page, line + text.count('\n', 0, match.start()), 'JS URL', navigation=nav)
        for match in re.finditer(r'\b(fetch|import|sendBeacon|WebSocket|EventSource)\s*\(\s*["\'`]([^"\'`$]+)["\'`]', text):
            reference(match[2], page, line + text.count('\n', 0, match.start()), 'JS request',
                      document_relative=match[1] != 'import')
        if STORAGE.search(text):
            errors.append(f'{page}: browser storage added; update the notice and review its purpose/consent')

    class Page(HTMLParser):
        def __init__(self, name):
            super().__init__()
            self.name, self.script, self.style = name, False, False

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            line = self.getpos()[0]
            if tag in ('form', 'iframe', 'audio', 'video'):
                errors.append(f'{self.name}:{line}: new form or embed requires privacy review')
            for key in ('src', 'poster', 'data') if tag == 'object' else ('src', 'poster'):
                if attrs.get(key):
                    reference(attrs[key], self.name, line, tag + '.' + key)
            for key in ('srcset', 'imagesrcset'):
                for part in attrs.get(key, '').split(','):
                    if part.strip():
                        reference(part.strip().split()[0], self.name, line, tag + '.' + key)
            if tag == 'link' and set(attrs.get('rel', '').split()) & {'stylesheet', 'preconnect', 'dns-prefetch', 'preload', 'modulepreload', 'prefetch', 'icon', 'manifest'}:
                reference(attrs.get('href', ''), self.name, line, 'link.' + attrs.get('rel', ''))
            if tag in ('a', 'area') and attrs.get('href'):
                reference(attrs['href'], self.name, line, 'navigation', navigation=True)
            for value in attrs.get('ping', '').split():
                reference(value, self.name, line, 'link ping')
            css(attrs.get('style', ''), self.name, line)
            for key, value in attrs.items():
                if key.startswith('on'):
                    js(value or '', self.name, line)
            if tag == 'script':
                self.script = attrs.get('type', '').lower() not in ('application/ld+json', 'application/json')
            if tag == 'style':
                self.style = True

        def handle_endtag(self, tag):
            if tag == 'script': self.script = False
            if tag == 'style': self.style = False

        def handle_data(self, data):
            if self.script: js(data, self.name, self.getpos()[0])
            if self.style: css(data, self.name, self.getpos()[0])

    for name in names:
        path = root / name
        if path.suffix not in ('.html', '.css', '.js', '.webmanifest'):
            continue
        text = path.read_text(encoding='utf-8')
        if path.suffix == '.html': Page(name).feed(text)
        elif path.suffix == '.css': css(text, name)
        elif path.suffix == '.js': js(text, name)
        else:
            for icon in json.loads(text).get('icons', []):
                reference(icon['src'], name, 1, 'manifest icon')
    # News URLs are outbound links. Media fields added to a runtime JSON payload
    # must be disclosed even before a renderer starts consuming them.
    def media_fields(value, name):
        if isinstance(value, dict):
            for key, child in value.items():
                if key in ('src', 'cdn_url', 'image', 'poster', 'thumbnail') and isinstance(child, str):
                    reference(child, name, 1, 'JSON media')
                else:
                    media_fields(child, name)
        elif isinstance(value, list):
            for child in value: media_fields(child, name)
    for name in names:
        if name.endswith('.json'):
            media_fields(json.loads((root / name).read_text(encoding='utf-8')), name)
    for host, refs in sorted(evidence.items()):
        if host not in allowed:
            errors.append('Undisclosed request host ' + host + ': ' + refs[0])
    notice = (root / 'privacy.html').read_text(encoding='utf-8')
    for provider in config['providers']:
        for host in provider['hosts']:
            if '<code>' + host + '</code>' not in notice:
                errors.append('Privacy page does not name provider host: ' + host)
        if f'href="{provider["policy"]}"' not in notice:
            errors.append('Missing provider privacy policy: ' + provider['name'])
    return evidence, errors


if __name__ == '__main__':
    evidence, errors = inventory()
    for host, refs in sorted(evidence.items()):
        print(f'{host}: {len(refs)} references; {refs[0]}')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'Privacy inventory passed: {len(evidence)} third-party resource hosts; no site-script storage.')
