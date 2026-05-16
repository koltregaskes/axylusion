# Axy Lusion — Agent Readiness

**Status:** DRAFT — awaiting Kol's sign-off. Not yet committed.
**Last updated:** 2026-05-16
**Estate-wide policy:** `W:\Websites\AGENT-READINESS-ESTATE.md`
**Repo:** `W:\Websites\sites\axylusion`
**Domain:** axylusion.com
**Stack:** Static HTML + vanilla CSS/JS
**Existing bio (from `about.html`):** *"Kol Tregaskes — AI artist and creative exploring the intersection of technology and imagination through Midjourney, Suno, and other AI tools."*

---

## ⚠️ Interlock: gallery image migration

The Midjourney CDN returns 403 on the published gallery images. `MIDJOURNEY-PUBLISHED-GALLERY-MIGRATION-PLAN.md` already exists in the repo for moving images to Cloudflare R2.

**`ImageGallery` and `VisualArtwork` schema cannot ship until images are live.** Schema pointing at broken URLs is worse than no schema — Google may downrank a site whose `ImageObject.contentUrl` 404s/403s.

Codex's order of operations:
1. Run the R2 migration first (see runbook at estate root: `CLOUDFLARE-R2-ASSET-MIGRATION-RUNBOOK.md`)
2. Validate gallery images render
3. Then ship the gallery JSON-LD per this doc

If Kol decides to ship schema work *now* with placeholders, the schema for the gallery must point at the post-migration R2 URLs even before they're live, and the migration must follow immediately. Don't ship a half-state.

---

## 1. Schema strategy

### 1.1 Home page (`index.html`)

