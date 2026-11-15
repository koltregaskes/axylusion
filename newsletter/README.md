# Creative newsletter draft

This is an offline contract and static edition build, not a subscription service.
`data/site-config.json` must contain `newsletter.signupsOpen: false`. Both the
build and site validator fail if it is changed or omitted. There is no form,
collector, provider account, deployed API, real subscriber store or live sender.

Run `python -B scripts/build-seo.py`, then `--check`. The build uses the existing
cinematic shell, CSP, navigation, SEO, sitemap, RSS and llms discovery. News links
to `editions.html` and `newsletter.html`. Dated pages live under `editions/`.
`data/newsletter-editions.json` supplies exactly the same items to email rendering.
The latest 32 indexed digests match the News archive window. Existing edition
files are retained when they leave the window. A routed snapshot also generates
an edition on its recorded UTC generation day, including when it is empty.

`categories.json` is the shared mapping for the existing News topic aliases and
newsletter: Image -> Visuals, Video -> Video, Audio -> Audio, Tools -> Workflows.
3D -> Visuals; Benchmarks -> Workflows. First recognised source tag wins, following
the existing News convention; unmatched tags use Tools. No claim of new editorial
classification is made. The source feed and archive can contain different stories.
The browser previously treated `art_ai` as Image while Python used Tools; both
now use Tools from this shared mapping, embedded on the generated News list.
Render `python -B scripts/render-cinematic-site.py --page news` after changing
the mapping; the offline acceptance test rejects an out-of-date embedded map.
The latest feed's count, failures and partial status are displayed, even at zero.

Every item has its recorded source date or an explicit unavailable label. Digest
dates and feed generation times never become story publication dates. Fresh means
the source date is the edition date or the preceding date (UTC calendar days).
Older, future-dated and undated items stay labelled on the archive page and are
excluded from email. No fresh preference match returns `skipped`. Sending an old
edition also returns `skipped`; it never counts as a delivered daily edition.
Last updated is a source snapshot stamp, with date-only precision stated when no
update time exists. No current feed fetch, external link verification or editorial
fact-check is implied by generating these supplied sources.

## Future backend integration

`contract.mjs` needs an injected clock, signing key of at least 32 random bytes,
HTTPS backend base and `async send(message)` interface. It never reads environment
variables or calls the network. `MemoryTransport` only captures messages;
`ResendTransport` throws `not configured` without runtime injection, and still
throws `not implemented` with a key. The service accepts only fake capture receipts.
No live adapter or browser bundle imports this module.

To integrate a Worker or another backend, port the Node crypto/fs boundary as
needed, and implement durable private storage, transactions, suppression and an
outbox. Persist the record (email, categories, consent time/version, confirmation,
preference-change and unsubscribe times) and send receipts. The current maps and
idempotency set disappear on restart. They are test doubles, not persistence.
Prevent retries from resending, and recheck suppression immediately before dispatch.

Expose rate-limited, validated subscription POSTs with neutral responses, a
confirmation email and explicit confirmation POST; a GET only previews. Never
activate pending records. Preference links expire after one hour; confirmation
tokens after 24 hours. Re-registration does not overwrite existing records or
reactivate unsubscribed addresses. Design a fresh-consent reactivation and expired
link recovery flow before production. Keep tokens and addresses out of logs.

Map the signed unsubscribe URL to `oneClick`: GET is read-only, and POST accepts
`application/x-www-form-urlencoded` with `List-Unsubscribe=One-Click` without a
login. Repeated valid POSTs succeed, including after preference changes. An email
app uses `List-Unsubscribe` and `List-Unsubscribe-Post`; the visible link opens a
confirmation page which POSTs. Production DKIM must cover both headers for RFC
8058. Implement that endpoint, anti-abuse controls, key rotation, HTTPS, retention,
access controls, deletion handling, provider errors, bounce/complaint suppression,
monitoring and recovery before opening sign-ups. Review privacy and consent copy
against the actual service. Do not merely flip the flag: remove its fail-closed
guard only in a separately reviewed backend integration.

## Kol's steps and acceptance still open

1. Create the selected Resend account when the backend and test plan are ready.
2. Verify the sending domain in Resend, approving required DNS changes separately.
3. Review the actual privacy/retention terms and approve the first page publication
   and first send, separately from the site launch.

Then deploy the authorised backend, obtain explicit test-recipient consent, and
prove confirmation receipt, category changes, one-click unsubscribe, no delivery
after suppression, failure/retry recovery, and a received email linking to the
dated public edition. Record deployed freshness and delivery receipts. None of
those outcomes, domain settings, inbox acceptance, browser accessibility or public
deployment is proved by this draft's unit tests.

Offline tests: `python -B scripts/test-newsletter.py` and
`node --test newsletter/newsletter.test.mjs`. CI runs them in Launch contract.
