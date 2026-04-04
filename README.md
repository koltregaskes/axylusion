# Xillusion

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

**Live Site:** [koltregaskes.github.io/axylusion](https://koltregaskes.github.io/axylusion)

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

## Publishing Notes

- The site is designed to be deployed as a static website.
- If you use GitHub Pages or another static host, make sure the custom domain and DNS are configured there rather than in the source files.
- Media uploads for the CMS are configured to land in `images/uploads/`.

## Links

- Main website: [koltregaskes.com](https://koltregaskes.com)
- X: [@Axylusion](https://x.com/Axylusion)
- Instagram: [@axylusion](https://www.instagram.com/axylusion)
- YouTube: [@AxyLusion](https://www.youtube.com/@AxyLusion)
- TikTok: [@axylusion](https://www.tiktok.com/@axylusion)
