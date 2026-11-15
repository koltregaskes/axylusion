# Axy Lusion Content Flows

Last updated: 2026-11-15

## Public Sources Of Truth

- Gallery pages read from `data/gallery.json`, with `gallery.js` carrying the embedded fallback copy for offline use.
- Homepage hero and showcase panels read from `data/homepage-gallery.json`.
- News reads `news-digests/news-feed-latest.json` when that file has articles. A successful gatherer run that matches nothing writes a fresh empty list, and the page keeps the digest archive in `news-digests/*.md` plus `news-digests/index.json`. The legacy main-branch Pages build remains the only publishing route; a GITHUB_TOKEN push starting that build still needs execution proof. Partial runs publish successful-source items and record failures; items from failed sources may drop. Total source outages preserve the previous feed, and partial coverage fails the freshness check.

## A-List withdrawal (hub #615 and #1508)

The A-List is being rebuilt from sources we have permission to publish.
Artificial Analysis data files are archived off-site and absent from this public tree.
The acquisition and cache-sync commands explicitly skip all work, including --check.
`render-a-list.py` now renders only noindex holding pages, without reading a snapshot.
No scheduled refresh invokes acquisition or ranked rendering. Retained legacy code is
inactive. Restoration requires written permission, a reviewed code change and fresh checks.

## Refresh Commands

- Gallery export from the shared database: `powershell -File scripts/sync-published-gallery.ps1 -Apply`
- Homepage payload rebuild from the gallery export: `python scripts/rebuild-homepage-gallery.py`
- News digest manifest refresh: `python scripts/update-news-digest-index.py`
- Combined local refresh pipeline: `powershell -File scripts/refresh-site-data.ps1`
- Combined local refresh pipeline without A-List sync/render: `powershell -File scripts/refresh-site-data.ps1 -SkipAList`
- Combined local refresh plus browser verification: `powershell -File scripts/refresh-site-data.ps1 -RunSmokeTest`
- Structural validation: `python scripts/validate-site.py`
  This checks that A-List snapshots remain absent and all eight old routes are data-free holding pages.
- Skip-navigation regression checks: `python -B scripts/test-navigation.py`.
  The shared renderer keeps existing skip links pointed at the main landmark, including
  when its ID changes. These offline checks also require current public pages to remain
  unchanged and do not activate staged editorial content.
- Browser smoke test wrapper: `powershell -File scripts/run-smoke-test.ps1`
- Browser smoke test after serving the repo locally: `node scripts/smoke-test-site.mjs --base-url http://127.0.0.1:4173`
- Scheduled refresh wrapper: `powershell -File scripts/run-scheduled-refresh.ps1 -Mode Morning|Evening`

## Scheduled Ops

- `Websites-AxyLusion-Refresh-Morning` runs daily at `07:20`.
  It runs the full refresh path: homepage payload, news digest index, news rendering, SEO, then validation. A-List acquisition is disabled in both modes.
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
