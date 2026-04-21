# Axy Lusion Content Flows

Last updated: 2026-04-11

## Public Sources Of Truth

- Gallery pages read from `data/gallery.json`, with `gallery.js` carrying the embedded fallback copy for offline use.
- Homepage hero and showcase panels read from `data/homepage-gallery.json`.
- News reads from `news-digests/*.md` plus `news-digests/index.json`.
- The A-List serves static HTML pages generated from `data/a-list-benchmarks.json`.
- `data/a-list-benchmarks.json` is presentation data only: it is synced from the shared AI Resource Hub cache at `W:\Websites\sites\ai-resource-hub\data\pg-cache\creative_benchmarks.json`.
- Shared benchmark acquisition belongs in `W:\Websites\sites\ai-resource-hub\scripts\scrapers\creative-benchmarks.ts`, not in Axy Lusion.

## Refresh Commands

- Gallery export from the shared database: `powershell -File scripts/sync-published-gallery.ps1 -Apply`
- Homepage payload rebuild from the gallery export: `python scripts/rebuild-homepage-gallery.py`
- News digest manifest refresh: `python scripts/update-news-digest-index.py`
- A-List snapshot refresh from AI Resource Hub: `python scripts/sync-a-list-benchmarks.py`
- A-List page render from the synced snapshot: `python scripts/render-a-list.py`
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
  It runs the full refresh path: homepage payload, news digest index, A-List sync/render, then validation.
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
- The browser smoke test currently tolerates Midjourney-hosted failures only on `index.html` and `gallery.html`, because those are the known launch blockers.
- Once the R2 migration is complete, the smoke test should pass cleanly across every checked page with no allowed failures.
