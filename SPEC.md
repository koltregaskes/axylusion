# Axy Lusion — Design Specification
## axylusion.com | AI Art Portfolio

**Version:** 1.0
**Created:** 2026-01-29
**Status:** Specification

---

## 1. Vision

Axy Lusion is a cinematic AI art portfolio showcasing Midjourney images, AI-generated videos, and Suno music. The experience should feel like stepping into a **dark gallery at night** — immersive, image-first, with the UI receding to let the art command attention. Think Instagram's visual density but with the moody editorial quality of landonorris.com.

**Design DNA:** Instagram's grid density × Lando Norris cinematic darkness × gallery museum experience.

---

## 2. Visual Design Direction

### 2.1 Colour Palette

```css
:root {
  /* Near-black base — art gallery darkness */
  --bg-void:        #050507;
  --bg-base:        #0A0A0E;
  --bg-surface:     #131317;
  --bg-elevated:    #1C1C22;
  --bg-modal:       #111115;

  /* Text — cool off-whites for gallery neutrality */
  --text-primary:   #EDEDF0;
  --text-secondary: #8E8E96;
  --text-muted:     #55555E;

  /* Accent — warm amber/cream (from current site) */
  --accent:         #C8A87C;
  --accent-hover:   #D4B88E;
  --accent-soft:    rgba(200, 168, 124, 0.12);

  /* Borders — barely visible */
  --border:         rgba(255, 255, 255, 0.06);
  --border-hover:   rgba(255, 255, 255, 0.12);

  /* Type badges */
  --badge-image:    #7B6FDE;
  --badge-video:    #E05252;
  --badge-music:    #4CAF79;

  /* Overlay */
  --overlay:        rgba(5, 5, 7, 0.85);
  --overlay-heavy:  rgba(5, 5, 7, 0.95);
}
```

**Dark only. No light mode.** The darkness is the frame.

### 2.2 Typography

```css
:root {
  --font-display:  'Source Serif 4', Georgia, serif;
  --font-body:     'Inter', -apple-system, sans-serif;
  --font-mono:     'JetBrains Mono', monospace;
  --font-prompt:   'JetBrains Mono', monospace;  /* Prompts always in mono */
}
```

| Element | Font | Size | Weight |
|---------|------|------|--------|
| Site title | Serif | 1.5rem | 700 |
| Hero overlay text | Serif | clamp(2rem, 4vw, 3.5rem) | 700 |
| Piece title (modal) | Serif | 1.5rem | 600 |
| Body text | Sans | 1rem | 400 |
| Prompt text | Mono | 0.875rem | 400 |
| Parameters | Mono | 0.75rem | 400 |
| Tags | Sans | 0.75rem | 500 |
| Metadata | Sans | 0.8125rem | 400 |

### 2.3 Motion & Animation

| Element | Effect | Duration |
|---------|--------|----------|
| Gallery grid items | Fade in on scroll (staggered) | 400ms, 50ms stagger |
| Image hover | Scale to 1.03 + brightness increase + overlay fade | 300ms ease-out |
| Modal open | Fade in + scale from 0.95 | 250ms ease-out |
| Modal close | Fade out + scale to 0.95 | 200ms ease-in |
| Modal image transition (nav) | Crossfade | 200ms |
| Filter change | Grid items shuffle with layout animation | 300ms |
| Hero parallax | Subtle Y translation on scroll | Continuous, 60fps |
| Infinite scroll loader | Pulse animation | 1s infinite |

---

## 3. Page Layouts

### 3.1 Homepage / Gallery

