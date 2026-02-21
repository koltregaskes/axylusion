# Axy Lusion - Session Handoff

**Last Updated:** 2026-02-21
**Last Commit:** 4c7056d

## Project Overview

**Axy Lusion** is an AI art portfolio website for Kol Tregaskes showcasing Midjourney images, videos, and Suno music.

- **Live:** https://koltregaskes.github.io/axylusiondotcom
- **Repo:** github.com/koltregaskes/axylusiondotcom
- **Domain:** axylusion.com (currently redirects to Notion - needs DNS update)

## Current State

### What's Working
- Gallery grid with 1,519 published images (Kol's own Midjourney creations)
- Search by keyword (searches name, prompt, tags, model)
- Filter by type (all/images/videos/music)
- Filter by date (year picker)
- Filter by model (e.g., "Midjourney v7")
- Sort options (newest/oldest/name A-Z/Z-A)
- Reset filters button
- Modal view with prompt, parameters, source link
- Modal navigation (arrows, keyboard, mouse wheel)
- Click-to-fullscreen in modal
- URL history (back button support)
- Tag-based filtering (click tags in modal)
- Pagination (24 items per page on gallery.html, 30 on index.html)
- Social links with brand icons (X, Instagram, YouTube, TikTok, Midjourney, Suno)
- Multiple pages: index, gallery, about, music, videos, news
- Decap CMS admin panel (config ready, auth not yet set up)

### CRITICAL: Broken Images
- **ALL images return 403** — `cdn.midjourney.com` blocks external hotlinking
- Images need to be downloaded and re-hosted on Cloudflare R2
- Migration script created at `scripts/migrate-images.py`
- Setup guide at `scripts/SETUP-R2.md`

### What's Hidden/Pending
- **Videos:** Hidden from gallery — Midjourney CDN returns 403 Forbidden
- **Music:** Schema ready but no Suno tracks added yet

### Important: Published Images vs Likes
- **gallery.json** and **gallery.js**: 1,519 items — Kol's own published images
- The database (universal.db) has 6,031 items — these are Midjourney LIKES, not published work
- `generate-gallery-from-db.py` queries `midjourney_likes` table — DO NOT use it to rebuild gallery
- The gallery.json.backup files contain the correct 1,519 published images

## Technical Details

### Schema (gallery.json)
```json
{
  "id": "uuid",
  "name": "Display Name",
  "type": "image|video|music",
  "source": "midjourney|suno|dalle|etc",
  "model": "Midjourney v7",
  "url": "https://midjourney.com/jobs/...",
  "cdn_url": "https://cdn.midjourney.com/.../0_0.png",
  "thumbnail_url": "optional for videos",
  "prompt": "The full prompt text",
  "parameters": "--ar 3:2 --style raw --stylize 200",
  "dimensions": "3:2",
  "created": "2024-12-14",
  "tags": ["portrait", "fantasy", "cinematic"]
}
```

### Model Version Logic
- Images **without** `--v` parameter = latest default model
- As of late 2024, default = **Midjourney v7**
- Need to check Midjourney changelog for when v7 became default
- Images with explicit `--v 6.1` = Midjourney v6.1

### Files Structure
```
axylusiondotcom/
├── index.html              # Homepage with hero carousel
├── gallery.html            # Full gallery page
├── about.html              # About page
├── music.html              # Music page
├── videos.html             # Videos page
├── news.html               # News page
├── gallery.js              # Gallery functionality (1.3MB, embedded data)
├── gallery-fixes.js        # Gallery bug fixes
├── gallery-modal-fixes.js  # Modal UX improvements
├── data-loader.js          # Shared data loader for all pages
├── styles.css              # Dark theme with amber/cream accents
├── scripts/
│   ├── migrate-images.py   # Image migration tool (CDN → R2)
│   └── SETUP-R2.md         # Cloudflare R2 setup guide
├── data/
│   └── gallery.json        # Source of truth (1,519 published items)
├── admin/
│   ├── index.html          # Decap CMS admin panel
│   └── config.yml          # CMS configuration
├── content/
│   ├── about.md            # About page content (CMS-editable)
│   └── news/               # News articles (CMS-editable)
├── images/uploads/         # CMS image uploads
├── generate-gallery-from-db.py  # Rebuild gallery.json from database
├── sync-dates-from-db.py   # Sync creation dates from database
├── check-id-overlap.py     # Check for duplicate IDs
├── ROADMAP.md              # Feature roadmap
├── SPEC.md                 # Design specification
├── SESSION-NOTES.md        # Previous session notes
├── SESSION-PROMPT.md       # Handoff prompt for new sessions
├── ADMIN-LOGIN.md          # Admin panel documentation
└── HANDOFF.md              # This file
```

## Pending Tasks (Priority Order)

### 1. Image Hosting Migration (BLOCKING)
All 1,519 images show broken (403 Forbidden from cdn.midjourney.com).
**Solution:** Migrate to Cloudflare R2 (10GB free, no bandwidth charges).
- Script ready: `scripts/migrate-images.py`
- Setup guide: `scripts/SETUP-R2.md`
- Steps: Download images from Midjourney → Upload to R2 → Update URLs
- See setup guide for detailed instructions

### 2. Image Grouping/Bundling Feature
Similar prompts should be bundled into collections:
- Homepage shows one "cover" image with "×3" badge
- Modal shows thumbnail carousel for variations
- Schema designed in plan file (see collection type)

### 3. Model Info Pages
Create pages documenting each AI model:
- Midjourney v7: capabilities, release date, changelog
- Future: v6.1, v6, Suno, DALL-E, etc.
- Include sample images from that model
- Link to official docs/changelogs

### 4. AI News Page
Expand site beyond gallery:
- AI news focused on content creation tools (image, video, music)
- Integrate with News Gatherer project
- Could have "listen to news" audio feature
- Static info pages for various models

### 5. Video Hosting Solution
Options to resolve 403 errors:
- Google Drive (15GB free)
- Cloudflare R2 (10GB free, scalable)
- Self-hosted on GitHub (limited ~1GB)

### 6. DNS Migration
Move axylusion.com from Notion to GitHub Pages:
1. Add CNAME file with `axylusion.com`
2. Update DNS: A record → GitHub Pages IPs
3. CNAME www → koltregaskes.github.io

## Social Media Strategy

Documented in plan file. Key points:
- @Axylusion accounts are new, need growth
- Cross-promote from @KolTregaskes
- Instagram: focus for visual AI art
- TikTok: short-form video clips with Suno music
- YouTube: longer compilations, visualisers

## Plan File Location

Full strategy documented at:
`C:\Users\kolin\.claude\plans\kind-gathering-popcorn.md`

## Recent Commits

1. `4c7056d` - Add session handoff prompt for new Claude Code sessions
2. `8b796f5` - Remove CNAME - not ready for custom domain yet
3. `89cb48d` - Fix: Add gallery.js script tag and update TikTok icon in footer
4. `4e9aa93` - Fix: Restore working homepage/gallery + standardize social icons
5. `9607777` - Fixed gallery data loading with shared data-loader.js
6. `c1dd86e` - Modal UX improvements (transitions, fullscreen, scroll detection)
7. `a9cc2b9` - Gallery rebuild from database (creation dates fixed, 6,031 items)

## Notes for Next Session

1. **IMAGES ARE BROKEN** — cdn.midjourney.com returns 403 on all images. Must complete R2 migration first.
2. **Gallery has 1,519 published images** — NOT the 6,031 likes in the database. gallery.js has the correct data embedded.
3. **data-loader.js is unused** — no HTML page loads it. Both index.html and gallery.html use gallery.js with embedded data.
4. **gallery-fixes.js and gallery-modal-fixes.js** — exist but not loaded by any page. May be dead code from earlier iterations.
5. **News page:** Has "coming soon" placeholder. Needs proper content and design.
6. **DNS:** axylusion.com still redirects to Notion — needs GitHub Pages migration.
7. **Test locally:** Use `file://` protocol — gallery.js has embedded data, no server needed.
