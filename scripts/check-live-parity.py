"""Compare public deployed bytes with a frozen Git commit. No provider mutations."""
import argparse
import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
ROOT = Path(__file__).resolve().parent.parent
BASE = "https://axylusion.com"
EXTRA = {"sitemap.xml", "feed.xml", "robots.txt", "llms.txt", "styles.css", "cinematic.css", "cross-site-nav.js", "scripts/cinematic.js", "favicon.svg", "site.webmanifest", "images/social-default.png", "data/gallery.json", "data/homepage-gallery.json"}
HEADERS = ("Server", "Content-Security-Policy", "Strict-Transport-Security", "X-Frame-Options", "X-Content-Type-Options", "Referrer-Policy")

def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)

class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, url):
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname not in {"axylusion.com", "www.axylusion.com"} or parsed.username or parsed.password:
            raise ValueError("Unsafe live-site redirect")
        return super().redirect_request(request, response, code, message, headers, url)

def public_paths(sha):
    tracked = git("ls-tree", "-r", "--name-only", sha).decode("utf-8").splitlines()
    return sorted(name for name in tracked if name in EXTRA or (name.endswith(".html") and ("/" not in name or name.startswith("a-list/") and name.count("/") == 1)))

def compare(sha, path):
    expected = git("show", f"{sha}:{path}")
    route = "/" if path == "index.html" else "/" + path
    url = BASE + route + "?launch-check=" + sha[:12]
    result = {"path": path, "url": BASE + route}
    try:
        request = Request(url, headers={"User-Agent": "AxyLusion-LaunchParity/1.0", "Cache-Control": "no-cache"})
        with build_opener(SafeRedirect()).open(request, timeout=15) as response:
            actual = response.read(8 * 1024 * 1024 + 1)
            result.update(status=response.status, expected_sha256=hashlib.sha256(expected).hexdigest(), live_sha256=hashlib.sha256(actual).hexdigest())
            final = urlsplit(response.url)
            result["match"] = response.status == 200 and len(actual) <= 8 * 1024 * 1024 and final.scheme == "https" and final.hostname == "axylusion.com" and actual == expected
            if path == "index.html": result["headers"] = {name: response.headers.get(name) for name in HEADERS}
    except Exception as error:
        result.update(match=False, error=type(error).__name__, status=getattr(error, "code", None))
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="origin/main")
    args = parser.parse_args()
    sha = git("rev-parse", "--verify", "--end-of-options", args.ref + "^{commit}").decode().strip()
    paths = public_paths(sha)
    if not paths: raise SystemExit("No public routes discovered")
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda path: compare(sha, path), paths))
    print(json.dumps({"source_sha": sha, "files": len(results), "matched": sum(row["match"] for row in results), "results": results}, indent=2))
    return int(any(not row["match"] for row in results))

if __name__ == "__main__":
    raise SystemExit(main())
