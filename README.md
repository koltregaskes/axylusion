# Axy Lusion

This repository contains the Axy Lusion creative portfolio site: a static website for AI artwork, music, video, news, blog posts, and creative tool coverage.

## What the Site Includes

- A cinematic homepage with a hero feature and latest-image scroll experience
- A full gallery backed by `data/gallery.json`
- Dedicated pages for music, video, blog, news, tools, and about content
- A simple Decap CMS admin shell for future editorial workflows

## Stack

- Plain HTML, CSS, and JavaScript
- No framework and no build step
- Static hosting friendly
- Gallery/media data stored in `data/gallery.json`

**Preview Path:** [koltregaskes.github.io/axylusion](https://koltregaskes.github.io/axylusion)

**Intended Production Domain:** `https://axylusion.com`

## Local Preview

Run a local static server from the repo root, for example:

```bash
python -m http.server 4173
```

Then open [http://127.0.0.1:4173/index.html](http://127.0.0.1:4173/index.html).

## Project Structure

- `index.html` - homepage and latest-image showcase
- `gallery.html` - searchable gallery
- `blog.html` - blog landing page and editorial entry point
- `news.html` - news landing page
- `music.html` / `videos.html` / `tools.html` - supporting sections
- `data/gallery.json` - gallery source data
- `styles.css` - shared site styling
- `admin/` - Decap CMS configuration and entry page
- `content/` - editable markdown content
- `news-digests/` - news source material used by the site
- `scripts/refresh-site-data.ps1` - local refresh pipeline for homepage/news/A-List validation
- `scripts/run-scheduled-refresh.ps1` - scheduled entrypoint for morning full refresh and evening news-only refresh
- `scripts/run-smoke-test.ps1` - local browser smoke-test wrapper for the public pages
- `scripts/rebuild-homepage-gallery.py` - repoint homepage gallery items from `data/gallery.json`
- `scripts/smoke-test-site.mjs` - browser smoke test for key public pages
- `docs/CONTENT-FLOWS.md` - source-of-truth and refresh documentation

## Publishing Notes

- The site is designed to be deployed as a static website.
- If you use GitHub Pages or another static host, make sure the custom domain and DNS are configured there rather than in the source files.
- Media uploads for the CMS are configured to land in `images/uploads/`.
- The current public site is driven by static HTML, `news-digests`, and JSON payloads rather than automatic markdown-to-page rendering from `content/`.
- Local unattended refresh is now registered through the central website scheduler:
  - `Websites-AxyLusion-Refresh-Morning` at `07:20`
  - `Websites-AxyLusion-Refresh-Evening` at `19:20`

## Links

- Main website: [koltregaskes.com](https://koltregaskes.com)
- X: [@Axylusion](https://x.com/Axylusion)
- Instagram: [@axylusion](https://www.instagram.com/axylusion)
- YouTube: [@AxyLusion](https://www.youtube.com/@AxyLusion)
- TikTok: [@axylusion](https://www.tiktok.com/@axylusion)
