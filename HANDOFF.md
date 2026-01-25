# Axy Lusion - Session Handoff

**Last Updated:** 2026-01-25
**Last Commit:** 344fb0a

## Project Overview

**Axy Lusion** is an AI art portfolio website for Kol Tregaskes showcasing Midjourney images, videos, and Suno music.

- **Live:** https://koltregaskes.github.io/axylusion
- **Repo:** github.com/koltregaskes/axylusion
- **Domain:** axylusion.com (currently redirects to Notion - needs DNS update)

## Current State

### What's Working
- Gallery grid with 4 sample images
- Search by keyword (searches name, prompt, tags, model)
- Filter by type (all/images/videos/music)
- Filter by date (year picker)
- Filter by model (e.g., "Midjourney v7")
- Reset filters button
- Modal view with prompt, parameters, source link
- Modal navigation (arrows, keyboard, mouse wheel)
- URL history (back button support)
- Tag-based filtering (click tags in modal)
- Pagination (30 items per page)
- Social links with brand icons

### What's Hidden/Pending
- **Videos:** Hidden from gallery - Midjourney CDN returns 403 Forbidden
- **Music:** Schema ready but no Suno tracks added yet

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
axylusion/
├── index.html          # Main page
├── gallery.js          # All functionality (embedded data + fetch fallback)
├── styles.css          # Dark theme with amber/cream accents
├── data/
│   └── gallery.json    # Source of truth for gallery items
├── ROADMAP.md          # Feature roadmap
└── HANDOFF.md          # This file
```

## Pending Tasks (Priority Order)

### 1. Midjourney Metadata Extraction Script
**Location:** `System/Scripts/midjourney/extract-gallery.py`

Build a Python + Playwright script that:
1. Uses Midjourney session cookie for authentication
2. Scrolls through archive page
3. Extracts: Job ID, prompt, parameters, creation date, CDN URL
4. Groups similar images by prompt similarity (>90% match)
5. Outputs to gallery.json format
6. Handles model version detection (check for --v parameter)

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

1. `344fb0a` - feat: Add reset filters button, fix brand icons, update model to v7
2. `cc71fcb` - feat: Add model field to schema and model filter dropdown
3. `de770c5` - fix: Hide videos, fix nav buttons and dropdown styling
4. `4581179` - feat: Add URL history, date filter, and modal navigation

## Notes for Next Session

1. **Start with:** Building the Midjourney extraction script
2. **Model detection:** Images without --v param after ~late 2024 = v7
3. **Bulk import:** Goal is 500+ images from Midjourney archive
4. **Test locally:** Use `file://` protocol - embedded data in gallery.js works offline
