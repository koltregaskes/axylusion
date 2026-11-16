# Mobile performance receipt — prepared 16 November 2026

Hub: #1908. Recommended reversible default: measure before changing the owner-held gallery collection or inventing responsive media variants.

## Run on a browser-capable host

With the existing Playwright dependency and installed Edge available:

```powershell
node scripts/measure-mobile-performance.mjs --base-url https://axylusion.com > <new-receipt.json>
```

This reads the explicitly named existing approved HTTPS origin; it does not deploy. Run on the final approved host after integration, once per acceptance pass. It creates three cold contexts for each of index.html, gallery.html and news.html: 390x844 mobile emulation, 150ms latency, 200,000 bytes/sec download, 4x CPU slowdown, five seconds observation after load. It records each sample, not a cherry-picked best run. Each must have LCP <=2500ms, CLS <=0.1 and no failed/HTTP-error resources. Any missing LCP/unsupported CLS is unverified, not zero. Browser-launch failures also fail the command. No automated schedule is added.

Receipt includes document transfer size, per-resource transfer/encoded sizes by host/type, and image loaded/loading/srcset/sizes/natural dimensions. Cross-origin sizes with restricted Resource Timing are null/unknown; never add those nulls as zero. Lazy offscreen images may remain unloaded. Sample requests use real fonts/R2 resources rather than blocking them. Navigation/measurement failure yields an unverified sample; require all nine samples and keep any failed run for diagnosis. The JSON has no cookies, storage, response bodies or query-string URLs.

## Verified here

Two Node regression groups cover missing values, boundary LCP/CLS thresholds, broken requests and mixed complete/incomplete samples; syntax check passes. CI runs those offline controls. Main source sizes: index.html 70,132 bytes; gallery.html 2,328,456 bytes; news.html 53,654 bytes. The sampled image tags use lazy loading/async decoding, with no srcset/sizes. These are uncompressed source bytes and sampled attributes, not measured network transfer or whole-gallery responsive acceptance.

## Still unverified

The live nine-sample run was not executed: this checkout has no Playwright/axe installation. No install, account or spending was needed for this preparation. Hosted CI and final-host LCP/CLS are unverified. This lab profile does not represent field Core Web Vitals, screen-reader/keyboard acceptance, post-scroll gallery interaction or all devices. After running, inspect large resource hosts and real image payloads, then propose an owner-approved derivative/pagination change if warranted. Preserve originals, prompts and selected collection; no synthetic image dimensions or compressed variants are claimed. Leave the performance checklist open until the required real measurements and image delivery evidence pass.
