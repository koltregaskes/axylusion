# Axy Lusion Launch Readiness

Last updated: 2026-04-09

## Ready Now

- Structural validation is automated in `.github/workflows/validate-site.yml`.
- Browser smoke tests now run in CI through `scripts/smoke-test-site.mjs`.
- News digest indexing is automated locally via `scripts/update-news-digest-index.py` and validated in CI.
- A single local refresh pipeline now exists at `scripts/refresh-site-data.ps1`.
- Homepage showcase repointing is automated locally via `scripts/rebuild-homepage-gallery.py`.
- The site now carries a dedicated favicon and a cleaner A-List navigation label.
- The A-List has a machine-readable local snapshot path via `scripts/sync-a-list-benchmarks.py` and `data/a-list-benchmarks.json` once synced.

## Still Blocked Externally

- Gallery and homepage images still point at expired `cdn.midjourney.com` URLs until the Cloudflare R2 migration is completed.
- The Decap CMS admin login depends on live authentication setup and should not be treated as launch-ready unless Netlify Identity or GitHub OAuth is configured.
- The custom domain handoff still needs to be applied after the final deploy target is chosen.

## Launch Sequence

1. Download the published Midjourney images and upload them to Cloudflare R2.
2. Run `python scripts/migrate-images.py` to rewrite website image URLs.
3. Run `powershell -File scripts/refresh-site-data.ps1`.
4. Run `node scripts/smoke-test-site.mjs --base-url http://127.0.0.1:4173` against a local preview server.
5. Deploy, confirm production rendering, then connect the custom domain.

## Phase 2 Follow-Up

- Rebuild the missing Midjourney archive extraction and import pipeline documented in `MIDJOURNEY-PUBLISHED-GALLERY-MIGRATION-PLAN.md`.
- Decide whether `/admin` is part of the live publishing workflow or should remain offline until authentication is configured.
- If the shared benchmark pipeline becomes part of routine ops, schedule `scripts/sync-a-list-benchmarks.py` as part of the same weekly refresh flow.
