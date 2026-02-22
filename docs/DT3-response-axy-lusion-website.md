# Deep Think 3 — Prompt 12: Axy Lusion — AI Art Portfolio Website

**Source:** Google Gemini 3 Deep Think (free tier)
**URL:** https://gemini.google.com/share/cebc3d742e71
**Created:** 2026-02-19
**Published:** 2026-02-21

---

As a senior front-end web developer and creative portfolio specialist, I have reviewed the requirements for the Axy Lusion AI art portfolio. Given the massive scale of 6,000+ high-resolution assets and the framework-free constraint, performance and zero-egress architecture are paramount.

Below is the comprehensive engineering strategy, migration toolkit, and vanilla implementation to permanently resolve your CDN issues, correct metadata, and integrate the dynamic static news feed. Everything strictly adheres to your premium dark-mode aesthetic and UK English guidelines.

---

## Deliverable 1: Image Hosting Migration Plan

### 1. Chosen Hosting Solution: Cloudflare R2

For a static portfolio containing 6,000+ AI-generated images (~50–100GB of unoptimised data), Cloudflare R2 is the undeniable best choice.

**Justification:** Unlike Bunny CDN or AWS S3, Cloudflare charges zero egress (bandwidth) fees. A highly visual masonry gallery consumed by thousands of users will rack up massive bandwidth usage, which R2 mitigates entirely.

**Cost Estimate:** The free tier covers 10GB of storage and 10 million reads per month. By converting 6,000 images to WebP (saving ~60-70% file size), your total footprint will sit around 3–5GB. Monthly Cost: £0.00. Even if you scale to 50GB, excess storage is just $0.015/GB (approx. £0.60/month).

**Vercel Blob limitation:** Vercel Blob is capped at 1GB on the free tier, making it unusable for a portfolio of this size.

### 2. Fallback Strategy for 403 Expired Images

Midjourney currently uses ephemeral signed URLs. Many images in gallery.js will likely return a 403 Forbidden error during migration.

**The Fallback Plan:** The migration script catches 403s and logs the Midjourney UUIDs to `failed_uuids.csv`. You must then use the Midjourney Web App's archive search or the `/show job_id: <UUID>` command in Discord to retrieve them, download them into a local `fallback_images/` directory, and re-run the script. The script automatically checks this local directory before querying the CDN.

### 3. Migration Script (`scripts/migrate_images.py`)

This script securely downloads images, optimises them to WebP format, uploads them to R2 via the AWS S3 API (boto3), and dynamically rewrites your `gallery.js` array. (Requires: `pip install requests Pillow boto3`)