**`Organization`** for the brand:

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://axylusion.com/#organization",
  "name": "Axy Lusion",
  "alternateName": "Axylusion",
  "url": "https://axylusion.com",
  "logo": "https://axylusion.com/favicon.svg",
  "description": "AI art portfolio and creative tool rankings. Kol Tregaskes — AI artist exploring the intersection of technology and imagination through Midjourney, Suno, and other AI tools.",
  "founder": { "@id": "https://koltregaskes.com/#person-kol" },
  "sameAs": ["https://x.com/Axylusion"],
  "parentOrganization": { "@id": "https://koltregaskes.com/#organization" }
}
```

**`WebSite`**:

```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "@id": "https://axylusion.com/#website",
  "name": "Axy Lusion",
  "url": "https://axylusion.com",
  "publisher": { "@id": "https://axylusion.com/#organization" }
}
```

### 1.2 Gallery page (`gallery.html`)

**`ImageGallery`** with one `VisualArtwork` per image. Codex emits this from `data/` JSON or wherever the gallery manifest lives.

```json
{
  "@context": "https://schema.org",
  "@type": "ImageGallery",
  "@id": "https://axylusion.com/gallery.html#gallery",
  "name": "Axy Lusion Gallery",
  "description": "AI-generated artwork by Kol Tregaskes",
  "image": [
    {
      "@type": "VisualArtwork",
      "@id": "https://axylusion.com/gallery.html#artwork-<slug>",
      "name": "<artwork title>",
      "description": "<artwork description>",
      "creator": { "@id": "https://koltregaskes.com/#person-kol" },
      "artMedium": "AI image generation (Midjourney)",
      "artform": "Digital art",
      "dateCreated": "<YYYY-MM-DD>",
      "image": "<R2 URL — post-migration>",
      "thumbnailUrl": "<R2 thumbnail URL>",
      "license": "<license URL — Kol to confirm>",
      "copyrightHolder": { "@id": "https://koltregaskes.com/#person-kol" },
      "isPartOf": { "@id": "https://axylusion.com/gallery.html#gallery" }
    }
    // ... one per artwork
  ]
}
```

**Kol's call:** what licence applies to the gallery? Default if not specified: "All rights reserved" (omit `license`).

### 1.3 A-List pages (`a-list.html`, `a-list/*.html`)

Each A-List page ranks AI creative tools (image-gen, video-gen, 3d, music, voice-tts, upscaling, image-editing). These are `ItemList` of `SoftwareApplication`:

```json
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "@id": "https://axylusion.com/a-list/image-generation.html#list",
  "name": "A-List: Image Generation Tools",
  "description": "Top AI image generation tools, ranked by Axy Lusion.",
  "numberOfItems": 12,
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "item": {
        "@type": "SoftwareApplication",
        "name": "Midjourney",
        "url": "https://www.midjourney.com",
        "applicationCategory": "DesignApplication",
        "operatingSystem": "Web"
      }
    }
    // ...
  ]
}
```

Plus a wrapping `ReviewPage` if Axy Lusion is opining on the rankings:

```json
{
  "@context": "https://schema.org",
  "@type": "Review",
  "itemReviewed": { "@id": "https://axylusion.com/a-list/image-generation.html#list" },
  "author": { "@id": "https://koltregaskes.com/#person-kol" },
  "reviewBody": "<rationale for ranking>"
}
```

### 1.4 Blog (`blog.html`, `blog-welcome.html`)

If blog posts are individual pages, `Article` each. If `blog.html` is a paginated index, use `Blog` schema with embedded `BlogPosting` items.

```json
{
  "@context": "https://schema.org",
  "@type": "Blog",
  "@id": "https://axylusion.com/blog.html#blog",
  "name": "Axy Lusion Blog",
  "publisher": { "@id": "https://axylusion.com/#organization" },
  "blogPost": [ /* BlogPosting array */ ]
}
```

### 1.5 About page (`about.html`)

`AboutPage` with `Person` reference (Kol).

### 1.6 Implementation pattern (for Codex)

Static HTML, so:
- Add JSON-LD as inline `<script type="application/ld+json">` in each page's `<head>`
- Gallery data is in `data/` (per the repo's existing `data-loader.js`) — extend the loader to also emit JSON-LD when rendering the gallery
- One canonical Organization + WebSite block at top of each page (or shared via build step). Don't duplicate the Person block per page — reference by `@id`.

---

## 2. Robots.txt and sitemap

### Robots.txt

Currently: no `robots.txt` visible — verify. If missing, add the estate baseline. If present, align.

### Sitemap.xml

Verify:
- Lists `index.html`, `about.html`, `gallery.html`, `blog.html`, `blog-welcome.html`, `a-list.html`, all `a-list/*.html` (7 sub-pages)
- Includes individual artwork pages if any exist
- `lastmod` reflects last gallery update (so AI agents see fresh content signals after R2 migration)

---

## 3. Browser-agent UX audit (web.dev spec)

Gallery interactivity (modal, fixes scripts visible in repo) needs audit:

- `gallery.js`, `gallery-fixes.js`, `gallery-modal-fixes.js` may construct interactive elements dynamically — Codex must confirm constructed elements use `<button>` / `<a>`, not styled `<div>` / `<span>`.
- Gallery modal accessibility: `role="dialog"`, `aria-modal="true"`, focus trap, escape to close. Critical for browser agents that take screenshots.
- A-List pages: rank cards must be `<a>` or `<button>` if clickable.

Form check: `admin/` directory present — verify admin forms have `<label for=…>`. (Admin probably gated behind auth, but the markup quality still matters for accessibility / browser agents the admin uses.)

---

## 4. Content cadence — non-commodity check

A-List rankings are exactly the kind of content Google calls out as *commodity* IF they're just "here are 10 tools" with no opinion. Axy Lusion's value lies in Kol's actual experience with each tool:

- Each A-List entry should include a `Review.reviewBody` with Kol's first-hand take ("Why I switched from Midjourney v6 to v7 for portraits...")
- Without first-person commentary, the ranking is commodity content
- Recommend Codex flags any A-List entry where `reviewBody` is empty or boilerplate

Gallery is unique by definition (one-of-a-kind generated images) — much less risk.

Blog: depends on content. Codex flags posts that read like generic AI-art tutorials without Kol's process / mistakes / iterations.

---

## 5. Crawl budget

Likely small (a-list/ has 7 pages, plus home, about, gallery, blog). No concerns.

---

## 6. Open items and dependencies

- **R2 migration must complete first** (see warning at top of this doc).
- **License decision** for gallery images — Kol's call.
- **A-List `reviewBody` content** — if rankings exist without rationale text, schema fidelity is poor. Editorial backfill needed.
- **Admin section schema** — typically excluded from sitemap + `noindex`'d. Codex confirms.

---

## 7. Definition of done for Codex

Phase 1 — Pre-migration (no images live yet):

- [ ] `Organization` + `WebSite` JSON-LD on home + every page (referenced by `@id`)
- [ ] `AboutPage` on about
- [ ] `ItemList` of `SoftwareApplication` on each A-List page
- [ ] `Blog` or `Article` on blog pages
- [ ] `BreadcrumbList` on deep pages
- [ ] `robots.txt` matches estate baseline
- [ ] `audit-agent-ready.py` passes on all pages except gallery
- [ ] Gallery page returns a schema STUB pointing to "coming soon" (or 503), not broken images

Phase 2 — Post-migration (after R2 migration):

- [ ] `ImageGallery` JSON-LD on gallery with all `VisualArtwork` entries
- [ ] All image URLs are R2 URLs and resolve
- [ ] Gallery page passes `audit-agent-ready.py`
