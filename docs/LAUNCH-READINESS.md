# Axy Lusion Launch Readiness

Last updated: 2026-04-11

## Ready Now

- Structural validation is automated in `.github/workflows/validate-site.yml`.
- Browser smoke tests now run in CI through `scripts/smoke-test-site.mjs`.
- News digest indexing is automated locally via `scripts/update-news-digest-index.py` and validated in CI.
- A single local refresh pipeline now exists at `scripts/refresh-site-data.ps1`.
- Local unattended refresh is now wired through the central scheduler with morning and evening Axy jobs.
- Shared watchdog monitoring now checks that the Axy refresh jobs continue landing in `cron_job_history`.
- Homepage showcase repointing is automated locally via `scripts/rebuild-homepage-gallery.py`.
- The site now carries a dedicated favicon and a cleaner A-List navigation label.
- The A-List now has a shared-source flow: AI Resource Hub acquires benchmark data, Axy Lusion syncs that cache into `data/a-list-benchmarks.json`, and `scripts/render-a-list.py` rebuilds the public ranking pages locally.
- Structural validation now catches A-List drift, so stale benchmark snapshots or stale rendered ranking pages fail the check instead of silently shipping.

## Still Blocked Externally

- Gallery and homepage images still point at expired `cdn.midjourney.com` URLs until the Cloudflare R2 migration is completed.
- The custom domain handoff still needs to be applied after the final deploy target is chosen.

## Launch Sequence

1. Download the published Midjourney images and upload them to Cloudflare R2.
2. Run `python scripts/migrate-images.py` to rewrite website image URLs.
3. Run `powershell -File scripts/refresh-site-data.ps1`.
4. Run `powershell -File scripts/run-smoke-test.ps1` for a local browser pass.
5. Deploy, confirm production rendering, then connect the custom domain.

## Phase 2 Follow-Up

- Rebuild the missing Midjourney archive extraction and import pipeline documented in `MIDJOURNEY-PUBLISHED-GALLERY-MIGRATION-PLAN.md`.
- The old Decap CMS shell has now been archived offline and removed from the public site until a real authenticated workflow exists.
- If the shared benchmark pipeline becomes part of routine ops, schedule `scripts/sync-a-list-benchmarks.py` as part of the same weekly refresh flow.
