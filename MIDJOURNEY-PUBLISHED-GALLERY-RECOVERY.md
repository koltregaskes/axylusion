# Midjourney Published Gallery Recovery

Last updated: 2026-04-04

## Executive Summary

The important asset is not just the Axy Lusion website. It is the published Midjourney archive pipeline behind it.

As of 2026-04-04, the real system appears to be:

1. Published Midjourney archive items were extracted from the authenticated Midjourney archive.
2. Those items were imported into `W:\Agent Workspace\System\Data\universal.db`.
3. The website-facing gallery export was then generated into `data/gallery.json` and mirrored into the embedded fallback data inside `gallery.js`.

That pipeline is only partly recoverable from surviving files. The database and the website export survive. The extraction/import scripts referenced in older handoffs do not.

## What The Real Pipeline Is

### 1. Archive Extraction

Historical notes in `W:\Agent Workspace\memory\2026-02-14.md` show a real extraction/import workflow for published Midjourney archive images:

- `1,078` new images extracted
- `1,519` total published Midjourney images in `universal.db`
- output artefacts historically named:
  - `System/Scripts/gallery/midjourney-full-sync.py`
  - `System/Scripts/gallery/midjourney-archive-extractor.py`
  - `System/Scripts/gallery/archive-all-items.json`
  - `System/Scripts/gallery/MIDJOURNEY-ARCHIVE-EXTRACTION-GUIDE.md`
  - `System/Scripts/gallery/README.md`

Those exact files are currently missing, but the notes are specific enough to treat the workflow as real historical fact rather than guesswork.

### 2. Database Import

The surviving canonical dataset is in:

- `W:\Agent Workspace\System\Data\universal.db`

Confirmed on 2026-04-04:

- `gallery_items`: `1519` rows
- `gallery_tags`: `70` rows
- `tags`: `311` rows
- all `gallery_items` are `status = published`
- all `gallery_items` are `source = midjourney`

The same memory note also records that the import workflow used WAL mode and required:

- `PRAGMA wal_checkpoint(FULL)`

after import.

### 3. Website Export

The website-facing export survives in both:

- `W:\Repos\_My OLD Websites\axylusion\data\gallery.json`
- `W:\Websites\sites\axylusion\data\gallery.json`

and is duplicated inside:

- `W:\Repos\_My OLD Websites\axylusion\gallery.js`
- `W:\Websites\sites\axylusion\gallery.js`

`gallery.js` first tries to fetch `data/gallery.json`, then falls back to the embedded dataset for `file://` usage.

That means the website delivery layer has always been:

- `data/gallery.json` as the normal served export
- embedded `gallery.js` data as the local/offline fallback

## What Survives

### Surviving Canonical-ish Data

- `universal.db` item inventory in `gallery_items`
- surviving website export in `data/gallery.json`
- embedded fallback copy in `gallery.js`

### Surviving Operational Context

- `W:\Agent Workspace\memory\2026-02-14.md`
- `W:\Agent Workspace\System\Agents\WINS\2026-02-08-midjourney-likes-extraction.md`
- `W:\Agent Workspace\Tasks\2-In-Progress\website-axy-lusion-gallery-dates.md`
- `W:\Agent Workspace\Tasks\2-In-Progress\website-axy-lusion-cdn-image-fix.md`
- `W:\Agent Workspace\.claude\skills\midjourney-date-extraction\SKILL.md`

### Surviving Live-Repo Helper

The current active Axy Lusion repo already contains an R2 migration helper:

- `W:\Websites\sites\axylusion\scripts\migrate-images.py`

That script is useful for the hosting migration, but it is not the original published-archive extraction/import pipeline.

## What Is Missing

These historically referenced operational pieces are not currently present:

- `System/Scripts/gallery/midjourney-full-sync.py`
- `System/Scripts/gallery/midjourney-archive-extractor.py`
- `System/Scripts/gallery/archive-all-items.json`
- `System/Scripts/gallery/MIDJOURNEY-ARCHIVE-EXTRACTION-GUIDE.md`
- `System/Scripts/gallery/README.md`
- the `midjourney-archive-extractor` skill mentioned in memory