```
┌──────────────────────────────────────────────────────────┐
│  Nav: "Axy Lusion" (left) · Gallery · Models · About     │
│       Search icon · Filter icon (right)                   │
│  ─ transparent → glass blur on scroll ─                   │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────┐        │
│  │  HERO — Full-bleed featured piece            │        │
│  │  Stunning AI art, full viewport height       │        │
│  │  Title overlay at bottom with gradient       │        │
│  │  "Explore the Gallery →"                     │        │
│  └──────────────────────────────────────────────┘        │
│                                                           │
│  ── Filter Bar ──                                        │
│  [All] [Images] [Videos] [Music]                          │
│  Model: [Any ▾]  Date: [Any ▾]  Tags: [Select ▾]        │
│  Sort: [Newest ▾]  ·  Grid: [□□ ▾]  ·  [Reset]          │
│                                                           │
│  ── Masonry / Grid Gallery ──                            │
│  ┌───────┐ ┌──────────┐ ┌───────┐ ┌───────┐             │
│  │       │ │          │ │       │ │       │             │
│  │  IMG  │ │   IMG    │ │  IMG  │ │  VID  │             │
│  │       │ │ (tall)   │ │       │ │  ▶    │             │
│  │ hover:│ │          │ │  ×3   │ │       │             │
│  │ title │ │          │ │bundle │ │       │             │
│  └───────┘ └──────────┘ └───────┘ └───────┘             │
│  ┌──────────┐ ┌───────┐ ┌───────┐ ┌──────────┐          │
│  │          │ │       │ │  ♪    │ │          │          │
│  │   IMG    │ │  IMG  │ │ MUSIC │ │   IMG    │          │
│  │          │ │       │ │       │ │          │          │
│  └──────────┘ └───────┘ └───────┘ └──────────┘          │
│                                                           │
│  [Loading more...] or [Load More] button                 │
│                                                           │
│  ── Footer ──                                            │
│  Social: @Axylusion links · Powered by AI                │
└──────────────────────────────────────────────────────────┘
```

**Grid behaviour:**
- **Desktop:** 4 columns, masonry layout (varied heights based on aspect ratio)
- **Tablet:** 3 columns
- **Mobile:** 2 columns
- Gap: 4px (tight, Instagram-style)
- Hover: title + model badge + type icon overlay
- Bundles: show "×3" badge, click opens collection view

### 3.2 Piece Modal (Lightbox)

```
┌──────────────────────────────────────────────────────────┐
│  ✕ close (top-right)        ← →  navigation arrows       │
│                                                           │
│  ┌────────────────────────────────────────────────┐      │
│  │                                                │      │
│  │                                                │      │
│  │            Full-resolution image                │      │
│  │            (or video player)                    │      │
│  │            (or audio player with waveform)      │      │
│  │                                                │      │
│  │                                                │      │
│  └────────────────────────────────────────────────┘      │
│                                                           │
│  Title (serif)                           [Share] [♡]     │
│  Created: 14 Jan 2026 · Midjourney v7                    │
│                                                           │
│  ── Prompt ──                                            │
│  ┌────────────────────────────────────────────────┐      │
│  │  cinematic portrait of a warrior queen,        │      │
│  │  volumetric lighting, film grain --ar 3:2      │      │
│  │  --style raw --stylize 200                     │      │
│  │                              [Copy Prompt 📋]  │      │
│  └────────────────────────────────────────────────┘      │
│                                                           │
│  Parameters: --ar 3:2 · --style raw · --s 200            │
│  Dimensions: 3:2 · Model: Midjourney v7                  │
│  Tags: [portrait] [fantasy] [cinematic] [lighting]        │
│                                                           │
│  [View on Midjourney ↗]                                  │
│                                                           │
│  ── Variations (if bundle) ──                            │
│  [thumb] [thumb] [thumb] [thumb]                          │
└──────────────────────────────────────────────────────────┘
```

**Modal interactions:**
- ← → arrow keys to navigate
- Mouse wheel to navigate (existing feature)
- Escape to close
- Click outside to close
- Swipe on mobile
- Deep-linkable URL (e.g., /gallery/piece-id)

### 3.3 Collection / Bundle View

When pieces are grouped by similar prompts:

