# Exact-artifact browser gate — 16 November 2026

Hub: #1908. The former runner always served the source checkout. CI now builds a new allowlisted artifact and serves only that directory to the existing all-route axe/CSP/overflow checks at 320, 390 and 1280px. Missing directories, malformed arguments and missing approved HTML routes fail closed. No Pages-source change is included.

Verified: three root-selection negative/positive controls; Node syntax check. Full browser execution and hosted CI are unverified locally: Playwright and axe-core are unavailable. CI already installs its pinned browser-check dependencies. Third-party requests stay blocked; this does not prove real fonts/media, keyboard/gallery interactions, screen-reader behaviour or final-host accessibility. Keep the accessibility checkbox open.

Run: node --test tests/browser-site.test.mjs; python -B scripts/build-public.py --output <new-directory>; node scripts/launch-browser.mjs --site <new-directory>.
