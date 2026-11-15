# Hosting and security headers

## What protects the site today

The supplied hosting arrangement is GitHub Pages from the repository root,
with `CNAME` set to `axylusion.com` and Cloudflare used for DNS. The repository
cannot prove the current Pages settings, Cloudflare proxy state or live headers.
Cloudflare DNS alone does not add response headers. No hosting or account
settings are changed by this work.

GitHub Pages ignores `_headers`. It is retained as a generated compatibility
mirror, labelled unused, because local validation previously required it and
CSP tests read it. Those CSP tests now read the intended policy directly.
Neither `_headers` nor `cloudflare-response-headers.json` is applied by a
workflow in this repository. The JSON is an approval-ready proposal, not
provider configuration readback. Its `enabled: true` would enable the rule
when applied; merely checking in this file enables nothing.

All 20 checked-in HTML pages contain an enforced meta CSP before scripts.
The meta policy is derived from the JSON response CSP, omitting only
`frame-ancestors`, which browsers ignore in meta. It restricts resource sources,
blocks ordinary inline scripts and plugins, restricts forms and base URLs, and
requests HTTPS upgrades. Most pages also declare a referrer meta policy;
that is not evidence of a Referrer-Policy response header on every route.
A meta CSP cannot supply HSTS, MIME sniffing protection, Permissions-Policy,
X-Frame-Options or frame-ancestors protection. HTTPS availability, redirects
and any headers supplied by the host must be verified separately.

The existing CSP intentionally retains inline styles and broad HTTPS image and
media sources. Its schema nonce is fixed in public static HTML, not a random
per-response nonce; it must not be described as protection against an attacker
who can inject markup using that value. This change preserves the existing
meta policy rather than claiming a complete XSS defence or a browser audit.

Read-only HEAD requests to `/`, `/about.html` and `/gallery.html` on
https://axylusion.com/ failed to connect during this work. No HTTP status or
response headers were received. Actual deployed content and protections remain
**unverified**, not confirmed missing or present.

## Intended policy and previous disagreements

`cloudflare-response-headers.json` is the one source of intended header values.
`python -B scripts/meta_csp.py --write` regenerates the unused `_headers` mirror
and every public HTML meta CSP after an approved source edit. Update the JSON
example below to match as well. `python -B scripts/meta_csp.py` checks all three
representations and the copy-paste example without changing files.

Before this fix, the unused `_headers` requested a year of HSTS with both
includeSubDomains and preload; the Cloudflare proposal requested a year only.
The proposal also used a weaker report-only CSP, permitted inline scripts and
Suno frames, omitted form-action and HTTPS upgrades, omitted data/blob media
and data fonts, and allowed self framing. The meta CSP instead came from
`_headers` and omitted frame-ancestors. Permissions-Policy existed only in
`_headers`. X-Frame-Options SAMEORIGIN conflicted with its frame-ancestors none.

The proposal now preserves the enforced meta policy as the response CSP,
adds frame-ancestors none, aligns X-Frame-Options to DENY and includes the
existing Permissions-Policy. It requests `max-age=31536000` only for HSTS.
There is no includeSubDomains directive or preload request. Do not submit the
domain to a preload list. Preloading or changing the HSTS scope needs a new
explicit decision from Kol. Even plain HSTS is remembered by clients for its
max-age; disabling a rule does not instantly clear cached HSTS.

## Exact change requiring Kol's yes

Recommendation: retain GitHub Pages and approve adding **one HTTP Response
Header Modification Transform Rule** to the existing Cloudflare zone, in the
`http_response_headers_transform` phase, using the expression and six Set
operations in the JSON below. Apply only after the owner confirms the site is
already proxied through Cloudflare and eligible for response header transforms.
If it is DNS-only, stop: proxy activation is a separate network change requiring
Kol's approval and a site, TLS and mail impact check. A move to Cloudflare Pages
or a Worker is not included in this proposal.

