# Axy Lusion Launch Readiness

Last updated: 2026-05-05

## Ready Now

- Structural validation is automated in `.github/workflows/validate-site.yml`.
- Browser smoke tests now run in CI through `scripts/smoke-test-site.mjs`.
- News digest indexing is automated locally via `scripts/update-news-digest-index.py` and validated in CI.
- A single local refresh pipeline now exists at `scripts/refresh-site-data.ps1`.
- Local unattended refresh is now wired through the central scheduler with morning and evening Axy jobs.
- Shared watchdog monitoring now checks that the Axy refresh jobs continue landing in `cron_job_history`.
- Homepage showcase repointing is automated locally via `scripts/rebuild-homepage-gallery.py`.
- The site now carries a dedicated favicon and a cleaner A-List navigation label.
- The public A-List shows Artificial Analysis Elo copied into `data/aa-leaderboard-capture.json`. `scripts/sync-a-list-benchmarks.py` must not publish a hub cache older than 45 days over that snapshot.
- Structural validation checks that the arena snapshot matches its capture and that the rendered ranking pages match the snapshot.
- Homepage and gallery rendering now suppresses direct `cdn.midjourney.com` requests and uses `images/media-hosting-pending.svg` for Midjourney-hosted items until durable media hosting is complete.
- Browser smoke tests now require `index.html` and `gallery.html` to be clean instead of tolerating Midjourney CDN failures.
- The May 2026 A-List composite is not current. Do not treat those scores, or the 24 August 2026 snapshot, as the public list.

## Still Blocked Externally

- Gallery and homepage payloads still contain 1,519 gallery and 18 homepage `cdn.midjourney.com` URLs for migration bookkeeping, but the public render path no longer requests them.
- Full media-rich launch remains blocked until the published Midjourney originals are downloaded and uploaded to Cloudflare R2 or another durable owned host.
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
- Routine A-List refresh belongs in `scripts/refresh-a-list-benchmarks.py`, which copies the current public Elo boards. The hub-cache sync stays behind that step and refuses a stale cache.
