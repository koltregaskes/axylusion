# Axy Lusion Content Flows

Last updated: 2026-04-11

## Public Sources Of Truth

- Gallery pages read from `data/gallery.json`, with `gallery.js` carrying the embedded fallback copy for offline use.
- Homepage hero and showcase panels read from `data/homepage-gallery.json`.
- News reads from `news-digests/*.md` plus `news-digests/index.json`.
- The A-List serves static HTML pages generated from `data/a-list-benchmarks.json`.
- Public scores are the Elo copied from Artificial Analysis into `data/aa-leaderboard-capture.json` by `scripts/refresh-a-list-benchmarks.py`. The retrieval date on the page is that capture's date.
- `scripts/sync-a-list-benchmarks.py` still reads the AI Resource Hub cache at `W:\Websites\sites\ai-resource-hub\data\pg-cache\creative_benchmarks.json`, but it will not replace a current arena snapshot when that cache's newest `updated_at` or `scraped_at` is older than 45 days.
- Music, 3D, and upscaling stay off the public A-List until a current public Elo board exists. Do not republish the 24 August 2026 editorial scores.

## Refresh Commands

- Gallery export from the shared database: `powershell -File scripts/sync-published-gallery.ps1 -Apply`
- Homepage payload rebuild from the gallery export: `python scripts/rebuild-homepage-gallery.py`
- News digest manifest refresh: `python scripts/update-news-digest-index.py`
- A-List arena refresh from the public Artificial Analysis boards: `python scripts/refresh-a-list-benchmarks.py`
- A-List hub-cache sync, refused when that cache is stale: `python scripts/sync-a-list-benchmarks.py`
- A-List page render from the snapshot: `python scripts/render-a-list.py`
- Combined local refresh pipeline: `powershell -File scripts/refresh-site-data.ps1`
- Combined local refresh pipeline without A-List sync/render: `powershell -File scripts/refresh-site-data.ps1 -SkipAList`
- Combined local refresh plus browser verification: `powershell -File scripts/refresh-site-data.ps1 -RunSmokeTest`
- Structural validation: `python scripts/validate-site.py`
  This now includes A-List drift checks for both the synced snapshot and the rendered public pages.
- Browser smoke test wrapper: `powershell -File scripts/run-smoke-test.ps1`
- Browser smoke test after serving the repo locally: `node scripts/smoke-test-site.mjs --base-url http://127.0.0.1:4173`
- Scheduled refresh wrapper: `powershell -File scripts/run-scheduled-refresh.ps1 -Mode Morning|Evening`

## Scheduled Ops

- `Websites-AxyLusion-Refresh-Morning` runs daily at `07:20`.
  It runs the full refresh path: homepage payload, news digest index, A-List arena refresh, hub-cache sync, render, then validation.
- `Websites-AxyLusion-Refresh-Evening` runs daily at `19:20`.
  It runs the lighter evening path: homepage payload, news digest index, then validation.
- Both tasks are registered through `W:\Websites\schedules\jobs.psd1` and execute through `W:\Websites\schedules\monitoring\Run-Logged.ps1`, so runs land in shared `cron_job_history`.
- Shared watchdog coverage also exists in `W:\Websites\schedules\monitoring\Check-Freshness.ps1`, which now alerts if either Axy scheduled refresh stops landing in `cron_job_history`.
- These tasks intentionally do not duplicate upstream jobs:
  - `LLATOS Website News Cycle`
  - `AI Resource Hub - Daily Update`

## CMS Caveat

- The old Decap CMS shell has been archived offline under `W:\Websites\LOCAL-ONLY\archive\axylusion-admin-shell\2026-04-21\` and is no longer part of the public site.
- The archived `config.yml` defined Decap CMS collections under `content/`, but the public site still does not rebuild pages from those markdown files automatically.
- `content/about.md`, `content/blog/*`, and `content/news/*` should therefore be treated as staged editorial content until a renderer/export step is added.
- The live news page is driven by `news-digests`, not `content/news`.

## Launch Notes

- The homepage gallery should be rebuilt after any gallery repoint, especially the Cloudflare R2 migration.
- `scripts/migrate-images.py stage-local <download-dir>` can now copy a staged Midjourney archive into `images/gallery/` and rewrite gallery URLs for repo-local static hosting without any external bucket.
- The public render path currently uses `images/media-hosting-pending.svg` instead of requesting `cdn.midjourney.com` media, because Midjourney CDN URLs return 403 and are not launch-durable.
- The browser smoke test now expects `index.html` and `gallery.html` to pass cleanly with no allowed Midjourney host failures.
- Once the R2 migration is complete, remove the temporary render fallback and verify the smoke test still passes cleanly across every checked page.
