# Midjourney Published Gallery Migration Plan

Last updated: 2026-04-04

## Goal

Move the useful published Midjourney archive process into the active Axy Lusion repo without duplicating the canonical inventory or pretending the old static export is the whole system.

## Migration Table

| Source artefact | Target destination | Action | Blockers / risks | Priority |
|---|---|---|---|---|
| `W:\Agent Workspace\System\Data\universal.db` `gallery_items` | Remain in place as upstream data source for now | Reference | Lives outside this repo; long-term target should be Postgres or a formal shared DB path | P0 |
| `W:\Agent Workspace\System\Data\universal.db` `gallery_tags` | Remain in place, but do not trust as complete | Reference | Tag coverage is materially weaker than the website export | P1 |
| Old site export `data/gallery.json` | `W:\Websites\sites\axylusion\data\gallery.json` | Keep as current delivery export | Contains placeholder/suspect dates and website-only enrichment | P0 |
| Old embedded fallback in `gallery.js` | `W:\Websites\sites\axylusion\gallery.js` | Keep and resync from export | Duplication risk if not regenerated whenever export changes | P0 |
| Missing extraction/import pipeline | `W:\Websites\sites\axylusion\scripts\` | Rebuild | Historical scripts are missing; browser automation against Midjourney must be re-authenticated and re-tested | P0 |
| Missing full-sync docs | `W:\Websites\sites\axylusion\` root markdown files | Rebuild | Memory notes survive, but the real scripts do not | P1 |
| `scripts/migrate-images.py` | Stay in active repo | Keep and extend | Depends on local downloads and R2 credentials | P0 |
| Durable image hosting | Cloudflare R2 | Rebuild / execute | Needs R2 bucket, credentials, and local source image archive | P0 |
| Created-date audit | Shared metadata cleanup process | Rebuild | Current DB dates are mostly empty; current site dates are partly placeholder | P1 |
| Model/version audit | Shared metadata cleanup process | Rebuild | DB sparse, website enriched but not yet fully verified | P1 |
| Tag reconciliation | Upstream metadata pipeline plus website export sync | Rebuild | DB tags and website tags are not aligned | P1 |

## Recommended Priority Order

1. Treat `gallery_items` as the canonical item inventory.
2. Use the rebuilt export script to regenerate website delivery files from the DB plus current website enrichment.
3. Finish the R2 image migration so the site stops depending on expired Midjourney CDN URLs.
4. Rebuild the missing extraction/import step that harvests new published Midjourney items.
5. Rebuild metadata enrichment for dates, models, and tags.
6. Only after that, consider collections/groupings and broader media expansion.

## Weekly Operational Flow

### Short-Term Practical Flow

1. Extract new published Midjourney items from the authenticated archive.
2. Import or reconcile them into `universal.db.gallery_items`.
3. Run `PRAGMA wal_checkpoint(FULL)` after import.
4. Run the active repo export sync:
   - `W:\Websites\sites\axylusion\scripts\sync-published-gallery.ps1`
5. If new files have working permanent media URLs, run the R2 migration update.
6. Review visual output on the website.

### Current Limitation

Step 1 is still missing as executable code. The historical notes prove it used to exist, but it must now be rebuilt.

## What To Copy, Rebuild, Or Reference

### Copy

- No old extraction scripts should be copied blindly because the referenced folder is missing.

### Rebuild

- Published archive extractor
- DB import/reconcile script
- Full sync wrapper
- Metadata enrichment for created dates, tags, and model/version

### Reference

- `universal.db` as the upstream published-inventory source
- current website export as the website-facing enrichment layer
- old repo docs as historical context only

## Key Risks

- Re-exporting directly from the DB without enrichment would degrade the live site because created dates, tags, and model labels are currently stronger in the website export than in the DB.
- Midjourney CDN URLs are still expiring and cannot be treated as permanent media.
- Older handoffs and plans refer to paths that no longer exist, especially `_My Websites` and `System/Scripts/gallery`.
- The current repo already contains duplicate delivery data in `gallery.js` and `data/gallery.json`, so any export process must keep them in sync.

## Concrete Next Steps

1. Use `scripts/export-published-gallery.py` as the active delivery rebuild step.
2. When R2 is ready, use `scripts/migrate-images.py` to repoint `cdn_url` values away from Midjourney.
3. Rebuild the missing archive extractor as a separate authenticated browser automation job.
4. Add a proper metadata audit pass for:
   - created dates
   - tags
   - model/version
5. Once extraction/import is rebuilt, schedule the full sync as a regular local job.
