# Remaining launch content — 16 November 2026

Hub owner/claim: [rooms-os-hub #1908](https://github.com/koltregaskes/rooms-os-hub/issues/1908).
Codex, T3 Gaming Laptop. Base: `7f54640cfd1cc5856d6677bb4bdef8d33334746f`.

## Prepared change

- `tools.html`: all 43 cards use descriptive copy without dated model specifications,
  comparative rankings, quoted prices, plan entitlements or blanket output-rights
  promises. Each existing provider link remains available for current details.
- `music.html` and `videos.html`: explicitly state that no on-site playback/download
  is available and that external catalogue availability is unverified. Music no
  longer advertises licensable cues as an established entitlement.
- `store.html`: replace ready-to-license language with availability/permission
  checks and link the provider's music terms. The Tech Today card goes to a creator
  profile, so its button now says the track link is unavailable. Remove the
  unverified OfferCatalog/recording schema while retaining page/brand metadata.

These four pages are hand-maintained HTML: the cinematic renderer does not generate
them. `build-seo.py` regenerates their social/structured page metadata from the head.
Reversible default: retain the directory and listing links, withdraw unsupported
sales/price/rights claims, and label unknown availability rather than invent it.
No A-List ranking data, provider account, checkout or publication is enabled.

## Evidence

- `python scripts/build-seo.py --check` and `python scripts/check-seo.py`: passed
  (11 indexable pages, 11 sitemap URLs, 18 gallery images, 135 RSS items).
- `python scripts/check-internal-links.py`: passed, 20 HTML routes.
- `python scripts/validate-site.py`: structural checks passed; existing warning
  remains for 1,519 Midjourney URLs in gallery bookkeeping.
- `python scripts/meta_csp.py`, `python scripts/test-seo.py` and
  `git diff --check`: passed.
- [Bounded external receipt](launch-content-links-2026-11-16.json): 61 unique URLs
  on these four pages; 50 successful HTTP responses, 11 HTTP 403 responses,
  zero confirmed 404/410. Initial sandbox requests were transport-denied;
  the receipt records the subsequent network-enabled pass. No polling or login.
  A 2xx response can be an app shell; it does not prove track identity, playback,
  a working purchase path or a licence. A 403 is unverified, not a broken-link verdict.
- Current primary source: [ElevenLabs Music Terms](https://elevenlabs.io/music-terms),
  read 16 November, showing an update of 9 October 2026. Sections 1.3–1.5, 3.1
  and 4 require checking availability, the applicable plan and output clearance.
  The site therefore makes no blanket commercial-use promise.

## Remaining acceptance / resume

Keep the content checkbox open pending review and final-host checks. No full
browser, screen-reader, performance or live-site acceptance was performed here.
Review the diff, then check each changed page on the approved final artifact.
Confirm the external Suno, YouTube, TikTok and ElevenLabs profiles actually show
the intended work; obtain the exact Tech Today track URL before advertising it as
a direct destination. Recheck the 11 access-denied provider links in an authorised
human browser session; do not create accounts or log in as part of this task.
Any restored price/model/rights claim needs a dated primary-source receipt.

Gallery selection remains Kol's decision. First launch remains after Kol's Korner
and requires Kol's approval. Backend work starts after launch-list acceptance;
this unit does not clear the broader list or change existing operator ownership.
