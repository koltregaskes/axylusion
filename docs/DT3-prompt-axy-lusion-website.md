# Prompt 12: Axy Lusion — AI Art Portfolio Website

**Target:** Google Gemini 3 Deep Think (free tier)
**Purpose:** Fix critical bugs, add a news page, and establish permanent image hosting for the Axy Lusion AI art portfolio
**Created:** 2026-02-19
**Part of:** Workspace 2.0 — Website Management Hub

---

## 1. `<role>` - Define Identity and Expertise

You are a senior front-end web developer and creative portfolio specialist with deep expertise in:
- **Static portfolio websites** — lightweight, fast, visually striking showcase sites for digital artists
- **Image hosting & CDN strategy** — permanent, reliable image delivery for AI-generated artwork at scale (6,000+ items)
- **Vanilla HTML/CSS/JS** — framework-free development for maximum performance and simplicity
- **Dark-mode premium aesthetics** — luxury gallery design with rich blacks, warm amber accents, ambient glow effects
- **Gallery UX** — masonry layouts, lazy loading, modal viewers, filtering, search, infinite scroll
- **Responsive design** — full-bleed hero sections, mobile-optimised galleries, touch-friendly navigation
- **SEO for visual content** — Open Graph images, structured data, image sitemaps, descriptive alt text
- **News/blog integration** — adding article feeds to existing static sites using build-time generation
- **GitHub Pages deployment** — static hosting, custom domains, automated builds
- **AI creative tools ecosystem** — Midjourney, Suno, Runway, Kling, Luma, Stable Diffusion

You write clean, semantic HTML with well-organised CSS custom properties. Every change preserves the existing premium aesthetic.

---

## 2. `<constraints>` - Hard Requirements

### Technical Stack (Existing — Do Not Change)
- **Language:** Vanilla HTML5, CSS3, JavaScript (ES6+)
- **Styling:** Custom CSS with CSS variables (design tokens in `:root`)
- **Fonts:** Inter (display/body), JetBrains Mono (monospace)
- **Deployment:** GitHub Pages
- **No build tools:** No webpack, no bundlers, no npm — pure static files
- **No frameworks:** No React, Vue, or Angular — vanilla JS only

### Design Tokens (Existing — Preserve)
```css
:root {
    --axyl-amber: #c4851a;
    --axyl-amber-light: #d4a03a;
    --axyl-amber-dark: #8a5d12;
    --axyl-amber-glow: rgba(196, 133, 26, 0.4);
    --axyl-cream: #f5e6c8;
    --axyl-white: #fafafa;
    --axyl-black: #0a0a0a;
    --axyl-dark: #111111;
    --axyl-gray-900: #1a1a1a;
    --axyl-gray-800: #222222;
    --axyl-gray-700: #333333;
    --axyl-gray-600: #444444;
    --axyl-gray-500: #666666;
    --axyl-gray-400: #888888;
    --axyl-gray-300: #aaaaaa;
}
```

### Absolute Rules
1. **Dark mode only** — no light mode, no toggle. The premium black gallery aesthetic is the brand.
2. **Amber accent only** — `#c4851a` is the brand colour. No new accent colours.
3. **No breaking changes** — existing gallery, about, videos, music pages must continue to work.
4. **Performance first** — site has 6,000+ gallery items. Lazy loading, pagination, and efficient DOM are mandatory.
5. **Mobile-first responsive** — galleries must work on phones. Touch-friendly modal viewer.
6. **Accessibility** — all images must have alt text. Keyboard navigation for gallery modal.
7. **UK English** throughout all copy and comments.
8. **Social links order** — X, Instagram, YouTube, TikTok, Midjourney, Suno (consistent across all pages).

---

## 3. `<architecture>` - System Design

### Current Site Structure
```
axylusion.com/
├── index.html          ← Homepage (hero carousel + gallery + about)
├── gallery.html        ← Full gallery with search/filter
├── videos.html         ← Video showcase (coming soon)
├── music.html          ← Music showcase (coming soon)
├── news.html           ← News page (CURRENTLY COMING SOON PLACEHOLDER)
├── about.html          ← About the artist
├── styles.css          ← All design tokens + component styles
├── gallery.js          ← Gallery data (6,031 items as JSON) + interactivity
└── assets/             ← Static assets (favicon, etc.)
```

### Navigation Structure
```
Logo: "Axy Lusion"
Nav:  Gallery | Videos | Music | News | About
Social: X | Instagram | YouTube | TikTok | Midjourney | Suno
Footer: Brand + tagline + social + copyright → links to koltregaskes.com
```

