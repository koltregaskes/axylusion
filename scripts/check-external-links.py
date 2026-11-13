"""Bounded external crawl. Only confirmed HTTP 404/410 fail the link gate."""
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.error import HTTPError
ROOT = Path(__file__).resolve().parent.parent

def classify(status=None, error=None, final_url=None):
    if status in (404, 410):
        return "broken", f"HTTP {status}"
    if error or status is None or not 200 <= status < 300:
        return "unverified", error or f"HTTP {status}"
    if final_url and urlsplit(final_url).scheme != "https":
        return "unverified", "Insecure destination or HTTPS downgrade"
    return "verified", f"HTTP {status}"

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = set()
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "link" and attrs.get("rel") in ("preconnect", "dns-prefetch"):
            return
        for key in ("href", "src"):
            value = attrs.get(key, "")
            if urlsplit(value).scheme in ("https", "http") and urlsplit(value).hostname != "axylusion.com":
                self.urls.add(value.split("#")[0])

def check(url):
    try:
        with urlopen(Request(url, headers={"User-Agent": "AxyLusion-LinkCheck/1.0"}), timeout=12) as response:
            return url, *classify(response.status, final_url=response.url)
    except HTTPError as error:
        return url, *classify(error.code)
    except Exception as error:
        return url, *classify(error=type(error).__name__)

def main():
    parser = Links()
    for page in ROOT.rglob("*.html"):
        if not any(part.startswith(".") or part == "node_modules" for part in page.relative_to(ROOT).parts):
            parser.feed(page.read_text(encoding="utf-8"))
    if not parser.urls:
        raise SystemExit("No external URLs discovered")
    counts = dict.fromkeys(("broken", "unverified", "verified"), 0)
    with ThreadPoolExecutor(max_workers=12) as pool:
        for url, state, detail in pool.map(check, sorted(parser.urls)):
            counts[state] += 1
            if state != "verified":
                print(f"::warning::{state.upper()}: {url} ({detail})")
    print(f"External crawl: {len(parser.urls)} URLs; {counts}. Only confirmed 404/410 fail. Unverified is not healthy.")
    return int(counts["broken"] > 0)

if __name__ == "__main__":
    raise SystemExit(main())
