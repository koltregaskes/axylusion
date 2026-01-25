# Axylusion

AI Art, Video & Music Gallery by [Kol Tregaskes](https://koltregaskes.com)

## Live Site

**Domain:** [axylusion.com](https://axylusion.com) (pending DNS configuration)
**GitHub Pages:** [koltregaskes.github.io/axylusion](https://koltregaskes.github.io/axylusion)

## Features

- **Unified Gallery** - Images, videos, and music in one place
- **Search & Filter** - By keyword, date, type, or tags
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Dark Theme** - Purple/pink gradient accent colours
- **No Backend Required** - Static site with JSON database

## Content Sources

| Type | Source | Format |
|------|--------|--------|
| Images | Midjourney | PNG via CDN |
| Videos | Midjourney | MP4 via CDN |
| Music | Suno | MP3 (local or CDN) |

## Structure

```
axylusion/
├── index.html          # Main page
├── styles.css          # Styling
├── gallery.js          # Logic (includes embedded data fallback)
├── data/
│   └── gallery.json    # Gallery database
└── README.md
```

## Adding Content

Edit `data/gallery.json` with new entries:

```json
{
  "id": "unique-id",
  "name": "Display Name",
  "type": "image|video|music",
  "source": "midjourney|suno",
  "url": "https://source-link",
  "cdn_url": "https://direct-media-url",
  "prompt": "Generation prompt",
  "parameters": "--ar 16:9 --style raw",
  "dimensions": "16:9",
  "created": "2024-12-14",
  "tags": ["tag1", "tag2"]
}
```

## Local Development

Just open `index.html` in a browser. The site works with file:// protocol thanks to embedded data fallback.

For live reloading:
```bash
npx http-server -p 8080
```

## Deployment

Push to GitHub and enable Pages from the main branch.

## Related

- **Main Site:** [koltregaskes.com](https://koltregaskes.com)
- **Midjourney:** [@koltregaskes](https://www.midjourney.com/@koltregaskes)
- **X/Twitter:** [@axylusion](https://x.com/axylusion)
