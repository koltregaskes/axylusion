# Axy Lusion

This repository contains the Axy Lusion creative portfolio site: a static website for AI artwork, music, video, news, blog posts, and creative tool coverage.

## What the Site Includes

- A cinematic homepage with a hero feature and latest-image scroll experience
- A full gallery backed by `data/gallery.json`
- Dedicated pages for music, video, blog, news, tools, and about content
- Archived Decap CMS shell files kept offline in `W:\Websites\LOCAL-ONLY\archive\axylusion-admin-shell\2026-04-21\` pending any future authenticated editorial workflow

## Stack

- Plain HTML, CSS, and JavaScript
- No framework; a small Python build updates search metadata, sitemap and RSS
- Static hosting friendly
- Gallery/media data stored in `data/gallery.json`

**Preview Path:** [koltregaskes.github.io/axylusion](https://koltregaskes.github.io/axylusion)

**Intended Production Domain:** `https://axylusion.com`

## Local Preview

Before committing content changes, run:

```powershell
python scripts/build-seo.py
python scripts/check-seo.py
python scripts/validate-site.py
```

`build-seo.py` discovers public root and A-List HTML, adds per-page social cards
and JSON-LD, and generates `sitemap.xml` and `feed.xml`. RSS includes up to 50
non-empty indexed digests and their deduplicated source stories. Item GUIDs are
stable URLs and publication dates come from the digest, never build time.
`--check` fails CI if tracked output has gone stale. The refresh pipeline runs
the generator after rendering, and both HTML renderers use the same metadata.

The gallery image sitemap uses durable image URLs already recorded in the site.
Midjourney URLs excluded by the renderer are excluded from the sitemap too.
The default social card is `images/social-default.png`, a real 1200x630 PNG.

Run a local static server from the repo root, for example:

```bash
python -m http.server 4173
```

Then open [http://127.0.0.1:4173/index.html](http://127.0.0.1:4173/index.html).

## Project Structure

- `index.html` - homepage and latest-image showcase
- `gallery.html` - searchable gallery
- `blog.html` - blog landing page and editorial entry point
- `news.html` - news landing page
- `music.html` / `videos.html` / `tools.html` - supporting sections
- `data/gallery.json` - gallery source data
- `styles.css` - shared site styling
- `content/` - editable markdown content
- `news-digests/` - news source material used by the site
- `scripts/refresh-site-data.ps1` - local refresh pipeline for homepage/news/A-List validation
- `scripts/run-scheduled-refresh.ps1` - scheduled entrypoint for morning full refresh and evening news-only refresh
- `scripts/run-smoke-test.ps1` - local browser smoke-test wrapper for the public pages
- `scripts/migrate-images.py` - repoint expired Midjourney CDN media to repo-local hosting or Cloudflare R2
- `scripts/rebuild-homepage-gallery.py` - repoint homepage gallery items from `data/gallery.json`
- `scripts/smoke-test-site.mjs` - browser smoke test for key public pages
- `docs/CONTENT-FLOWS.md` - source-of-truth and refresh documentation

## Publishing Notes

- The site is designed to be deployed as a static website.
- If you use GitHub Pages or another static host, make sure the custom domain and DNS are configured there rather than in the source files.
- The old Decap CMS shell has been removed from the public site until a real authenticated editorial workflow exists. The archived shell files are stored offline under `W:\Websites\LOCAL-ONLY\archive\axylusion-admin-shell\2026-04-21\`.
- Media uploads for the old CMS shell were configured to land in `images/uploads/`.
- The current public site is driven by static HTML, `news-digests`, and JSON payloads rather than automatic markdown-to-page rendering from `content/`.
- Local unattended refresh is now registered through the central website scheduler:
  - `Websites-AxyLusion-Refresh-Morning` at `07:20`
  - `Websites-AxyLusion-Refresh-Evening` at `19:20`

## Links

- Main website: [koltregaskes.com](https://koltregaskes.com)
- X: [@Axylusion](https://x.com/Axylusion)
- Instagram: [@axylusion](https://www.instagram.com/axylusion)
- YouTube: [@AxyLusion](https://www.youtube.com/@AxyLusion)
- TikTok: [@axylusion](https://www.tiktok.com/@axylusion)

## Launch security code (hub #1508)

The current origin is GitHub Pages behind Cloudflare DNS. Pages does not honour
Cloudflare Pages `_headers` files. `cloudflare-response-headers.json` is the
response-header Transform Rule payload for the existing proxied production host;
apply it through the existing zone's `http_response_headers_transform` ruleset
only in the authorised hosting change. This PR does not change DNS or provider
settings. HSTS omits includeSubDomains/preload. CSP is report-only until actual
media, embeds and inline script/style behaviour have been checked in production;
it is not an enforced CSP or proof of deployed headers. If traffic is DNS-only,
the rule cannot apply. Verify the actual response headers after hosting cutover.

`npm ci --ignore-scripts` installs the lockfile; `npm audit --audit-level=low`
fails on all reported severities. `scripts/scan-source-secrets.py` scans tracked
text with redacted output, excluding environment files and binaries, not history.
`scripts/check-external-links.py` performs a bounded external crawl and treats
401/403/429 responses as unverified warnings requiring review, rather than claiming them safe. Definite errors and HTTPS downgrades fail CI.
No form handler, payment or store setup is added by these changes.