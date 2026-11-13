"""Bounded external href/src crawl. Fails on errors and HTTPS downgrade."""
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
ROOT=Path(__file__).resolve().parent.parent
urls=set()
class Links(HTMLParser):
    def handle_starttag(self, tag, attrs):
        for key,value in attrs:
            if key in ('href','src') and value and value.startswith('https://') and urlsplit(value).hostname!='axylusion.com': urls.add(value.split('#')[0])
for p in ROOT.rglob('*.html'):
    if not any(x.startswith('.') or x=='node_modules' for x in p.relative_to(ROOT).parts): Links().feed(p.read_text(encoding='utf-8'))
def check(url):
    try:
        with urlopen(Request(url,headers={'User-Agent':'AxyLusion-LinkCheck/1.0'}), timeout=12) as response:
            if urlsplit(response.url).scheme!='https': return url,'HTTPS downgrade'
            return url,None
    except Exception as e: return url,type(e).__name__
assert urls,'No external links discovered'
failed=[]
with ThreadPoolExecutor(max_workers=12) as pool:
    for url,error in pool.map(check,sorted(urls)):
        if error: failed.append((url,error))
print(f'External crawl: {len(urls)} URLs; {len(failed)} failed or blocked destinations')
for url,error in failed: print(f'{error}: {url}')
raise SystemExit(bool(failed))