# Dependency maintenance

Prepared for hub #1908 / #1508, 16 November 2026. Recommended accountable owner: the existing Axy launch/operator owner (agent:claude); Codex prepares fixes and evidence. Owner acceptance remains pending on the hub. No new runtime owner is appointed here.

The proposed Dependabot configuration opens weekly npm and GitHub Actions review PRs, Monday 09:00 Europe/London, at most three open per ecosystem. It activates only if approved and merged to the default branch. No auto-merge, deployment or paid service is enabled by this PR.

For each update:

1. Review the resolved package/action changes and upstream advisory/release evidence. Keep `package.json`, lockfile and any workflow-pinned Playwright versions compatible; browser launch checks currently install their own pinned version.
2. In an authorised checkout, run `npm ci --ignore-scripts` and `npm audit --audit-level=low`. Launch security already runs these in CI. Record UTC date, full head SHA, lockfile SHA256 and advisory counts/dispositions. A network failure or absent audit is UNKNOWN, not clean.
3. Require the existing Launch security, Validate Site, Launch contract, CSP and PNG contracts on the exact candidate head, including real browser smoke coverage. Changes to Actions must retain minimum permissions and avoid exposing credentials.
4. Retain a known-good head. Existing owner reviews and Kol approves any merge/public delivery under the launch gates. Urgent exploitable advisories escalate on #1908/#1508 without waiting for Monday. Never run `npm audit fix --force` as a substitute for review.
5. Repeat the authorised redacted repository/history/artifact scan at the frozen launch head. Do not open .env or report matched secret values. Follow scanner admission limits; this PR does not claim a history or artifact scan.

Local evidence: configuration and lockfile are parseable; the lock currently resolves Playwright and Playwright Core 1.64.0. No package was upgraded or installed. A dated advisory lookup, bot first-run, owner acceptance, hosted checks and full security acceptance remain unverified.
