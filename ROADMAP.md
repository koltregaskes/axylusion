# Axylusion Website Roadmap

**Brand:** Axylusion - AI Art, Video & Music by Kol Tregaskes
**Domain:** axylusion.com (currently redirects to Notion - needs DNS update)
**Repo:** github.com/koltregaskes/axylusion

---

## Current State (v1.0)

**Live:** [koltregaskes.github.io/axylusion](https://koltregaskes.github.io/axylusion)

### Features
- Gallery grid with images, videos, music
- Search by keyword
- Filter by date (month picker)
- Filter by type (all/images/videos/music)
- Tag-based filtering
- Modal view with prompt, parameters, source link
- Social links (X, Instagram, YouTube, TikTok, Midjourney)
- Responsive design (desktop/tablet/mobile)
- Dark theme with amber/cream accents

### Tech Stack
- Static HTML/CSS/JS
- JSON database (`data/gallery.json`)
- GitHub Pages hosting
- Midjourney CDN for images/videos

---

## Content Sources

| Type | Platform | Notes |
|------|----------|-------|
| **Images** | Midjourney | CDN URLs work directly |
| **Videos** | Midjourney | MP4 with .webp thumbnails |
| **Music** | Suno | Need to extract playlist data |
| **Music Videos** | Instagram/YouTube/TikTok | Embed or link |

---

## Phase 2: Content Expansion

### Priority 1: Populate Gallery (500+ images)
- [ ] Catalogue Midjourney likes from archive
- [ ] Extract metadata (prompts, parameters, dates)
- [ ] Build automation script for batch processing
- [ ] Add proper tagging taxonomy

### Priority 2: Music Integration
- [ ] Export Suno playlist metadata
- [ ] Add Suno tracks to gallery
- [ ] Music player in modal (audio element)
- [ ] Album art support (use Suno cover images)

### Priority 3: Music Videos
- [ ] Decide: embed vs link strategy
- [ ] Add music video entries to database
- [ ] Video-specific tags (music-video, visualiser, etc.)

---

## Phase 3: Website Features

### Navigation Structure
```
axylusion.com/
├── / (Gallery - current)
├── /images (Filtered view)
├── /videos (Filtered view)
├── /music (Music-focused page with player)
└── /about (Brand story, links to socials)
```

### Enhanced Gallery Features
- [ ] Infinite scroll or pagination
- [ ] Grid density options (compact/comfortable)
- [ ] Sort options (date, name, random)
- [ ] Lightbox navigation (prev/next with keyboard)
- [ ] Collection/album groupings

### Music Page
- [ ] Persistent audio player
- [ ] Playlist functionality
- [ ] Visualiser background option
- [ ] Links to streaming platforms

### About Page
- [ ] Brand story
- [ ] Links to all socials
- [ ] Contact/commission info (if applicable)
- [ ] Link back to koltregaskes.com

---

## Phase 4: Technical Improvements

### Performance
- [ ] Image lazy loading (already implemented)
- [ ] Service worker for offline gallery
- [ ] CDN for static assets
- [ ] WebP thumbnails for all images

### SEO & Social
- [ ] Open Graph images per item
- [ ] Structured data (JSON-LD)
- [ ] Sitemap generation
- [ ] robots.txt

### Analytics
- [ ] Privacy-friendly analytics (Plausible/Fathom)
- [ ] Track popular items, search terms

---

## Phase 5: DNS & Domain

### Current State
- `axylusion.com` redirects to `axylusion-art.notion.site`
- GitHub Pages at `koltregaskes.github.io/axylusion`

### Migration Plan
1. Enable GitHub Pages for axylusion repo
2. Add CNAME file with `axylusion.com`
3. Update DNS records:
   - A record → GitHub Pages IPs
   - CNAME www → koltregaskes.github.io
4. Test and verify SSL

---

## Branding Notes

### Current Palette (Temporary)
- Amber: `#c4851a`
- Cream: `#f5e6c8`
- Background: `#0a0a0a`
- Surface: `#1a1a1a`

### Logo
- AI-generated wordmark from Midjourney
- No specific font - custom design
- Available in multiple aspect ratios

### Future Branding
- Consider consistent colour direction
- May need icon/favicon
- Social media templates

---

## Integration with Main Site

**koltregaskes.com** (notion-site-test)
- Add "Axylusion" link to navigation
- Cross-link blog posts about AI art to Axylusion

**axylusion.com** (this site)
- "Kol Tregaskes" link in footer
- About page mentions main site

---

## Social Platforms

| Platform | Handle | Content |
|----------|--------|---------|
| X | @Axylusion | All content types |
| Instagram | @axylusion | Music videos, images |
| YouTube | @AxyLusion | Music videos, longer content |
| TikTok | @axylusion | Short music videos |
| Midjourney | @axylusion | Source images |

---

## Next Actions

1. **Now:** Enable GitHub Pages on the repo
2. **Soon:** Batch-add Midjourney images (500+)
3. **Next:** Integrate Suno music
4. **Later:** DNS migration from Notion to GitHub Pages