```python
import json
import os
import re
import requests
import boto3
from io import BytesIO
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

# Configuration
R2_ENDPOINT = "https://<YOUR_ACCOUNT_ID>.r2.cloudflarestorage.com"
BUCKET_NAME = "axylusion-gallery"
CUSTOM_DOMAIN = "https://r2.axylusion.com"
FALLBACK_DIR = "fallback_images"

s3 = boto3.client('s3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=os.getenv('R2_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('R2_SECRET_KEY')
)

def process_item(item):
    if CUSTOM_DOMAIN in item['image']:
        return item, True  # Already migrated

    uuid = item['image'].split('/')[-2] if '/' in item['image'] else item['id']
    fallback_path = os.path.join(FALLBACK_DIR, f"{uuid}.png")
    img_data = None

    # 1. Attempt fallback directory first
    if os.path.exists(fallback_path):
        with open(fallback_path, 'rb') as f:
            img_data = f.read()
    else:
        # 2. Fetch from CDN
        try:
            res = requests.get(item['image'], timeout=10)
            if res.status_code == 403:
                return item, False  # 403 Expired
            res.raise_for_status()
            img_data = res.content
        except Exception as e:
            print(f"Network error for {uuid}: {e}")
            return item, False

    # 3. Optimise and Convert to WebP
    try:
        img = Image.open(BytesIO(img_data)).convert("RGB")

        full_io = BytesIO()
        img.save(full_io, format="WEBP", quality=85)
        full_io.seek(0)

        img.thumbnail((400, 400), Image.Resampling.LANCZOS)
        thumb_io = BytesIO()
        img.save(thumb_io, format="WEBP", quality=80)
        thumb_io.seek(0)

        # 4. Upload to Cloudflare R2
        s3.upload_fileobj(full_io, BUCKET_NAME, f"gallery/{uuid}.webp",
                          ExtraArgs={'ContentType': 'image/webp'})
        s3.upload_fileobj(thumb_io, BUCKET_NAME, f"thumbs/{uuid}.webp",
                          ExtraArgs={'ContentType': 'image/webp'})

        item['image'] = f"{CUSTOM_DOMAIN}/gallery/{uuid}.webp"
        item['thumbnail'] = f"{CUSTOM_DOMAIN}/thumbs/{uuid}.webp"
        return item, True
    except Exception as e:
        print(f"Processing error for {uuid}: {e}")
        return item, False


def main():
    os.makedirs(FALLBACK_DIR, exist_ok=True)

    with open('gallery.js', 'r', encoding='utf-8') as f:
        content = f.read()

    match = re.search(r'(\[.*\])', content, re.DOTALL)
    data = json.loads(match.group(1))

    failed_uuids = []
    updated_data = []
    print(f"Processing {len(data)} images...")

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(process_item, data)

    for item, success in results:
        updated_data.append(item)
        if not success:
            failed_uuids.append(item['id'])

    # Write back preserving variable declaration
    prefix = content[:match.start()]
    suffix = content[match.end():]
    with open('gallery.js', 'w', encoding='utf-8') as f:
        f.write(prefix + json.dumps(updated_data, indent=4) + suffix)

    if failed_uuids:
        with open('failed_uuids.csv', 'w') as f:
            f.write("uuid\n" + "\n".join(failed_uuids))
        print(f"Logged {len(failed_uuids)} expired images to failed_uuids.csv. Download these manually to /{FALLBACK_DIR}.")


if __name__ == "__main__":
    main()
```

### 4. GitHub Actions Workflow (Image Uploads)

To automate future uploads effortlessly, create `.github/workflows/upload-images.yml`.

```yaml
name: Process New Gallery Images

on:
  push:
    paths:
      - 'gallery.js'
    branches:
      - main

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install requests Pillow boto3
      - name: Run Migration Script
        env:
          R2_ACCESS_KEY: ${{ secrets.R2_ACCESS_KEY }}
          R2_SECRET_KEY: ${{ secrets.R2_SECRET_KEY }}
        run: python scripts/migrate_images.py
      - name: Commit Updated Gallery
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: migrate new images to R2 [skip ci]"
          file_pattern: "gallery.js"
```

---

## Deliverable 2: Gallery Date Correction Script

