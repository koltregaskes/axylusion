#!/usr/bin/env python3
"""Download the published Midjourney gallery images to local disk.

Why this exists: all 1,519 gallery images hotlink cdn.midjourney.com, which
now returns 403 to plain requests. The CDN still serves images when the
request carries a browser User-Agent and a midjourney.com Referer (verified
2026-06-10). This script captures the archive locally so the Cloudflare R2
migration (scripts/SETUP-R2.md) can proceed even if that behaviour changes.

- Resumable: already-downloaded files are skipped, safe to re-run.
- Polite: sequential with a small delay; ~25-40 minutes for the full set.
- Output: scripts/downloaded-images/<uuid>_<variant>.<ext>
- Manifest: scripts/downloaded-images/manifest.json maps original URL ->
  local file, for the later URL rewrite in data/gallery.json + gallery.js.

Usage: python scripts/download-gallery-images.py [--limit N]
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GALLERY_JSON = REPO / "data" / "gallery.json"
OUT_DIR = Path(__file__).resolve().parent / "downloaded-images"
MANIFEST = OUT_DIR / "manifest.json"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
REFERER = "https://www.midjourney.com/"
DELAY_SECONDS = 0.6
TIMEOUT = 30
MAX_RETRIES = 3

CDN_RE = re.compile(r"https://cdn\.midjourney\.com/([0-9a-f-]+)/([^\"?\s]+)")


def local_name(uuid: str, tail: str) -> str:
    safe_tail = tail.replace("/", "_")
    return f"{uuid}_{safe_tail}"


def collect_urls() -> list:
    text = GALLERY_JSON.read_text(encoding="utf-8")
    seen = {}
    for match in CDN_RE.finditer(text):
        url = match.group(0)
        if url not in seen:
            seen[url] = (match.group(1), match.group(2))
    return [(url, uuid, tail) for url, (uuid, tail) in seen.items()]


def fetch(url: str, dest: Path) -> str:
    # The CDN fingerprints clients: Python's urllib gets 403 where curl gets
    # 200 with identical headers (verified 2026-06-10). Shell out to curl.
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = subprocess.run(
                [
                    "curl", "-s", "-A", UA, "-e", REFERER,
                    "--max-time", str(TIMEOUT),
                    "-o", str(tmp), "-w", "%{http_code}", url,
                ],
                capture_output=True, text=True, timeout=TIMEOUT + 15,
            )
            code = result.stdout.strip()
            if code == "200" and tmp.exists() and tmp.stat().st_size > 1024:
                tmp.rename(dest)
                return "ok"
            raise ValueError(f"HTTP {code or 'no-response'}")
        except Exception as exc:  # noqa: BLE001 - log-and-retry is the point
            tmp.unlink(missing_ok=True)
            if attempt == MAX_RETRIES:
                return f"failed: {exc}"
            time.sleep(2 * attempt)
    return "failed: retries exhausted"


def main() -> int:
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}
    if MANIFEST.exists():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    urls = collect_urls()
    if limit:
        urls = urls[:limit]
    total = len(urls)
    done = skipped = failed = 0

    print(f"{total} unique cdn.midjourney.com URLs found in {GALLERY_JSON.name}")

    for index, (url, uuid, tail) in enumerate(urls, 1):
        dest = OUT_DIR / local_name(uuid, tail)
        if dest.exists() and dest.stat().st_size > 1024:
            manifest[url] = dest.name
            skipped += 1
            continue
        status = fetch(url, dest)
        if status == "ok":
            manifest[url] = dest.name
            done += 1
        else:
            failed += 1
            print(f"  [{index}/{total}] FAILED {url} -> {status}", flush=True)
        if index % 50 == 0:
            print(f"  [{index}/{total}] ok={done} skipped={skipped} failed={failed}", flush=True)
            MANIFEST.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
        time.sleep(DELAY_SECONDS)

    MANIFEST.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"\nComplete: ok={done} skipped={skipped} failed={failed} of {total}")
    print(f"Manifest: {MANIFEST}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
