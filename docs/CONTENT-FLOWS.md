# Axy Lusion Content Flows

Last updated: 2026-04-09

## Public Sources Of Truth

- Gallery pages read from `data/gallery.json`, with `gallery.js` carrying the embedded fallback copy for offline use.
- Homepage hero and showcase panels read from `data/homepage-gallery.json`.
- News reads from `news-digests/*.md` plus `news-digests/index.json`.
- The A-List currently serves static HTML pages backed by the local snapshot in `data/a-list-benchmarks.json`.

## Refresh Commands

- Gallery export from the shared database: `powershell -File scripts/sync-published-gallery.ps1 -Apply`
- Homepage payload rebuild from the gallery export: `python scripts/rebuild-homepage-gallery.py`
- News digest manifest refresh: `python scripts/update-news-digest-index.py`
- A-List snapshot refresh from AI Resource Hub: `python scripts/sync-a-list-benchmarks.py`
- Combined local refresh pipeline: `powershell -File scripts/refresh-site-data.ps1`
- Structural validation: `python scripts/validate-site.py`
- Browser smoke test after serving the repo locally: `node scripts/smoke-test-site.mjs --base-url http://127.0.0.1:4173`

## CMS Caveat

- `admin/config.yml` defines Decap CMS collections under `content/`, but the current public site does not rebuild pages from those markdown files automatically.
- `content/about.md`, `content/blog/*`, and `content/news/*` should therefore be treated as staged editorial content until a renderer/export step is added.
- The live news page is driven by `news-digests`, not `content/news`.

## Launch Notes

- The homepage gallery should be rebuilt after any gallery repoint, especially the Cloudflare R2 migration.
- The browser smoke test currently tolerates Midjourney-hosted failures only on `index.html` and `gallery.html`, because those are the known launch blockers.
- Once the R2 migration is complete, the smoke test should pass cleanly across every checked page with no allowed failures.
