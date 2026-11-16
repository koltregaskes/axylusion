# Axy Lusion operator runbook

Prepared 16 November 2026 for hub #1908 / #1508. This is a reviewable procedure, not operational acceptance. Existing launch owner agent:claude retains custody through the current site operator. Kol approves first launch, domain/DNS/mail/account changes and public delivery. No new scheduler, collector or backup owner is created.

## Current routes and constraints

- News: `.github/workflows/refresh-routed-feed.yml`, 05:15 UTC daily, reads the existing shared news configuration, writes `news-digests/news-feed-latest.json`. Partial coverage records failures and fails the run; total outage preserves the previous feed. A successful empty selection is valid. It can request the existing main-branch Pages build; do not manually dispatch it without publication approval.
- Freshness: `routed-feed-freshness.yml`, 06:30 UTC daily. Fails at one day or partial source coverage; the check does not fetch or fabricate articles. A workflow failure is not proof that an operator received an alert.
- Validate Site: 06:15/18:15 UTC plus pushes/PRs; this is structural/browser validation, not a publisher or a received alert.
- Live parity: `live-parity.yml` is manual only. Its source comparison is not proof that the proposed allowlist controls publishing. Preserve Kol's Pages-source approval gate.
- Gallery: static artwork needs no invented daily edits. Existing gallery exporter/publish guard and archive owner retain custody. A-List acquisition/output stays disabled (#615).
- Local scheduled wrapper depends on the existing central Windows runner. `CONTENT-FLOWS.md` and `run-scheduled-refresh.ps1` name different runner paths. These are source references, not current installation evidence. Existing admitted scheduler owner must verify the actual task command, host, last result and history before changing either. This gaming laptop is not an always-on host. Do not run the wrapper here as a health test.

## Safe local preflight

Freeze and record the full candidate SHA and UTC check time. Work in a clean review branch; preserve all work. These commands inspect source without deployment:

```powershell
git status --short
git rev-parse HEAD
python -B scripts/update-news-digest-index.py --check
python -B scripts/build-seo.py --check
python -B scripts/check-seo.py
python -B scripts/check-internal-links.py
python -B scripts/privacy_check.py
python -B scripts/meta_csp.py
python -B scripts/validate-site.py
node --test tests/refresh-routed-feed.test.mjs tests/routed-feed-freshness.test.mjs tests/news-order.test.mjs tests/feed-publication.test.mjs
node scripts/check-routed-feed-freshness.mjs
```

Freshness failure must be reported with original source/generated timestamps and failed-source names. Do not refresh a timestamp to silence it. Build a new artifact with `python -B scripts/build-public.py --output <new-directory>`; never reuse or clear an existing directory. After artifact-link PR #124 and the separately prepared SEO artifact change are accepted, run their `--site <new-directory>` checks on that exact output.

## Incident and recovery

1. Record incident UTC, candidate/deployed SHA, failing workflow URL or check, affected routes and source coverage on #1908; escalate launch risk to #1508 and existing owner. Keep sensitive provider/account details private. Do not poll. Use the existing run's completion result once available.
2. For feed failure, preserve the previous good feed and inspect the existing refresh failure summary. Repair only the failing source/filter path; never replace an outage with a fabricated empty success. Require a successful natural run and exact destination receipt after the approved fix.
3. For missing media or gallery shrink, stop publication and preserve manifests, originals and variants. Reuse the count/unavailable guard. Match job AND variant; do not substitute a same-job image or delete unavailable records to make a count pass.
4. For failed deployment/parity, freeze further publication. Compare the actual public bytes with the intended frozen commit using `python -B scripts/check-live-parity.py --ref <full-sha>` (read-only network access). Record redirects and actual headers separately; `_headers` is not enforced by Pages.
5. Rollback requires Kol's approval for public delivery. Existing operator selects the previously evidenced known-good commit/artifact and opens a reviewed revert/restore branch, retaining the failed version. Do not reset/force-push main or delete files. Deploy only through the approved existing Pages route. Then verify exact public bytes, gallery/media, feed, redirects, TLS/headers and contact journey again. No known-good deployment SHA or successful rollback is asserted by this document.

## Monitoring acceptance still required

Use existing workflow notifications/watchdog; do not add a competing timer. Existing operator must choose and confirm a recipient privately. In an isolated fixture, prove stale feed, partial/lost source, missing media, parity mismatch and deployment failure each lead to one received operator alert; then restore the exact fixture bytes and record recovery. Do not break production to exercise a failure. Record run URL, received UTC, acknowledged owner and recovery receipt without inbox addresses or message payloads. Until received evidence exists, alerting is UNKNOWN.

## Backup and isolated restore

Existing archive/media owner retains original exports. Repository clones alone do not back up externally hosted R2 images or unpublished originals. Agree a retained-copy location and retention policy with that owner; never copy secrets/.env. Public derivatives, manifests/prompts/permitted-use evidence, approved content and non-secret configuration need retained copies, with source revision, relative filenames, sizes and SHA256. Do not move, prune or overwrite originals.

For an operator-authorised rehearsal: copy a frozen approved backup into a NEW isolated directory, verify every checksum, and match gallery ID + image variant to restored files. Check image decode/dimensions, available/unavailable counts, captions/provenance and permissions against the saved manifest. Build/validate the restored artifact there, including internal/media links and privacy inventory. Keep an evidence record of matched/missing/ambiguous counts and bytes restored. A copied manifest or an intact ZIP alone is not restore acceptance. Do not upload the rehearsal or extract unrelated private archives. Original-media coverage and a real restore are currently UNVERIFIED here.

## Before launch and BAU

Current planning window: 21–23 December 2026, exact day unassigned; Axy is second after Kol's Korner. Readiness is D−14, with seven consecutive proofs D−20 through D−14, followed by 14 days BAU. Existing owner records the assigned day; do not infer it from old dates.

Each dated proof must link execution, source timestamp/coverage, frozen commit, exact deployed-byte/media readback and received alert/recovery evidence. Final acceptance also needs full accessibility/screen-reader and mobile performance checks, external destination dispositions, final-host request/storage privacy review, actual aggregate-only collector event under #1498/#367, and domain/contact/mail/search readbacks. This repo currently declares GitHub Pages, Google Fonts and R2 in its privacy inventory; do not enable analytics/newsletter and leave the notice unchanged. Keep owned analytics account/collector custody with the existing owner; source-only fixtures do not prove ingestion.

After launch: review existing morning refresh/freshness completions and incoming alerts, investigate failures promptly, check weekly dependency PRs under the proposed maintenance procedure, and repeat retained backup/restore receipts on the owner-approved cadence and after material media/manifest changes. Exact retention/cadence, alert recipient, named operator acceptance, known-good SHA and seven-day receipts remain open on #1908. This document must not tick those boxes.

## Local preflight receipt — 16 November 2026

Run against base `17570b48334ee8a6ff77b01f4e77ef53440794da` plus this documentation only. Digest manifest current; SEO generation/check passed (11 indexable pages, 11 sitemap URLs, 18 image entries, 135 RSS items); 20 HTML internal-link routes passed; privacy inventory and meta CSP passed; structural validation passed with the existing 1,519 Midjourney bookkeeping URL warning. All 20 Node feed/publication/order/freshness regressions passed; their deliberately injected 404/429 errors are fixture output. The committed feed generated at 2026-11-16T13:36:13.334Z passed freshness with zero matching articles. No actual source fetch, scheduled run, deployment, live readback, alert delivery, backup or rollback was performed by this preflight. Hosted CI is unverified.
