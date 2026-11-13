"""Bounded external href/src crawl. Fails on errors and HTTPS downgrade."""
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError
ROOT=Path(__file__).resolve().parent.parent
urls=set()
class Links(HTMLParser):
    def handle_starttag(self, tag, attrs):
        if tag=='link' and dict(attrs).get('rel') in ('preconnect','dns-prefetch'): return
        for key,value in attrs:
            if key in ('href','src') and value and value.startswith('https://') and urlsplit(value).hostname!='axylusion.com': urls.add(value.split('#')[0])
for p in ROOT.rglob('*.html'):
    if not any(x.startswith('.') or x=='node_modules' for x in p.relative_to(ROOT).parts): Links().feed(p.read_text(encoding='utf-8'))
def check(url):
    try:
        with urlopen(Request(url,headers={'User-Agent':'AxyLusion-LinkCheck/1.0'}), timeout=12) as response:
            if urlsplit(response.url).scheme!='https': return url,'HTTPS downgrade'
            return url,None
    except HTTPError as e: return url,('UNVERIFIED_HTTP_' if e.code in (401,403,429) else 'HTTP_')+str(e.code)
    except Exception as e: return url,type(e).__name__
assert urls,'No external links discovered'
failed=[]; unverified=[]
with ThreadPoolExecutor(max_workers=12) as pool:
    for url,error in pool.map(check,sorted(urls)):
        if error and error.startswith('UNVERIFIED_'): unverified.append((url,error))
        elif error: failed.append((url,error))
for url,error in unverified: print(f'::warning::Blocked destination remains unverified: {url} ({error})')
print(f'Unverified bot/auth/rate-limited responses: {len(unverified)}')
print(f'External crawl: {len(urls)} URLs; {len(failed)} definite failures (blocked destinations counted separately)')
for url,error in failed: print(f'{error}: {url}')
raise SystemExit(bool(failed))