### Bug 1: CDN Image Hosting (CRITICAL)
**Problem:** Gallery items reference Midjourney CDN URLs like `https://cdn.midjourney.com/...`. These URLs expire and return **403 Forbidden**, breaking hero images and gallery thumbnails across the entire site.

**Impact:** The visual portfolio is broken — the core purpose of the site.

**Solution Architecture:**
```
Current (broken):
  gallery.js → cdn.midjourney.com/uuid/... → 403 EXPIRED

Proposed (permanent):
  gallery.js → permanent-host.com/gallery/filename.webp → 200 OK
```

**Requirements for permanent hosting:**
- Must handle 6,000+ images (likely 50-100GB total)
- Must serve fast globally (CDN-backed)
- Must support WebP format for size optimisation
- Must be cost-effective (free tier or very low cost)
- Must work with GitHub Pages (no server-side processing)

**Recommended options (evaluate and choose one):**
1. **Cloudflare R2** — S3-compatible, zero egress fees, free tier: 10GB storage + 10M reads/month
2. **Vercel Blob** — simple API, integrates with Vercel hosting, free tier: 1GB
3. **GitHub LFS + raw.githubusercontent.com** — built into repo, but 1GB limit
4. **Bunny CDN + Bunny Storage** — cheap (€0.005/GB stored, €0.01/GB served), pull zones globally
5. **Self-hosted on NAS via Tailscale** — free but limited to home network speed

**Migration script needed:** Download all valid images from Midjourney CDN before they expire, convert to WebP, upload to chosen host, update all references in gallery.js.

### Bug 2: Gallery Creation Dates
**Problem:** Gallery items display incorrect creation dates.

**Solution:** Audit the `gallery.js` data — each item has a `date` field. Cross-reference with actual creation dates from Midjourney usage logs or file metadata. Provide a correction script.

### Feature: News Page
**Problem:** `news.html` is currently a "Coming Soon" placeholder. Needs to become a real news feed filtered for AI creative tools.

**Architecture:**
```
News Data Pipeline:
  [LLATOS News Hub agent gathers AI news daily]
       ↓ filters for: Midjourney, Suno, Runway, Kling, Luma,
         Stable Diffusion, Pika, AI art, AI music, AI video
       ↓
  [news-data.json] — static JSON file regenerated daily
       ↓
  [news.html] — renders articles client-side from JSON
       ↓
  [GitHub Actions] — daily rebuild pushes updated JSON
```

**News page requirements:**
- Display articles as cards: title, summary, source, date, category tag
- Filter by category: Art, Video, Music, Tools, General
- Sort by: newest first (default), can toggle oldest first
- Pagination: 20 articles per page
- Visual style: matches existing gallery card aesthetic (dark cards, amber accents on hover)
- Source attribution: link to original article
- Mobile responsive: single column on mobile, 2-column on tablet, 3-column on desktop

**Same pattern as koltregaskes.com news page** — the main personal website already has a working news page using a similar static JSON → HTML rendering approach. Replicate that pattern but filtered for creative AI tools only.

---

## 4. `<schema>` - Data Structures

### Gallery Item (Existing — gallery.js)
```javascript
{
    "id": "unique-string",
    "title": "Artwork Title",
    "description": "Description of the piece",
    "image": "https://cdn.midjourney.com/uuid/0_0.png",  // BROKEN - needs migration
    "thumbnail": "https://cdn.midjourney.com/uuid/0_0_384_N.webp",
    "type": "image",          // image | video | music
    "model": "Midjourney v6", // AI model used
    "date": "2025-03-15",     // Creation date (BUGGY)
    "tags": ["portrait", "cyberpunk", "cinematic"],
    "featured": false
}
```

### Gallery Item (After Migration)
```javascript
{
    "id": "unique-string",
    "title": "Artwork Title",
    "description": "Description of the piece",
    "image": "https://r2.axylusion.com/gallery/unique-string.webp",    // PERMANENT
    "thumbnail": "https://r2.axylusion.com/thumbs/unique-string.webp", // PERMANENT
    "type": "image",
    "model": "Midjourney v6",
    "date": "2025-03-15",     // CORRECTED
    "tags": ["portrait", "cyberpunk", "cinematic"],
    "featured": false
}
```

### News Article (New)
```javascript
{
    "id": "news-2026-02-19-midjourney-v7",
    "title": "Midjourney V7 Announced with Real-Time Generation",
    "summary": "Midjourney announces V7 with significant improvements...",
    "source": "Midjourney Blog",
    "sourceUrl": "https://midjourney.com/blog/v7",
    "date": "2026-02-19",
    "category": "art",        // art | video | music | tools | general
    "tags": ["midjourney", "image-generation"],
    "imageUrl": null           // optional hero image
}
```

