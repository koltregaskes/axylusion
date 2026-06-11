# Midjourney Archive Intake

Last updated: 2026-05-30

## Purpose

This checklist is the safe local handoff for the Axy Lusion gallery migration task.
It standardizes where a recovered Midjourney image archive should be staged before
running `scripts/migrate-images.py`.

## Canonical Staging Path

Place the recovered image archive under:

`W:\Websites\sites\axylusion\scripts\downloaded-images\`

The migration helper defaults to that folder when no explicit download path is
passed.

## Expected File Shape

- Image files may live in nested folders.
- Supported extensions: `.png`, `.jpg`, `.jpeg`, `.webp`
- Filenames must contain the Midjourney job UUID used by `data/gallery.json`.

Examples:

- `4147cb5f-c531-47fd-b8a2-ab4ec1a424e9.png`
- `koltregaskes_cinematic_portrait_4147cb5f-c531-47fd-b8a2-ab4ec1a424e9.png`

## Resume Workflow

1. Stage the recovered archive into `scripts\downloaded-images\`.
2. Run `python scripts/migrate-images.py scan scripts/downloaded-images`
3. Confirm the match count is non-zero and note how many gallery items remain unmatched.
4. Run `python scripts/migrate-images.py stage-local scripts/downloaded-images`
5. Rebuild any dependent gallery payloads if needed.
6. Verify pages locally and confirm the migrated items no longer point at `cdn.midjourney.com`.

## Verification Commands

```powershell
python scripts/migrate-images.py status
python scripts/migrate-images.py scan scripts/downloaded-images
```

After a successful local staging pass:

```powershell
python scripts/migrate-images.py stage-local scripts/downloaded-images
python scripts/migrate-images.py status
```

## Current Blocker

The repo still has no local Midjourney source archive to stage, so the migration
cannot proceed beyond path preparation and scan readiness.
