# Privacy artifact gate — 16 November 2026

Hub: #1908. The privacy CLI formerly inspected only source. Use python -B scripts/privacy_check.py --site <artifact> to inspect actual artifact HTML, CSS, JavaScript, manifest and runtime JSON against the source-owned public allowlist/disclosure policy. Policy configuration is intentionally not copied into the public artifact. Missing directories/files and unsafe symlinks fail; no source fallback.

Verified: four retained-fixture controls (clean artifact, artifact-only collector/storage with source-pass and exact byte restoration, missing notice with restore, missing directory CLI); actual 246-file artifact passes with three disclosed resource hosts and no detected site-script storage. git diff --check passes. CI now runs the artifact inventory and controls immediately after building. The legacy privacy suite is unchanged; its temporary-directory cleanup was not run in this no-deletion session.

Limits: this is a conservative static inventory, not a JavaScript interpreter. Dynamically constructed requests, browser/provider storage, real R2/fonts/contact requests and any future analytics/newsletter handling still require final-host browser evidence and owner acceptance. No tracker, subscription service or Pages-source change enabled. Privacy checkbox stays open.
