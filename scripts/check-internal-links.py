"""Check every static HTML internal href/src, including fragment targets."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
ROOT = Path(__file__).resolve().parent.parent
class Links(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.refs=[]; self.ids=set(); self.feed(text)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if a.get('id'): self.ids.add(a['id'])
        for key in ('href','src'):
            if a.get(key): self.refs.append(a[key])
pages={p:Links(p.read_text(encoding='utf-8')) for p in ROOT.rglob('*.html') if not any(x.startswith('.') or x=='node_modules' for x in p.relative_to(ROOT).parts)}
errors=[]
for page, parsed in pages.items():
    for ref in parsed.refs:
        u=urlsplit(ref)
        if u.scheme and (u.scheme!='https' or u.netloc!='axylusion.com'): continue
        if u.netloc and u.netloc!='axylusion.com': continue
        target=(ROOT / unquote(u.path).lstrip('/') if u.path.startswith('/') else page.parent / unquote(u.path)).resolve() if u.path else page
        if target.is_dir(): target=target/'index.html'
        if not target.is_relative_to(ROOT) or not target.exists(): errors.append(f'{page.relative_to(ROOT)}: missing {ref}')
        elif u.fragment and target in pages and unquote(u.fragment) not in pages[target].ids: errors.append(f'{page.relative_to(ROOT)}: missing fragment {ref}')
if errors: raise SystemExit('\n'.join(errors))
assert pages, 'No HTML routes found'
print(f'Internal links passed: {len(pages)} HTML routes')