---

## 5. `<existing-code>` - Current Implementation

### styles.css — Design Tokens (First 62 Lines)
```css
:root {
    --axyl-amber: #c4851a;
    --axyl-amber-light: #d4a03a;
    --axyl-amber-dark: #8a5d12;
    --axyl-amber-glow: rgba(196, 133, 26, 0.4);
    --axyl-cream: #f5e6c8;
    --axyl-white: #fafafa;
    --axyl-black: #0a0a0a;
    --axyl-dark: #111111;
    --axyl-gray-900: #1a1a1a;
    --axyl-gray-800: #222222;
    --axyl-gray-700: #333333;
    --axyl-gray-600: #444444;
    --axyl-gray-500: #666666;
    --axyl-gray-400: #888888;
    --axyl-gray-300: #aaaaaa;
    --font-display: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-body: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
    --space-xs: 0.25rem;
    --space-sm: 0.5rem;
    --space-md: 1rem;
    --space-lg: 1.5rem;
    --space-xl: 2rem;
    --space-2xl: 3rem;
    --space-3xl: 4rem;
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --radius-xl: 16px;
    --radius-full: 9999px;
    --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-base: 250ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-slow: 400ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-spring: 500ms cubic-bezier(0.175, 0.885, 0.32, 1.275);
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
    --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
    --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.5);
    --shadow-xl: 0 16px 48px rgba(0, 0, 0, 0.6);
    --shadow-glow: 0 0 40px var(--axyl-amber-glow);
}
```

### news.html — Current Placeholder
```html
<section class="page-header">
    <div class="page-header-content">
        <h1 class="page-title">AI Tools News</h1>
        <p class="page-subtitle">Updates from Midjourney, Suno, Runway, and the AI creative world</p>
    </div>
</section>
<main class="coming-soon-section">
    <div class="coming-soon-content">
        <h2>Coming Soon</h2>
        <p>Daily news and updates about AI creative tools...</p>
        <div class="news-topics">
            <span class="topic-tag">Midjourney</span>
            <span class="topic-tag">Suno</span>
            <span class="topic-tag">Runway ML</span>
            <span class="topic-tag">Pika Labs</span>
            <span class="topic-tag">Stable Diffusion</span>
            <span class="topic-tag">Kling</span>
            <span class="topic-tag">Luma</span>
            <span class="topic-tag">AI Tutorials</span>
        </div>
    </div>
</main>
```

### index.html — Hero Section Structure
```html
<section class="hero" id="hero">
    <div class="hero-background">
        <div class="hero-image" id="hero-image"></div>
        <div class="hero-overlay"></div>
    </div>
    <div class="hero-content">
        <h1 class="hero-title">
            <span class="hero-title-main">Axy Lusion</span>
            <span class="hero-title-sub">AI Art, Video & Music</span>
        </h1>
        <p class="hero-tagline">Exploring the intersection of creativity and artificial intelligence</p>
        <div class="hero-cta">
            <a href="#gallery" class="cta-button primary">Explore Gallery</a>
            <a href="about.html" class="cta-button secondary">About the Artist</a>
        </div>
    </div>
    <div class="hero-featured"><!-- carousel nav --></div>
    <div class="hero-scroll-hint"><!-- scroll indicator --></div>
</section>
```

---

## 6. `<design-system>` - Visual Language

### Existing Aesthetic (Preserve)
The site has a **premium AI art gallery** feel — rich blacks, warm amber accents, ambient glow gradients. Think high-end photography portfolio meets cyberpunk neon restraint.

**Key visual elements:**
- **Ambient body gradient** — subtle radial amber glow behind content
- **Glassmorphism** — `backdrop-filter: blur()` on overlays and modals
- **Hero carousel** — full-viewport background images with overlay + featured info
- **Smart header** — appears on scroll-up, hides during hero section
- **Card hover states** — subtle lift + amber border glow + scale
- **Gallery modal** — full-screen image viewer with metadata sidebar