This is the main reason the published-image pipeline feels broken today: the delivery artefacts remain, but the extraction/import machinery is gone.

## Data Drift That Must Be Treated Explicitly

### Item Inventory

The DB and website export match exactly at the item-ID level:

- `json_only = 0`
- `db_only = 0`
- `intersection = 1519`

So inventory membership is aligned.

### Created Dates

Created dates are not trustworthy enough to treat as canon yet.

DB state:

- only `14` items have a non-empty `gallery_items.created`
- `1505` DB rows have an empty created date

Website export state:

- all `1519` items have a `created` value
- `1167` items share the exact date `2026-02-10`

That heavy clustering strongly suggests the site export contains placeholder or import-date fill values for much of the archive.

### Model / Version Metadata

DB state:

- `1492` items have empty/null `model`
- only `27` items explicitly say `Midjourney v7`

Website export state:

- `1301` items say `Midjourney v7`
- `192` items say `Midjourney v6`
- `26` items say `Midjourney v5`

The website export is much richer here, but it is not proven from the DB. Treat it as website-facing enrichment, not fully audited truth.

### Tags

DB tags lag far behind website tags.

DB state:

- `gallery_tags` contains `70` rows total
- only `14` items have any DB tags at all

Website export state:

- `1233` items are tagged
- `18` distinct tags are used heavily across the export

The website export is clearly the richer tagging surface today.

### Parameters

Parameters are equally sparse in both places:

- `1126` items are missing parameters in the DB
- `1126` items are missing parameters in the website export

So the website export did not solve parameter completeness.

## Source Of Truth By Concern

| Concern | Recommended truth now | Why |
|---|---|---|
| Published item inventory | `universal.db.gallery_items` | Exact 1519-item inventory with published/source status |
| Prompt text | `universal.db.gallery_items.prompt` | Best surviving imported prompt field |
| Source URLs | `universal.db.gallery_items.url` and `cdn_url` | Best surviving imported source records |
| Website export payload | `data/gallery.json` plus embedded `gallery.js` | Actual website delivery layer |
| Tags | Website export `tags` for now | DB tagging is far too incomplete |
| Created dates | Neither is fully canonical yet | DB is mostly empty; JSON has obvious placeholder clustering |
| Model/version | Website export for display, pending re-audit | DB is too sparse to drive the site today |
| Collections/groupings | None yet | DB collection tables are empty |

## Recommended Interpretation

Use the DB as the canonical inventory and prompt/source layer.

Use the current website export as a temporary enrichment layer for:

- tags
- created dates
- model labels

until extraction/import is rebuilt and those fields can be regenerated properly upstream.

## Stale Or Dangerous Assumptions

- `_My Websites` and `_My OLD Websites` are not interchangeable. The older repo evidence now lives under `_My OLD Websites`.
- Older Axy handoffs that call `gallery.json` the full source of truth are out of date. They describe the static-site layer, not the later DB-backed archive pipeline.
- The missing `System/Scripts/gallery` folder should not be assumed recoverable just because memory notes mention it.
- The website's `created` dates should not be treated as historically accurate without audit.
- Midjourney CDN URLs are not durable. They are delivery inputs, not a permanent hosting solution.

## What Should Be Migrated Into Workspace 2 / Current Estate

Migrate the operational pattern, not just the static JSON file:

1. DB-backed published inventory as the upstream record
2. export step that rebuilds `data/gallery.json` and `gallery.js`
3. R2 migration path for permanent image hosting
4. explicit documentation of metadata drift and confidence levels

## Immediate Recovery Outcome In The Live Repo

The active Axy Lusion repo now includes a rebuilt export layer:

- `scripts/export-published-gallery.py`
- `scripts/sync-published-gallery.ps1`

These scripts are designed to rebuild the website export from `universal.db` while preserving the current richer website metadata where the DB is still incomplete.
