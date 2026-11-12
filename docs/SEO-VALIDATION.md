# SEO validation, 12 November 2026

Measured from the checked-in public pages before the change and the local build
after it. These are offline output checks, not claims about live indexing.

| Check | Before | After |
| --- | ---: | ---: |
| Indexable pages | 18 | 18 |
| Missing canonical | 0 | 0 |
| Missing Open Graph image | 18 | 0 |
| Missing Open Graph URL | 11 | 0 |
| Missing Twitter image | 18 | 0 |
| Missing JSON-LD | 11 | 0 |
| Sitemap URLs | 18, hand-kept | 18, generated |
| Gallery image sitemap entries | 0 | 18 |
| RSS items | No feed | 136 |

The default social card is a real 1200x630 PNG. News RSS includes the latest 50
non-empty indexed digests plus their source headlines, deduplicated by stable URL.
No build-time dates are substituted for publication dates. `robots.txt` already
allows crawling and points to the correct sitemap. `llms.txt` now uses production
URLs and advertises the feed and sitemap.

Commands run successfully:

```powershell
python scripts/render-cinematic-site.py --page gallery
python scripts/render-a-list.py
python scripts/build-seo.py
python scripts/build-seo.py --check
python scripts/check-seo.py
python scripts/update-news-digest-index.py --check
python scripts/rebuild-homepage-gallery.py --check
python scripts/test-homepage-images.py
python scripts/validate-site.py
```

The SEO gate parses sitemap and RSS XML, validates JSON-LD and image dimensions,
and checks every public page and local RSS target. Isolated corruption checks
confirmed that it rejects a missing canonical, missing social image, invalid
JSON-LD, missing sitemap URL, invalid RSS date, malformed RSS XML and wrong PNG
dimensions.

The gallery data contains 1,519 entries with Midjourney CDN references, which the
existing renderer deliberately excludes. The change reuses 18 durable image URLs
already recorded by the homepage, so those images also render in the gallery and
appear in its sitemap. It does not invent URLs for the remaining entries. The
gallery's VisualArtwork metadata is preserved under ImageGallery.hasPart, with
actual image URLs in ImageGallery.image.

The pre-existing stale A-List snapshot and unavailable shared benchmark-cache
warnings remain. No upstream benchmark repository was read or changed. External
image availability and Search Console ownership were not checked.

The PR was updated with the 12 November digest from main and the feed rebuilt.
The stale-output CI gate correctly caught that newer source input before this
update; the feed count above reflects the final 50-digest window.

Protocol references: [Sitemaps](https://www.sitemaps.org/protocol.html) and
[Google image sitemaps](https://developers.google.com/search/docs/crawling-indexing/sitemaps/image-sitemaps).

Codex (12 Nov burn day, launched by Claude CoS)