### News Page Design (New — Must Match)
- **Article cards:** Same visual weight as gallery cards. Dark surface (`--axyl-gray-900`), subtle border (`--axyl-gray-700`), amber accent on hover.
- **Category badges:** Pill-shaped, text colour matches category. Art=amber, Video=blue (#4285F4), Music=green (#10A37F), Tools=purple (#9b59b6), General=gray.
- **Date formatting:** Relative for recent ("2 hours ago"), absolute for older ("15 Feb 2026"). UK date format always.
- **Source attribution:** Small text below title linking to original.
- **Empty state:** If no news loaded, show elegant placeholder (not a broken page).

### Typography Scale (Existing)
```
Page title:     clamp(3rem, 10vw, 6rem)  font-weight: 700  font-display
Section heading: 2rem                     font-weight: 600  font-display
Card title:     1.125rem                  font-weight: 600  font-body
Body text:      1rem                      font-weight: 400  font-body
Meta/dates:     0.875rem                  font-weight: 400  font-mono
```

---

## 7. `<task>` - Deliverables

### Deliverable 1: Image Hosting Migration Plan
Produce a detailed migration strategy document covering:
1. **Chosen hosting solution** with justification (compare Cloudflare R2, Bunny CDN, and Vercel Blob)
2. **Migration script** (Python or Node.js) that:
   - Reads all image URLs from gallery.js
   - Downloads each image (with retry logic for 403s — some may already be expired)
   - Converts to WebP format (both full-size and thumbnail)
   - Uploads to chosen hosting
   - Generates updated gallery.js with new URLs
3. **Fallback strategy** for images that are already expired (403)
4. **Cost estimate** per month for 6,000+ images
5. **GitHub Actions workflow** to handle future uploads

### Deliverable 2: Gallery Date Correction Script
Produce a script that:
1. Reads all items from gallery.js
2. Identifies items with suspicious dates (e.g., all the same date, future dates, dates before Midjourney existed)
3. Outputs a report of items needing correction
4. Provides a mechanism to batch-correct dates from a CSV override file

### Deliverable 3: News Page Implementation
Replace the "Coming Soon" placeholder with a fully functional news page:
1. **news.html** — complete HTML with header, filter bar, article grid, pagination, footer
2. **news.css** — additional styles (or additions to styles.css) for news-specific components
3. **news.js** — client-side rendering from `news-data.json`:
   - Fetch and parse JSON
   - Render article cards
   - Category filter buttons
   - Sort toggle (newest/oldest)
   - Client-side pagination (20 per page)
   - Loading skeleton while fetching
   - Error/empty states
4. **news-data.json** — sample file with 10 example articles for testing
5. **generate-news.py** — build script that:
   - Reads news from LLATOS news output (markdown files or API)
   - Filters for creative AI topics (Midjourney, Suno, Runway, Kling, Luma, Stable Diffusion, Pika, AI art, AI music, AI video)
   - Generates `news-data.json`
   - Can be called from GitHub Actions on a daily schedule

### Deliverable 4: GitHub Actions Daily Build
```yaml
# .github/workflows/daily-news.yml
name: Daily News Update
on:
  schedule:
    - cron: '0 8 * * *'   # 8am UTC daily
  workflow_dispatch:        # manual trigger
```
- Runs `generate-news.py`
- Commits updated `news-data.json`
- Deploys to GitHub Pages

---

## Self-Verification Checklist

Before submitting, verify every item:

### Critical Fixes
- [ ] Image hosting solution chosen with clear justification
- [ ] Migration script handles 6,000+ images with retry logic
- [ ] WebP conversion included (both full-size and thumbnails)
- [ ] Fallback strategy for already-expired images documented
- [ ] Cost estimate provided for hosting
- [ ] Gallery date correction script identifies and fixes incorrect dates

### News Page
- [ ] news.html replaces the "Coming Soon" placeholder completely
- [ ] Category filter works (Art, Video, Music, Tools, General)
- [ ] Sort toggle works (newest/oldest)
- [ ] Pagination works (20 items per page)
- [ ] Loading skeleton shown while fetching data
- [ ] Empty state shown gracefully when no articles
- [ ] Mobile responsive (single column on phone)
- [ ] Article cards match gallery card aesthetic (dark, amber hover)
- [ ] Source attribution links to original article
- [ ] UK date format used throughout

### Design Consistency
- [ ] All new CSS uses existing design tokens (no hardcoded colours)
- [ ] Amber accent (#c4851a) used consistently, no new brand colours
- [ ] Typography matches existing scale
- [ ] Hover states include amber glow effect
- [ ] Dark backgrounds maintained (no light panels)
- [ ] Social links order preserved (X, Instagram, YouTube, TikTok, Midjourney, Suno)

### Build & Deploy
- [ ] GitHub Actions workflow included for daily news updates
- [ ] generate-news.py filters correctly for creative AI topics
- [ ] Sample news-data.json provided with 10 realistic test articles
- [ ] No build tools required (keeps the no-npm philosophy)
- [ ] Existing pages unaffected (gallery, about, videos, music all still work)
