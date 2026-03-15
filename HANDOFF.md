# Axy Lusion Website — Codex Handoff Document

**Last updated:** 15 March 2026
**Branch:** `claude/review-project-docs-Co1Fr` (synced with remote)
**Repo:** `koltregaskes/axylusiondotcom`
**Live site:** GitHub Pages (currently axylusion.com, planned migration to xillusion.com)

---

## Project Overview

Axy Lusion is a portfolio website for Kol Tregaskes showcasing AI-generated art, video, and music. It's a pure **HTML/CSS/JavaScript static site** hosted on **GitHub Pages** — no framework, no build step.

### Site Pages

| Page | File | Purpose |
|------|------|---------|
| Homepage | `index.html` | Hero section, full-screen showcase images, about artist section, back-to-top button |
| Gallery | `gallery.html` | Browsable grid of 1,500+ AI artworks with search, filters, pagination, and modal detail view |
| Videos | `videos.html` | AI video content |
| Music | `music.html` | AI music content |
| News | `news.html` + `news-app.js` | Dynamic news feed from markdown digest files, filtered for creative AI content only |
| Tools | `tools.html` | AI creative tools page (currently hardcoded/stale — needs updating) |
| A-List | `a-list.html` + `a-list/*.html` | Ranked leaderboard of top AI creative tools by category |
| About | `about.html` | Bio, tools used (linked), social connections, contact form |

### Key Files

- **`styles.css`** — Single CSS file for the entire site (~4000 lines)
- **`gallery.js`** — Large file (~1.4MB) containing embedded gallery data as JSON (`embeddedData.items`)
- **`news-app.js`** — News parsing, creative tag filtering, and display logic
- **`news-digests/`** — Directory of markdown digest files (YYYY-MM-DD-digest.md format)
- **`a-list/`** — Subdirectory for A-List category detail pages

---

## Architecture & Key Patterns

### Gallery Data
- Gallery items are embedded in `gallery.js` as `embeddedData.items`
- Each item has: `id`, `name`, `type`, `source`, `model`, `url` (Midjourney link), `cdn_url`, `prompt`, `parameters`, `dimensions`, `created`, `tags`
- **No title display** — Midjourney images don't have titles; the `name` field exists in data but is NOT shown in the UI
- Previously a PLACEHOLDER_DATE filter hid ~1,167 images — this has been removed, all items now show

### News Filtering
- News articles are parsed from markdown digest files at load time
- Creative filtering happens at **parse time** in `parseDigest()` — non-creative articles are dropped before they enter `this.articles`
- Creative tags: `['image', 'video', 'audio', 'creative', '3d']` (note: 'design' was intentionally removed as it caught non-creative governance articles)
- Tag detection uses regex patterns against both title AND summary text
- The user's long-term plan is to add destination tags at the news source level (e.g., `site:creative`) rather than inferring from content

### A-List Rankings
- Data is embedded directly in HTML (no JSON file, no external fetch)
- Meta-scores combine: Artificial Analysis (35%), LM Arena (30%), LLM Stats (15%), Expert Reviews (20%)
- Tooltips on scores use CSS `[data-tooltip]::after` — pure CSS, no JavaScript
- 7 categories: Image Gen, Image Editing, Video, Music, Voice/TTS, 3D, Upscaling
- Only the Image Generation detail sub-page exists (`a-list/image-generation.html`) — the other 6 need to be created from that template

### Contact Form
- Uses Formspree (`https://formspree.io/f/xcontact`) — the `xcontact` placeholder needs to be replaced with an actual Formspree form ID, or migrated to **Supabase** (Kol has a Supabase project set up)

---

## What's Been Done (Recent Sessions)

1. **Homepage showcase** — Removed title/date overlay, fixed dual scrollbar (removed nested scroll container), switched from `background-image: cover` to `<img>` with `object-fit: contain`
2. **Back-to-top button** — Added fixed-position amber circle that appears on scroll
3. **Gallery grid** — Removed broken aspect ratio filter, removed A-Z/Z-A sort options, removed all hover overlay text
4. **Gallery modal** — Restored prompt, Midjourney link, parameters, model, dimensions, tags. Removed title (doesn't exist for MJ images)
5. **Gallery artwork count** — Removed PLACEHOLDER_DATE filter, all 1,500+ artworks now visible
6. **News filtering** — Moved creative filter from display toggle to parse-time exclusion, removed 'design' from creative tags
7. **About page** — Tool names linked to websites, mailto replaced with contact form
8. **A-List page** — New page with 7 categories of ranked AI creative tools, tooltips, one detail sub-page

---

## What Still Needs Doing

### High Priority
- [ ] **Tools page is entirely stale** — All content is hardcoded with fabricated dates (e.g., "February 2026" but content is old). Needs either dynamic content from news digests or a manual rewrite with accurate information
- [ ] **A-List detail sub-pages** — 6 of 7 category pages need to be created from the `a-list/image-generation.html` template (image-editing, video-generation, music-generation, voice-tts, 3d-generation, upscaling)
- [ ] **Contact form backend** — Replace Formspree placeholder with actual form ID, or migrate to Supabase

### Medium Priority
- [ ] **About Artist section** on homepage — Visibility was reported as inconsistent (sometimes not showing)
- [ ] **News tag quality** — The real fix is at the source level: adding destination tags like `site:creative` in the digest files so each website can filter cleanly. This is a cross-project task with the main Kol's Korner site
- [ ] **Domain swap to Xillusion.com** — Kol has the domain on IONOS. Needs: 4 A records (185.199.108-111.153), CNAME www -> koltregaskes.github.io, update CNAME file in repo, update GitHub Pages settings

### Future / Planned
- [ ] **Supabase integration** — Kol has a Supabase project. Plans to use it for: contact form, newsletter signup, and eventually news storage
- [ ] **Multi-site news distribution** — Share news across 3 sites (main, Axy Lusion, AI Resource Hub) with per-site config. Recommended approach: shared JS with `window.NEWS_CONFIG` per site
- [ ] **A-List data automation** — GitHub Action to periodically check leaderboard APIs and flag ranking changes
- [ ] **Oldest-first gallery sort** — Works but items with placeholder date '2026-02-10' cluster together. May need date cleanup in gallery.js data

---

## Design System

- **Colour palette:** Dark theme — `--axyl-black`, `--axyl-gray-*`, `--axyl-cream`, `--axyl-amber` (gold accent)
- **Fonts:** Display font (headings), body font, mono font (code/params) — defined as CSS variables
- **Spacing:** Uses CSS custom properties (`--space-xs` through `--space-xxl`)
- **Consistent nav:** All pages share the same header with nav links and social icons. Navigation order: Gallery, Videos, Music, News, Tools, A-List, About

---

## Related Projects

- **Kol's Korner** (koltregaskes.com) — Main personal site, source of news digests
- **AI Resource Hub** — Technical AI news site (planned, will share news infrastructure)
- **Supabase** — Set up under Kol's Korner, shared across projects

---

## Notes for Codex

- This is a **static site** — no npm, no build, no framework. Just edit HTML/CSS/JS directly
- The `gallery.js` file is ~1.4MB — be careful with full reads
- All navigation changes need to be applied across **all HTML files** (there's no shared component system)
- Profile picture uses `unavatar.io/x/axylusion` with fallback
- The site uses GitHub Pages — push to main branch to deploy
- Kol prefers creative AI content only on this site (not general AI/tech news)
- No titles on gallery images — Midjourney doesn't produce titles
- The user wants to move away from JSON data files toward Supabase for data storage