```
┌──────────────────────────────────────────────────────────┐
│  ← Back to Gallery                                       │
│                                                           │
│  Collection: "Warrior Queen Series" (serif H1)           │
│  4 variations · Midjourney v7 · December 2024            │
│                                                           │
│  ┌──────────┐ ┌──────────┐                               │
│  │          │ │          │                               │
│  │  Full    │ │  Full    │                               │
│  │  size    │ │  size    │                               │
│  │          │ │          │                               │
│  └──────────┘ └──────────┘                               │
│  ┌──────────┐ ┌──────────┐                               │
│  │          │ │          │                               │
│  │  Full    │ │  Full    │                               │
│  │  size    │ │  size    │                               │
│  │          │ │          │                               │
│  └──────────┘ └──────────┘                               │
│                                                           │
│  Shared Prompt: "cinematic portrait of a warrior..."     │
│  [Copy Prompt]                                           │
└──────────────────────────────────────────────────────────┘
```

### 3.4 Model Info Page

```
┌──────────────────────────────────────────────────────────┐
│  Nav                                                      │
├──────────────────────────────────────────────────────────┤
│  Model: Midjourney v7 (serif H1)                         │
│  Released: October 2024 · Image Generation                │
│  [Official Docs ↗]                                       │
│                                                           │
│  ── Overview ──                                          │
│  Description of capabilities, strengths, style            │
│                                                           │
│  ── Sample Gallery ──                                    │
│  Grid of pieces created with this model                  │
│  (filtered from main gallery)                            │
│                                                           │
│  ── Key Parameters ──                                    │
│  Table: parameter, description, range, default            │
│                                                           │
│  ── Changelog ──                                         │
│  Timeline of updates and improvements                    │
│                                                           │
│  [View all {model} pieces →]                             │
└──────────────────────────────────────────────────────────┘
```

### 3.5 About Page

Minimal editorial page: who Kol is, what Axy Lusion is about, links to koltregaskes.com and social accounts. Gallery highlight reel.

---

## 4. Component List

| Component | Purpose | Notes |
|-----------|---------|-------|
| **NavBar** | Transparent → glass on scroll | Minimal, stays out of the way |
| **HeroSection** | Full-bleed featured artwork | Rotating featured piece |
| **FilterBar** | Type/model/date/tag filters | Sticky below nav |
| **GalleryGrid** | Masonry image grid | CSS Grid + JS for masonry |
| **GalleryItem** | Single grid tile | Hover overlay with meta |
| **BundleBadge** | "×3" variation counter | On grouped items |
| **TypeBadge** | Image/Video/Music indicator | Colour-coded (purple/red/green) |
| **PieceModal** | Full lightbox view | Image + prompt + metadata |
| **PromptBlock** | Monospace prompt display | Copy button |
| **ParameterChips** | Individual parameter badges | --ar, --style, --s etc |
| **TagPill** | Clickable tag | Filters gallery on click |
| **MediaPlayer** | Video/audio playback | Video: native HTML5 or Plyr; Audio: waveform |
| **CollectionView** | Bundled variations page | Grid of related pieces |
| **ModelCard** | Model info summary | Name, icon, piece count |
| **ModelPage** | Full model documentation | Specs, samples, changelog |
| **InfiniteScroll** | Auto-load on scroll | IntersectionObserver trigger |
| **ShareMenu** | Per-piece sharing | X, copy link, download |
| **SearchOverlay** | Full-text search | Searches prompts, tags, names |
| **SkeletonGrid** | Loading state | Grey placeholder tiles |
| **EmptyState** | No results message | Friendly prompt to reset filters |
| **Footer** | Social links, credits | Minimal |

---

## 5. Data Requirements

### 5.1 Gallery Schema (existing, extended)

```typescript
interface GalleryPiece {
  id: string;
  name: string;
  type: 'image' | 'video' | 'music';
  source: 'midjourney' | 'suno' | 'dalle' | 'stable-diffusion' | 'runway';
  model: string;                    // "Midjourney v7"
  url: string;                      // Source page URL
  cdn_url: string;                  // Direct media URL
  thumbnail_url?: string;           // For videos/music
  prompt: string;
  parameters: string;               // "--ar 3:2 --style raw"
  dimensions: string;               // "3:2"
  created: string;                  // ISO date
  tags: string[];
  featured?: boolean;
  collection_id?: string;           // Groups variations
  width?: number;                   // Pixels (for masonry calc)
  height?: number;
  blurhash?: string;                // Placeholder while loading
}

interface Collection {
  id: string;
  name: string;
  description?: string;
  cover_piece_id: string;
  piece_ids: string[];
  shared_prompt?: string;
}

interface ModelInfo {
  id: string;
  name: string;                     // "Midjourney v7"
  provider: string;                 // "Midjourney"
  type: 'image' | 'video' | 'music' | 'multimodal';
  released: string;
  description: string;
  capabilities: string[];
  parameters: ModelParameter[];
  changelog: ChangelogEntry[];
  official_url: string;
  piece_count: number;              // Computed
}
```