This script audits the JSON, identifies logical impossibilities (dates prior to Midjourney's existence or future dates), and applies batch fixes via a CSV override (`date_corrections.csv` formatted as `id,correct_date`).

```python
# scripts/fix_dates.py
import json
import re
import csv
from datetime import datetime

MJ_INCEPTION = datetime(2022, 2, 1)  # Midjourney v1 release roughly

def main():
    with open('gallery.js', 'r', encoding='utf-8') as f:
        content = f.read()
    match = re.search(r'(\[.*\])', content, re.DOTALL)
    data = json.loads(match.group(1))

    # 1. Audit Phase
    suspicious = []
    for item in data:
        try:
            dt = datetime.strptime(item.get('date', ''), "%Y-%m-%d")
            if dt < MJ_INCEPTION:
                suspicious.append((item['id'], item['date'], "Pre-dates Midjourney"))
            elif dt > datetime.now():
                suspicious.append((item['id'], item['date'], "Future date"))
        except ValueError:
            suspicious.append((item['id'], item.get('date'), "Invalid format"))

    if suspicious:
        print(f"--- Found {len(suspicious)} suspicious dates ---")
        for sid, sdate, reason in suspicious:
            print(f"ID: {sid} | Date: {sdate} | Issue: {reason}")

    # 2. Correction Phase
    try:
        with open('date_corrections.csv', 'r', encoding='utf-8') as f:
            corrections = {row['id']: row['correct_date'] for row in csv.DictReader(f)}

        corrected_count = 0
        for item in data:
            if item['id'] in corrections:
                item['date'] = corrections[item['id']]
                corrected_count += 1

        if corrected_count > 0:
            prefix = content[:match.start()]
            suffix = content[match.end():]
            with open('gallery.js', 'w', encoding='utf-8') as f:
                f.write(prefix + json.dumps(data, indent=4) + suffix)
            print(f"\nSuccessfully corrected {corrected_count} dates.")
    except FileNotFoundError:
        print("\nNote: 'date_corrections.csv' not found. Create it to apply batch fixes.")


if __name__ == '__main__':
    main()
```

---

## Deliverable 3: News Page Implementation

### 1. `news.html`

Fully responsive, accessible HTML5. Social links perfectly match the specified order.

```html
<!DOCTYPE html>
<html lang="en-GB">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI News | Axy Lusion</title>
    <meta name="description" content="Latest updates on AI creative tools: Midjourney, Suno, Runway, and more.">
    <link rel="stylesheet" href="styles.css">
    <link rel="stylesheet" href="news.css">
</head>
<body>
    <header class="site-header">
        <a href="index.html" class="logo">Axy Lusion</a>
        <nav class="main-nav">
            <a href="gallery.html">Gallery</a>
            <a href="videos.html">Videos</a>
            <a href="music.html">Music</a>
            <a href="news.html" class="active" aria-current="page">News</a>
            <a href="about.html">About</a>
        </nav>
        <div class="social-links">
            <a href="#" aria-label="X">X</a>
            <a href="#" aria-label="Instagram">Instagram</a>
            <a href="#" aria-label="YouTube">YouTube</a>
            <a href="#" aria-label="TikTok">TikTok</a>
            <a href="#" aria-label="Midjourney">Midjourney</a>
            <a href="#" aria-label="Suno">Suno</a>
        </div>
    </header>

    <main class="page-container">
        <section class="page-header">
            <div class="page-header-content">
                <h1 class="page-title">AI Tools News</h1>
                <p class="page-subtitle">Updates from Midjourney, Suno, Runway, and the AI creative world</p>
            </div>
        </section>

        <section class="news-controls">
            <div class="filter-bar" id="category-filters" role="group" aria-label="Filter news by category">
                <button class="filter-btn active" data-category="all">All</button>
                <button class="filter-btn" data-category="art">Art</button>
                <button class="filter-btn" data-category="video">Video</button>
                <button class="filter-btn" data-category="music">Music</button>
                <button class="filter-btn" data-category="tools">Tools</button>
                <button class="filter-btn" data-category="general">General</button>
            </div>
            <div class="sort-toggle">
                <button id="sort-btn" class="sort-btn" aria-label="Toggle sort order">Sort: Newest First</button>
            </div>
        </section>

        <section class="news-grid-container">
            <div id="news-grid" class="news-grid" aria-live="polite">
            </div>
            <div id="empty-state" class="empty-state hidden">
                <p>No articles found for this category.</p>
            </div>
            <div class="pagination" id="pagination-controls" aria-label="Pagination">
                <button id="prev-btn" class="page-nav-btn" disabled>Previous</button>
                <span id="page-info" class="page-info">Page 1 of 1</span>
                <button id="next-btn" class="page-nav-btn" disabled>Next</button>
            </div>
        </section>
    </main>

    <footer class="site-footer">
        <div class="footer-brand">Axy Lusion</div>
        <p class="footer-tagline">Exploring the intersection of creativity and artificial intelligence</p>
        <div class="social-links">
            <a href="#" aria-label="X">X</a>
            <a href="#" aria-label="Instagram">Instagram</a>
            <a href="#" aria-label="YouTube">YouTube</a>
            <a href="#" aria-label="TikTok">TikTok</a>
            <a href="#" aria-label="Midjourney">Midjourney</a>
            <a href="#" aria-label="Suno">Suno</a>
        </div>
        <p class="copyright">&copy; 2026 Axy Lusion. <a href="https://koltregaskes.com">koltregaskes.com</a></p>
    </footer>

    <script src="news.js"></script>
</body>
</html>
```

### 2. `news.css`

Designed to match the gallery's luxury dark aesthetic with amber hovers and pill-shaped category badges.

```css
.page-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: var(--space-xl) var(--space-md);
}

.news-controls {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    align-items: center;
    gap: var(--space-md);
    margin-bottom: var(--space-2xl);
}

.filter-bar {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-sm);
}

.filter-btn, .sort-btn, .page-nav-btn {
    background: transparent;
    border: 1px solid var(--axyl-gray-700);
    color: var(--axyl-gray-300);
    padding: var(--space-xs) var(--space-md);
    border-radius: var(--radius-full);
    font-family: var(--font-body);
    font-size: 0.875rem;
    cursor: pointer;
    transition: all var(--transition-fast);
}

.filter-btn:hover, .sort-btn:hover, .page-nav-btn:not(:disabled):hover {
    border-color: var(--axyl-amber);
    color: var(--axyl-white);
    box-shadow: 0 0 10px var(--axyl-amber-glow);
}

.filter-btn.active {
    background: var(--axyl-amber);
    border-color: var(--axyl-amber);
    color: var(--axyl-dark);
    font-weight: 600;
}

.page-nav-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    border-color: var(--axyl-gray-800);
}

.news-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: var(--space-lg);
}

@media (min-width: 768px) {
    .news-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (min-width: 1024px) {
    .news-grid { grid-template-columns: repeat(3, 1fr); }
}

.news-card {
    background: var(--axyl-gray-900);
    border: 1px solid var(--axyl-gray-700);
    border-radius: var(--radius-lg);
    padding: var(--space-lg);
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
    text-decoration: none;
    color: var(--axyl-white);
    transition: all var(--transition-base);
}

.news-card:hover {
    transform: translateY(-4px);
    border-color: var(--axyl-amber);
    box-shadow: 0 8px 24px rgba(0,0,0,0.5), 0 0 20px var(--axyl-amber-glow);
}

.news-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--space-xs);
}

.category-badge {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    padding: 4px 12px;
    border-radius: var(--radius-full);
}

/* Specific Badge Colours as requested */
.badge-art { color: var(--axyl-amber); border: 1px solid var(--axyl-amber); background: rgba(196, 133, 26, 0.1); }
.badge-video { color: #4285F4; border: 1px solid #4285F4; background: rgba(66, 133, 244, 0.1); }
.badge-music { color: #10A37F; border: 1px solid #10A37F; background: rgba(16, 163, 127, 0.1); }
.badge-tools { color: #9b59b6; border: 1px solid #9b59b6; background: rgba(155, 89, 182, 0.1); }
.badge-general { color: var(--axyl-gray-400); border: 1px solid var(--axyl-gray-400); background: rgba(136, 136, 136, 0.1); }

.news-date {
    font-family: var(--font-mono);
    font-size: 0.875rem;
    color: var(--axyl-gray-400);
}

.news-title {
    font-family: var(--font-body);
    font-size: 1.125rem;
    font-weight: 600;
    line-height: 1.4;
    margin: 0;
}

.news-summary {
    font-family: var(--font-body);
    font-size: 1rem;
    color: var(--axyl-gray-300);
    line-height: 1.6;
    margin: 0;
    flex-grow: 1;
}

.news-source {
    font-family: var(--font-mono);
    font-size: 0.875rem;
    color: var(--axyl-gray-500);
    margin-top: var(--space-md);
    padding-top: var(--space-sm);
    border-top: 1px solid var(--axyl-gray-800);
}

.news-card:hover .news-source {
    color: var(--axyl-amber-light);
}

.empty-state {
    text-align: center;
    padding: var(--space-3xl);
    color: var(--axyl-gray-400);
    font-family: var(--font-mono);
    border: 1px dashed var(--axyl-gray-700);
    border-radius: var(--radius-lg);
}

.hidden { display: none !important; }

.pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: var(--space-md);
    margin-top: var(--space-2xl);
}

.page-info {
    font-family: var(--font-mono);
    font-size: 0.875rem;
    color: var(--axyl-gray-400);
}

/* Skeleton Loading Animation */
.skeleton-card {
    background: var(--axyl-gray-900);
    border: 1px solid var(--axyl-gray-800);
    border-radius: var(--radius-lg);
    min-height: 250px;
    position: relative;
    overflow: hidden;
}

.skeleton-card::after {
    content: '';
    position: absolute;
    top: 0; left: -100%;
    width: 200%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.05), transparent);
    animation: loading 1.5s infinite linear;
}

@keyframes loading {
    0% { transform: translateX(0); }
    100% { transform: translateX(50%); }
}
```

### 3. `news.js`

Client-side Vanilla JS managing fetch, format, filtering, and seamless DOM pagination.

```javascript
document.addEventListener('DOMContentLoaded', () => {
    const grid = document.getElementById('news-grid');
    const filterBtns = document.querySelectorAll('.filter-btn');
    const sortBtn = document.getElementById('sort-btn');
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const pageInfo = document.getElementById('page-info');
    const emptyState = document.getElementById('empty-state');
    const paginationControls = document.getElementById('pagination-controls');

    let allArticles = [];
    let filteredArticles = [];
    let currentCategory = 'all';
    let isNewestFirst = true;
    let currentPage = 1;
    const itemsPerPage = 20;

    function formatUKDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffHrs = Math.floor((now - date) / (1000 * 60 * 60));
        if (diffHrs < 1) return 'Just now';
        if (diffHrs === 1) return '1 hour ago';
        if (diffHrs < 24) return `${diffHrs} hours ago`;
        if (diffHrs < 48) return 'Yesterday';
        return new Intl.DateTimeFormat('en-GB', {
            day: 'numeric', month: 'short', year: 'numeric'
        }).format(date);
    }

    function renderSkeletons() {
        grid.innerHTML = Array(6).fill('<div class="skeleton-card"></div>').join('');
    }

    function applyFiltersAndSort() {
        filteredArticles = currentCategory === 'all'
            ? [...allArticles]
            : allArticles.filter(a => a.category === currentCategory);

        filteredArticles.sort((a, b) => {
            const timeA = new Date(a.date).getTime();
            const timeB = new Date(b.date).getTime();
            return isNewestFirst ? timeB - timeA : timeA - timeB;
        });

        currentPage = 1;
        renderPage();
    }

    function renderPage() {
        grid.innerHTML = '';
        if (filteredArticles.length === 0) {
            emptyState.classList.remove('hidden');
            paginationControls.classList.add('hidden');
            return;
        }
        emptyState.classList.add('hidden');
        paginationControls.classList.remove('hidden');

        const totalPages = Math.ceil(filteredArticles.length / itemsPerPage);
        const startIdx = (currentPage - 1) * itemsPerPage;
        const pageItems = filteredArticles.slice(startIdx, startIdx + itemsPerPage);

        pageItems.forEach(item => {
            const card = document.createElement('a');
            card.href = item.sourceUrl || '#';
            card.className = 'news-card';
            card.target = '_blank';
            card.rel = 'noopener noreferrer';
            card.innerHTML = `
                <div class="news-meta">
                    <span class="category-badge badge-${item.category}">${item.category}</span>
                    <span class="news-date">${formatUKDate(item.date)}</span>
                </div>
                <h2 class="news-title">${item.title}</h2>
                <p class="news-summary">${item.summary}</p>
                <div class="news-source">Source: ${item.source}</div>
            `;
            grid.appendChild(card);
        });

        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
        prevBtn.disabled = currentPage === 1;
        nextBtn.disabled = currentPage === totalPages;
    }

    // Event Listeners
    filterBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            filterBtns.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentCategory = e.target.dataset.category;
            applyFiltersAndSort();
        });
    });

    sortBtn.addEventListener('click', () => {
        isNewestFirst = !isNewestFirst;
        sortBtn.textContent = `Sort: ${isNewestFirst ? 'Newest First' : 'Oldest First'}`;
        applyFiltersAndSort();
    });

    prevBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderPage();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    });

    nextBtn.addEventListener('click', () => {
        const totalPages = Math.ceil(filteredArticles.length / itemsPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            renderPage();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    });

    // Init Data Fetch
    renderSkeletons();
    fetch('news-data.json')
        .then(res => res.json())
        .then(data => {
            allArticles = data;
            applyFiltersAndSort();
        })
        .catch(err => {
            console.error(err);
            grid.innerHTML = '';
            emptyState.innerHTML = '<p>Unable to load news. Please try again later.</p>';
            emptyState.classList.remove('hidden');
        });
});
```

### 4. `news-data.json` (Sample Payload)

```json
[
    {
        "id": "news-2026-02-19-mj",
        "title": "Midjourney V7 Announced with Real-Time Generation",
        "summary": "Midjourney's latest model brings sub-second rendering times and massive improvements to prompt coherence and typography generation.",
        "source": "Midjourney Blog",
        "sourceUrl": "https://midjourney.com",
        "date": "2026-02-19T09:00:00Z",
        "category": "art",
        "tags": ["midjourney", "image-generation"]
    },
    {
        "id": "news-2026-02-18-suno",
        "title": "Suno v5 Released: Stem Export & Mastering Tools",
        "summary": "The AI music platform now allows users to export individual stems (vocals, drums, bass) directly from their generated tracks.",
        "source": "Suno AI Updates",
        "sourceUrl": "https://suno.com",
        "date": "2026-02-18T14:30:00Z",
        "category": "music",
        "tags": ["suno", "audio"]
    },
    {
        "id": "news-2026-02-17-runway",
        "title": "Runway Gen-4 Pushes Boundaries of Coherent Video",
        "summary": "Runway introduces Gen-4, featuring 60-second generation limits with near-perfect temporal consistency across character movement.",
        "source": "Runway Research",
        "sourceUrl": "https://runwayml.com",
        "date": "2026-02-17T09:15:00Z",
        "category": "video",
        "tags": ["runway", "video-generation"]
    },
    {
        "id": "news-2026-02-16-kling",
        "title": "Kling Video AI Opens Public API",
        "summary": "Kling expands its ecosystem by offering a highly performant API for developers building custom video generation tools.",
        "source": "AI Video Daily",
        "sourceUrl": "https://kuaishou.com",
        "date": "2026-02-16T11:00:00Z",
        "category": "tools",
        "tags": ["kling", "api"]
    },
    {
        "id": "news-2026-02-15-sd3",
        "title": "Stable Diffusion 3.5 Open Sourced for Local Generation",
        "summary": "Stability AI drops the weights for SD 3.5, allowing local execution of high-fidelity 8B parameter models.",
        "source": "Stability AI",
        "sourceUrl": "https://stability.ai",
        "date": "2026-02-15T08:00:00Z",
        "category": "art",
        "tags": ["stable diffusion", "open source"]
    },
    {
        "id": "news-2026-02-14-luma",
        "title": "Luma Dream Machine Update Enhances Camera Controls",
        "summary": "A major workflow update to Luma provides directors with unparalleled 3D spatial camera control during video generation.",
        "source": "Luma Labs",
        "sourceUrl": "https://lumalabs.ai",
        "date": "2026-02-14T15:45:00Z",
        "category": "video",
        "tags": ["luma", "video"]
    },
    {
        "id": "news-2026-02-13-pika",
        "title": "Pika Labs Introduces Lip Sync Features",
        "summary": "Pika Labs adds native audio-to-animation lip syncing, vastly streamlining AI character animation workflows.",
        "source": "Pika Official",
        "sourceUrl": "https://pika.art",
        "date": "2026-02-13T10:20:00Z",
        "category": "video",
        "tags": ["pika", "animation"]
    },
    {
        "id": "news-2026-02-12-comfy",
        "title": "ComfyUI 2.0 Overhauls Node Interface",
        "summary": "The community-favourite node software releases a massive UX update, simplifying complex AI art routing for beginners.",
        "source": "ComfyUI GitHub",
        "sourceUrl": "https://github.com",
        "date": "2026-02-12T13:10:00Z",
        "category": "tools",
        "tags": ["comfyui", "workflows"]
    },
    {
        "id": "news-2026-02-11-copyright",
        "title": "UK High Court Rules on AI Artwork Authorship",
        "summary": "A landmark ruling determines that significant human input via prompting and curation qualifies for standard copyright protections.",
        "source": "Tech Law Review",
        "sourceUrl": "https://example.com",
        "date": "2026-02-11T09:30:00Z",
        "category": "general",
        "tags": ["copyright", "law"]
    },
    {
        "id": "news-2026-02-10-udio",
        "title": "Udio Enhances Audio Fidelity to 48kHz",
        "summary": "Udio matches the industry standard with lossless 48kHz stereo outputs, setting a new benchmark for synthetic audio quality.",
        "source": "Udio Blog",
        "sourceUrl": "https://udio.com",
        "date": "2026-02-10T16:00:00Z",
        "category": "music",
        "tags": ["udio", "audio generation"]
    }
]
```

### 5. `scripts/generate_news.py`

This script processes raw output from your LLATOS agent, safely filtering for relevant creative AI topics.

```python
import json
import os
from datetime import datetime

TARGET_KEYWORDS = ['midjourney', 'suno', 'runway', 'kling', 'luma',
                   'stable diffusion', 'pika', 'ai art', 'ai music', 'ai video']

def categorise_article(text):
    text = text.lower()
    if any(k in text for k in ['midjourney', 'stable diffusion', 'ai art']):
        return 'art'
    if any(k in text for k in ['runway', 'kling', 'luma', 'pika', 'ai video']):
        return 'video'
    if any(k in text for k in ['suno', 'udio', 'ai music']):
        return 'music'
    if any(k in text for k in ['update', 'api', 'tooling', 'comfyui']):
        return 'tools'
    return 'general'

def build_news_feed():
    raw_data_path = 'llatos_raw_output.json'
    raw_articles = []

    if os.path.exists(raw_data_path):
        with open(raw_data_path, 'r', encoding='utf-8') as f:
            raw_articles = json.load(f)

    filtered_articles = []
    for article in raw_articles:
        text = (article.get('title', '') + ' ' + article.get('summary', '') +
                ' ' + ' '.join(article.get('tags', []))).lower()
        if any(keyword in text for keyword in TARGET_KEYWORDS):
            category = categorise_article(text)
            filtered_articles.append({
                "id": article.get("id", f"news-{int(datetime.now().timestamp())}"),
                "title": article.get("title", "Untitled"),
                "summary": article.get("summary", ""),
                "source": article.get("source", "Unknown Source"),
                "sourceUrl": article.get("sourceUrl", "#"),
                "date": article.get("date", datetime.utcnow().isoformat() + "Z"),
                "category": category,
                "tags": article.get("tags", [])
            })

    # Sort descending (newest first)
    filtered_articles.sort(key=lambda x: x['date'], reverse=True)

    with open('news-data.json', 'w', encoding='utf-8') as f:
        json.dump(filtered_articles, f, indent=4)

    print(f"Built news-data.json with {len(filtered_articles)} relevant articles.")

if __name__ == '__main__':
    build_news_feed()
```

---

## Deliverable 4: GitHub Actions Daily Build

`.github/workflows/daily-news.yml`

This workflow operates entirely on GitHub's free runners without triggering npm setups, ensuring the architecture remains fast, vanilla, and automated.

```yaml
name: Daily News Update

on:
  schedule:
    - cron: '0 8 * * *'   # 8am UTC daily
  workflow_dispatch:       # Allows manual trigger button in UI

permissions:
  contents: write

jobs:
  update-news:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      # Example: Pull daily output from LLATOS (Update with your actual agent retrieval method)
      # - run: curl -o llatos_raw_output.json https://api.koltregaskes.com/llatos/today

      - name: Generate News JSON
        run: python scripts/generate_news.py

      - name: Commit and Push Changes
        uses: stefanzweifel/git-auto-commit-action@v5
        with:
          commit_message: "chore: update daily news data [skip ci]"
          file_pattern: "news-data.json"
          branch: main
```
