"""Generate/check meta CSP and the unused _headers mirror from the Cloudflare proposal.

No provider settings are changed. Run --write after an intended policy edit.
"""
import argparse
import json
import re
from html import escape
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

MIRROR_NOTICE = (
    '# UNUSED by GitHub Pages: this file does not configure live response headers.\n'
    '# Generated from cloudflare-response-headers.json; do not edit by hand.\n'
    '# Regenerate: python -B scripts/meta_csp.py --write\n'
    '# Proposed Cloudflare change and approval: docs/HOSTING-SECURITY.md\n'
)


def intended_headers():
    payload = json.loads((ROOT / 'cloudflare-response-headers.json').read_text(encoding='utf-8'))
    rules = payload.get('rules', [])
    if len(rules) != 1:
        raise ValueError('Expected one proposed Cloudflare rule')
    rule = rules[0]
    if (rule.get('action') != 'rewrite' or rule.get('enabled') is not True or
        rule.get('expression') != '(http.host eq "axylusion.com" or http.host eq "www.axylusion.com")'):
        raise ValueError('Unexpected Cloudflare action, enabled flag or hostname scope')
    entries = rule.get('action_parameters', {}).get('headers', {})
    required = {'X-Content-Type-Options', 'X-Frame-Options', 'Referrer-Policy',
                'Strict-Transport-Security', 'Permissions-Policy', 'Content-Security-Policy'}
    if set(entries) != required:
        raise ValueError('Expected exactly the six intended security headers (enforced CSP)')
    headers = {}
    for name, entry in entries.items():
        value = entry.get('value')
        if entry.get('operation') != 'set' or not isinstance(value, str) or not value.strip() or '\n' in value or '\r' in value:
            raise ValueError('Invalid set operation or header value: ' + name)
        headers[name] = value
    if headers['Strict-Transport-Security'] != 'max-age=31536000':
        raise ValueError('HSTS must omit includeSubDomains and preload; scope changes need Kol')
    if headers['X-Frame-Options'] != 'DENY':
        raise ValueError('X-Frame-Options must agree with frame-ancestors none')
    directives = {}
    for directive in headers['Content-Security-Policy'].split(';'):
        tokens = directive.strip().split()
        if not tokens:
            continue
        name = tokens[0].lower()
        if name in directives:
            raise ValueError('Duplicate CSP directive: ' + name)
        directives[name] = tokens[1:]
    if directives.get('frame-ancestors') != ["'none'"]:
        raise ValueError('Expected frame-ancestors none in the response CSP')
    if not directives.get('default-src') or not directives.get('script-src'):
        raise ValueError('Missing default-src or script-src')
    return headers


def policy():
    # frame-ancestors is ignored in a meta CSP and must be a response header.
    value = intended_headers()['Content-Security-Policy']
    return '; '.join(d.strip() for d in value.split(';') if d.strip() and d.strip().split()[0].lower() != 'frame-ancestors')


def headers_mirror():
    return MIRROR_NOTICE + '/*\n' + ''.join(f'  {name}: {value}\n' for name, value in intended_headers().items())

def pages():
    excluded={'node_modules','docs','tests','scripts'}
    return sorted(p for p in ROOT.rglob('*.html') if not any(part.startswith('.') or part in excluded for part in p.relative_to(ROOT).parts))

def apply(text):
    text=re.sub(r'\s*<meta\b(?=[^>]*http-equiv=["\']Content-Security-Policy["\'])[^>]*>', '', text,flags=re.I)
    tag='<meta http-equiv="Content-Security-Policy" content="'+escape(policy(),quote=False).replace('"','&quot;')+'">'
    text,count=re.subn(r'<meta\b[^>]*charset[^>]*>',lambda m:m[0]+'\n  '+tag,text,count=1,flags=re.I)
    if count!=1: raise ValueError('Missing charset before CSP insertion')
    return text

class MetaCheck(HTMLParser):
    def __init__(self): super().__init__(); self.policies=[]; self.script_seen=False; self.late=False
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='script': self.script_seen=True
        if tag=='meta' and attrs.get('http-equiv','').lower()=='content-security-policy':
            self.policies.append(attrs.get('content')); self.late|=self.script_seen

def check():
    if (ROOT / '_headers').read_text(encoding='utf-8') != headers_mirror():
        raise ValueError('_headers is stale; run python -B scripts/meta_csp.py --write')
    doc = (ROOT / 'docs/HOSTING-SECURITY.md').read_text(encoding='utf-8')
    examples = re.findall(r'^```json\n(.*?)^```', doc, flags=re.M | re.S)
    payload = json.loads((ROOT / 'cloudflare-response-headers.json').read_text(encoding='utf-8'))
    if len(examples) != 1 or json.loads(examples[0]) != payload:
        raise ValueError('docs/HOSTING-SECURITY.md Cloudflare example is stale')
    files=pages()
    if not files: raise ValueError('No built HTML pages')
    for page in files:
        parser=MetaCheck(); parser.feed(page.read_text(encoding='utf-8'))
        if parser.policies!=[policy()] or parser.late: raise ValueError(str(page.relative_to(ROOT))+': missing, duplicated, stale or late meta CSP')
    print(f'Cloudflare proposal and unused _headers mirror agree; meta CSP matches (without frame-ancestors) before scripts on all {len(files)} built HTML pages. Live headers are not checked.')

if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Regenerate the unused mirror and all HTML meta CSP tags locally')
    args = parser.parse_args()
    if args.write:
        (ROOT / '_headers').write_text(headers_mirror(), encoding='utf-8', newline='\n')
        for page in pages():
            text = page.read_text(encoding='utf-8')
            updated = apply(text)
            if updated != text:
                page.write_text(updated, encoding='utf-8', newline='\n')
    check()