### 5.2 Data Sources

| Source | Content | Method |
|--------|---------|--------|
| Midjourney archive | Images, prompts, parameters | Playwright scraper (pending build) |
| Suno | Music tracks | Manual curation initially |
| Manual entry | Metadata, tags, collections | gallery.json editing |
| Model info | Specs, changelogs | Manual research + AI assist |

### 5.3 Target Scale

- **Phase 1:** 50 curated pieces (current: 4)
- **Phase 2:** 500+ via automated Midjourney extraction
- **Phase 3:** 1000+ with video and music content

---

## 6. Tech Stack Recommendation

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Framework** | Astro 5 (static) or enhanced vanilla JS | Current site is vanilla HTML/JS — could upgrade or keep simple |
| **Styling** | Tailwind CSS 4 | Utility-first, fast iteration |
| **Gallery engine** | CSS Grid masonry + IntersectionObserver | Native performance, no heavy library |
| **Image optimisation** | Cloudflare Images or sharp (build-time) | WebP/AVIF, responsive srcset, blurhash |
| **Video hosting** | Cloudflare R2 + Stream | Solves 403 errors, scalable, affordable |
| **Audio player** | Wavesurfer.js | Waveform visualisation for music |
| **Search** | Fuse.js (client-side fuzzy) | Searches prompts, tags, names |
| **Hosting** | Cloudflare Pages | Free tier, global CDN |
| **Domain** | axylusion.com | Migrate DNS from Notion redirect |
| **Data** | Static JSON (gallery.json) | Simple, fast, git-versioned |
| **Analytics** | Cloudflare Web Analytics | Privacy-respecting |

### Migration Path

The current site works. Two options:

**Option A — Enhance existing (recommended for speed):**
- Keep vanilla HTML/CSS/JS structure
- Add Tailwind for styling
- Implement masonry grid
- Add new components incrementally

**Option B — Rebuild in Astro:**
- Full rebuild with component architecture
- Better for long-term maintenance at 1000+ pieces
- Share design tokens with koltregaskes.com

---

## 7. Performance Requirements

| Metric | Target | Strategy |
|--------|--------|----------|
| **LCP** | < 2.0s | Hero image preload, optimised formats |
| **FID** | < 50ms | Minimal JS, defer non-critical |
| **CLS** | < 0.05 | Fixed aspect ratios, blurhash placeholders |
| **Image load** | Progressive | Blurhash → thumbnail → full resolution |
| **Gallery load** | 30 items initial | Then infinite scroll batches of 30 |
| **Modal open** | < 100ms | Pre-fetched nearby images |
| **Search** | < 50ms | Client-side Fuse.js, pre-indexed |

### Image Pipeline

```
Source (Midjourney CDN)
  → Download original (high-res)
  → Generate blurhash (build time)
  → Generate thumbnail (400px wide, WebP)
  → Generate display (1200px wide, WebP)
  → Generate full (original size, WebP + AVIF)
  → Upload to Cloudflare R2
  → Serve via Cloudflare CDN with responsive srcset
```

---

## 8. Inspiration References

| Site | What to Take |
|------|-------------|
| **landonorris.com** | Full-bleed hero, cinematic darkness, editorial scroll experience |
| **Instagram** | Grid density, 4px gaps, hover previews, modal navigation |
| **unsplash.com** | Masonry grid, blurhash placeholders, image-first experience |
| **behance.net** | Project/collection grouping, creative portfolio patterns |
| **artstation.com** | AI art showcase patterns, prompt display conventions |

---

*Specification by Claude (subagent: website-design-specs) — 2026-01-29*