In Cloudflare's existing zone, open Rules / Transform Rules / Modify Response
Header (the dashboard wording may vary). Add a rule named `Axy Lusion security
headers`, use the exact `expression` below, and add each `headers` entry with
operation **Set static** and its literal value. Confirm no existing rule or
managed header feature overrides or duplicates these headers. Save the prior
rule state for rollback and review this completed change with Kol before
saving/deploying it. No API credentials or account connection are needed to
review this proposal.

This is the intended ruleset fragment. The single member of `rules` is the rule
object; preserve all other zone rules if an authorised owner uses an API rather
than the dashboard. Do not replace the zone's entire ruleset with this fragment.

```json
{
  "description": "PROPOSED ONLY: Axy Lusion response headers; requires Kol's approval before application",
  "rules": [
    {
      "expression": "(http.host eq \"axylusion.com\" or http.host eq \"www.axylusion.com\")",
      "action": "rewrite",
      "action_parameters": {
        "headers": {
          "X-Content-Type-Options": {
            "operation": "set",
            "value": "nosniff"
          },
          "X-Frame-Options": {
            "operation": "set",
            "value": "DENY"
          },
          "Referrer-Policy": {
            "operation": "set",
            "value": "strict-origin-when-cross-origin"
          },
          "Strict-Transport-Security": {
            "operation": "set",
            "value": "max-age=31536000"
          },
          "Permissions-Policy": {
            "operation": "set",
            "value": "accelerometer=(), autoplay=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
          },
          "Content-Security-Policy": {
            "operation": "set",
            "value": "default-src 'self'; img-src 'self' data: https:; media-src 'self' https: data: blob:; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com data:; script-src 'self' 'nonce-axylusion-cinematic-schema'; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com; frame-ancestors 'none'; upgrade-insecure-requests"
          }
        }
      },
      "enabled": true
    }
  ]
}
```

The proposed response CSP is **enforced**, not report-only. This matches the
existing enforced meta CSP for resources and adds real framing protection.
Report-only CSP would not enforce frame-ancestors. This exact proposal and
its production behaviour still require Kol's approval and subsequent readback.

## Verify after the authorised change

Run these read-only commands in PowerShell, using normal TLS verification:

```powershell
curl.exe --silent --show-error --head --max-time 30 https://axylusion.com/
curl.exe --silent --show-error --head --max-time 30 https://axylusion.com/about.html
curl.exe --silent --show-error --head --max-time 30 https://axylusion.com/gallery.html
curl.exe --silent --show-error --head --max-time 30 https://axylusion.com/a-list/image-generation.html
curl.exe --silent --show-error --head --max-time 30 https://www.axylusion.com/
```

Record the status, Location (if present), header names/values and UTC capture
time. Compare the six response headers on successful content responses exactly
against the JSON, ignoring header-name case and harmless whitespace. Confirm a
single enforced Content-Security-Policy including frame-ancestors none, DENY
framing, nosniff, the specified referrer and permissions policies, and HSTS
without includeSubDomains/preload. Record redirect responses separately. If a
redirect points outside the approved hosts, review its destination before any
follow-up request. Do not treat a redirect alone as a content-header pass.
A connection error, blank output, missing header or unexpected duplicate fails
acceptance. A Cloudflare Server header alone does not prove this rule applied.

For a representative page, also use GET and inspect its real bytes:

```powershell
curl.exe --silent --show-error --max-time 30 --dump-header response-headers.txt --output response-body.html https://axylusion.com/about.html
```

Confirm that the GET has the same intended headers and its HTML contains the
matching meta CSP before scripts. Check real font/media loading and navigation
in a browser and test framing is blocked. The existing offline/browser contract
tests are preparation, not evidence that Cloudflare deployed the rule. Recheck
the former GitHub project URL separately during final-host acceptance; a rule
scoped to axylusion.com cannot protect github.io.

For rollback, disable only the newly added rule after the authorised owner
reviews the failure; retain its previous state and record fresh readback.
If HSTS must be unwound, an approved replacement with max-age=0 on HTTPS helps
clients that revisit; clients that do not revisit retain the previous expiry.
Do not silently change proxy, DNS, hosting or unrelated rules as a workaround.
