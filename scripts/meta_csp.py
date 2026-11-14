"""Meta CSP for the HTML bytes served by legacy GitHub Pages."""
import re
from html import escape
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def policy():
    current=None; values=[]
    for line in (ROOT/'_headers').read_text(encoding='utf-8').splitlines():
        if line.strip() and not line[0].isspace(): current=line.strip()
        match=re.match(r"\s+Content-Security-Policy:\s*(.+)",line,re.I)
        if current=='/*' and match: values.append(match[1])
    if len(values)!=1: raise ValueError('Expected one global CSP in _headers')
    return '; '.join(d.strip() for d in values[0].split(';') if d.strip() and d.strip().split()[0].lower()!='frame-ancestors')

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
    files=pages()
    if not files: raise ValueError('No built HTML pages')
    for page in files:
        parser=MetaCheck(); parser.feed(page.read_text(encoding='utf-8'))
        if parser.policies!=[policy()] or parser.late: raise ValueError(str(page.relative_to(ROOT))+': missing, duplicated, stale or late meta CSP')
    print(f'Meta CSP matches _headers (without frame-ancestors) before scripts on all {len(files)} built HTML pages.')

if __name__=='__main__': check()
