// Gallery data - embedded for local file:// access, also loads from data/gallery.json when served
const embeddedData = {
  "items": [
    {
      "id": "e055ca01-1d3c-433c-80f3-aa4818322225",
      "name": "Fantasy Heroine - Red Hair",
      "type": "image",
      "source": "midjourney",
      "url": "https://www.midjourney.com/jobs/e055ca01-1d3c-433c-80f3-aa4818322225?index=0",
      "cdn_url": "https://cdn.midjourney.com/e055ca01-1d3c-433c-80f3-aa4818322225/0_0.png",
      "prompt": "Cinematic, ultra-high quality realistic professional award winning photography, Lora, strong young woman, intense gaze, determined expression, slightly wild red hair, fantasy heroine portrait, half body, subtle battle scars, dirt and dust on skin, graphic novel illustration on antique yellowed parchment paper with light grain, extreme high-contrast black and white pencil drawing, hard noir lighting, deep shadows, blown-out highlights, bold ink lines combined with rough graphite shading, visible pencil strokes, cross-hatching, heavy chiaroscuro, Sin City style noir atmosphere, brutal contrast, almost monochrome, hand-drawn comic art, dark fantasy graphic novel, in the style of Luis Royo and Frank Frazetta, dramatic composition, cinematic framing, raw emotional intensity+ use text",
      "parameters": "--ar 3:2 --style raw --stylize 200 --profile aztrg5w",
      "dimensions": "3:2",
      "created": "2024-12-14",
      "tags": ["portrait", "fantasy", "cinematic", "noir", "woman", "graphic-novel", "sin-city"]
    },
    {
      "id": "bbee3420-ec91-4dbd-b4fe-fd81a4e39a47",
      "name": "Fantasy Heroine - Variant",
      "type": "image",
      "source": "midjourney",
      "url": "https://www.midjourney.com/jobs/bbee3420-ec91-4dbd-b4fe-fd81a4e39a47?index=0",
      "cdn_url": "https://cdn.midjourney.com/bbee3420-ec91-4dbd-b4fe-fd81a4e39a47/0_0.png",
      "prompt": "Cinematic, ultra-high quality realistic professional award winning photography, Lora, strong young woman, intense gaze, determined expression, slightly wild red hair, fantasy heroine portrait, half body, subtle battle scars, dirt and dust on skin, graphic novel illustration on antique yellowed parchment paper with light grain, extreme high-contrast black and white pencil drawing, hard noir lighting, deep shadows, blown-out highlights, bold ink lines combined with rough graphite shading, visible pencil strokes, cross-hatching, heavy chiaroscuro, Sin City style noir atmosphere, brutal contrast, almost monochrome, hand-drawn comic art, dark fantasy graphic novel, in the style of Luis Royo and Frank Frazetta, dramatic composition, cinematic framing, raw emotional intensity+ use text",
      "parameters": "--ar 3:2 --style raw --stylize 1000 --profile aztrg5w",
      "dimensions": "3:2",
      "created": "2024-12-14",
      "tags": ["portrait", "fantasy", "cinematic", "noir", "woman", "graphic-novel", "sin-city"]
    },
    {
      "id": "c3558a76-5d87-4b0f-8153-dbd38646e905",
      "name": "Cyberpunk Woman - Comic Style",
      "type": "image",
      "source": "midjourney",
      "url": "https://www.midjourney.com/jobs/c3558a76-5d87-4b0f-8153-dbd38646e905?index=0",
      "cdn_url": "https://cdn.midjourney.com/c3558a76-5d87-4b0f-8153-dbd38646e905/0_0.png",
      "prompt": "comic book style, beautiful woman, mid 30s, athletic, dark hair pushed back, cyberpunk, near future, leather jacket, crop top, cargo pants, looking directly at the camera, stood in front of a futuristic neon city, neon lights, night time",
      "parameters": "--ar 91:51 --style raw --stylize 1000 --profile aztrg5w",
      "dimensions": "91:51",
      "created": "2024-12-14",
      "tags": ["portrait", "cyberpunk", "cinematic", "sci-fi", "woman", "comic", "neon", "city"]
    },
    {
      "id": "9c76a821-7461-4d02-abc3-a09b685fe73d",
      "name": "Cyberpunk Hover Bike",
      "type": "image",
      "source": "midjourney",
      "url": "https://www.midjourney.com/jobs/9c76a821-7461-4d02-abc3-a09b685fe73d?index=0",
      "cdn_url": "https://cdn.midjourney.com/9c76a821-7461-4d02-abc3-a09b685fe73d/0_0.png",
      "prompt": "cinematic still of a sleek industrial black hover bike with a rider in matte black armor, desert terrain with scattered debris, dust trails behind the vehicle, low camera angle emphasizing speed and power, dramatic motion blur on background, golden hour lighting with warm amber tones, photorealistic rendering, high detail mechanical parts, weathered and battle-worn aesthetic",
      "parameters": "--ar 21:9 --style raw --stylize 300 --profile aztrg5w",
      "dimensions": "21:9",
      "created": "2024-12-14",
      "tags": ["sci-fi", "cinematic", "vehicle", "landscape", "desert", "action", "futuristic"]
    },
    {
      "id": "5cd9687f-59b6-4688-ae38-bed536dd4a3e",
      "name": "Man Winking",
      "type": "video",
      "source": "midjourney",
      "url": "https://www.midjourney.com/jobs/5cd9687f-59b6-4688-ae38-bed536dd4a3e?index=0",
      "cdn_url": "https://cdn.midjourney.com/5cd9687f-59b6-4688-ae38-bed536dd4a3e/0_0.mp4",
      "prompt": "man looks at camera, winks, smiles",
      "parameters": "--duration 5s --profile aztrg5w",
      "dimensions": "video",
      "created": "2024-12-14",
      "tags": ["portrait", "video", "man", "animation"]
    }
  ]
};

// State
let items = [];
let activeTag = null;
let currentModalIndex = -1;
let filteredItems = [];

// DOM elements
const gallery = document.getElementById('gallery');
const modal = document.getElementById('modal');
const modalMedia = document.getElementById('modal-media');
const modalTitle = document.getElementById('modal-title');
const modalPrompt = document.getElementById('modal-prompt');
const modalParams = document.getElementById('modal-params');
const modalType = document.getElementById('modal-type');
const modalDimensions = document.getElementById('modal-dimensions');
const modalDate = document.getElementById('modal-date');
const modalTags = document.getElementById('modal-tags');
const modalLink = document.getElementById('modal-link');
const closeBtn = document.querySelector('.close');
const prevBtn = document.getElementById('modal-prev');
const nextBtn = document.getElementById('modal-next');
const searchInput = document.getElementById('search');
const dateFilter = document.getElementById('date-filter');
const typeFilter = document.getElementById('type-filter');
const tagsBar = document.getElementById('tags-bar');
const resultsCount = document.getElementById('results-count');

// Load data - try fetch first (for served files), fall back to embedded (for file://)
async function loadData() {
    try {
        const response = await fetch('data/gallery.json');
        if (response.ok) {
            const data = await response.json();
            items = data.items;
        } else {
            throw new Error('Fetch failed');
        }
    } catch (error) {
        // Fall back to embedded data for local file:// access
        console.log('Using embedded data (local mode)');
        items = embeddedData.items;
    }
    initTags();
    renderGallery();
}

// Get all unique tags
function getAllTags() {
    const tagSet = new Set();
    items.forEach(item => item.tags.forEach(tag => tagSet.add(tag)));
    return Array.from(tagSet).sort();
}

// Initialize tag buttons
function initTags() {
    const tags = getAllTags();
    tagsBar.innerHTML = tags.map(tag =>
        `<button class="tag-btn" data-tag="${tag}">${tag}</button>`
    ).join('');

    tagsBar.querySelectorAll('.tag-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tag = btn.dataset.tag;
            if (activeTag === tag) {
                activeTag = null;
                btn.classList.remove('active');
            } else {
                tagsBar.querySelectorAll('.tag-btn').forEach(b => b.classList.remove('active'));
                activeTag = tag;
                btn.classList.add('active');
            }
            renderGallery();
        });
    });
}

// Filter items
function getFilteredItems() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    const dateValue = dateFilter.value; // YYYY-MM format
    const typeValue = typeFilter.value;

    return items.filter(item => {
        // Type filter
        if (typeValue !== 'all' && item.type !== typeValue) return false;

        // Tag filter
        if (activeTag && !item.tags.includes(activeTag)) return false;

        // Date filter (by month)
        if (dateValue) {
            const itemMonth = item.created.substring(0, 7); // YYYY-MM
            if (itemMonth !== dateValue) return false;
        }

        // Keyword search (searches name, prompt, and tags)
        if (searchTerm) {
            const searchable = [
                item.name,
                item.prompt,
                ...item.tags
            ].join(' ').toLowerCase();
            if (!searchable.includes(searchTerm)) return false;
        }

        return true;
    });
}

// Render gallery
function renderGallery() {
    filteredItems = getFilteredItems();

    // Update count
    resultsCount.textContent = `${filteredItems.length} ${filteredItems.length === 1 ? 'item' : 'items'}`;

    if (filteredItems.length === 0) {
        gallery.innerHTML = '<div class="empty-state"><h3>No results found</h3><p>Try adjusting your search or filters</p></div>';
        return;
    }

    gallery.innerHTML = filteredItems.map((item, index) => {
        let mediaHtml = '';
        let badgeHtml = '';
        let overlayHtml = '';

        if (item.type === 'video') {
            // For Midjourney videos, the thumbnail is at 0_0_thumbnail_00001.webp or similar
            // Try multiple thumbnail patterns
            const thumbBase = item.cdn_url.replace('/0_0.mp4', '');
            const videoThumb = `${thumbBase}/0_0_thumbnail_00001.webp`;
            const fallbackThumb = item.cdn_url.replace('.mp4', '.webp');
            mediaHtml = `<img src="${videoThumb}" alt="${item.name}" loading="lazy"
                onerror="this.onerror=null; this.src='${fallbackThumb}';">`;
            badgeHtml = '<div class="video-play-icon"></div>';
        } else if (item.type === 'music') {
            // For music, use album art if available, otherwise placeholder
            if (item.thumbnail_url) {
                mediaHtml = `<img src="${item.thumbnail_url}" alt="${item.name}" loading="lazy">`;
            } else {
                mediaHtml = '<div class="music-placeholder">&#127925;</div>';
            }
            badgeHtml = '<span class="type-badge music">music</span>';
        } else {
            mediaHtml = `<img src="${item.cdn_url}" alt="${item.name}" loading="lazy">`;
        }

        overlayHtml = `
            <div class="overlay">
                <div class="title">${item.name}</div>
                <div class="meta">${item.dimensions} · ${item.created}</div>
            </div>
        `;

        return `
        <div class="gallery-item" data-id="${item.id}" data-index="${index}">
            ${badgeHtml}
            ${mediaHtml}
            ${overlayHtml}
        </div>
    `}).join('');

    // Add click handlers
    gallery.querySelectorAll('.gallery-item').forEach(el => {
        el.addEventListener('click', () => {
            const index = parseInt(el.dataset.index);
            openModal(filteredItems[index], index);
        });
    });
}

// Open modal
function openModal(item, index) {
    currentModalIndex = index;

    // Set media
    if (item.type === 'video') {
        // Use proper video element with controls
        modalMedia.innerHTML = `<video src="${item.cdn_url}" controls autoplay loop playsinline>
            Your browser does not support video playback.
        </video>`;
    } else if (item.type === 'music') {
        // For Suno music with video, show video player
        if (item.cdn_url && item.cdn_url.endsWith('.mp4')) {
            modalMedia.innerHTML = `<video src="${item.cdn_url}" controls autoplay loop playsinline>
                Your browser does not support video playback.
            </video>`;
        } else {
            modalMedia.innerHTML = `<audio src="${item.cdn_url}" controls autoplay></audio>`;
        }
    } else {
        modalMedia.innerHTML = `<img src="${item.cdn_url}" alt="${item.name}">`;
    }

    modalTitle.textContent = item.name;
    modalType.textContent = item.type;
    modalDimensions.textContent = item.dimensions;
    modalDate.textContent = item.created;

    // Create clickable tags
    modalTags.innerHTML = item.tags.map(t => `<span data-tag="${t}">${t}</span>`).join('');

    // Add click handlers to tags
    modalTags.querySelectorAll('span').forEach(tagEl => {
        tagEl.addEventListener('click', () => {
            const tag = tagEl.dataset.tag;
            closeModal();
            filterByTag(tag);
        });
    });

    modalPrompt.textContent = item.prompt || '';
    modalParams.textContent = item.parameters || '';

    if (item.url) {
        modalLink.href = item.url;
        modalLink.style.display = 'inline-block';

        // Dynamic link text based on source
        if (item.source === 'midjourney') {
            modalLink.textContent = 'View on Midjourney';
        } else if (item.source === 'suno') {
            modalLink.textContent = 'View on Suno';
        } else {
            modalLink.textContent = 'View Source';
        }
    } else {
        modalLink.style.display = 'none';
    }

    // Update navigation buttons
    updateNavButtons();

    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

// Filter by tag (called from modal tag click)
function filterByTag(tag) {
    // Set the active tag
    activeTag = tag;

    // Update tag bar to show active state
    tagsBar.querySelectorAll('.tag-btn').forEach(btn => {
        if (btn.dataset.tag === tag) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Re-render gallery with filter
    renderGallery();

    // Scroll to top of gallery
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Update navigation button states
function updateNavButtons() {
    prevBtn.disabled = currentModalIndex <= 0;
    nextBtn.disabled = currentModalIndex >= filteredItems.length - 1;
}

// Navigate to previous item
function showPrevious() {
    if (currentModalIndex > 0) {
        currentModalIndex--;
        openModal(filteredItems[currentModalIndex], currentModalIndex);
    }
}

// Navigate to next item
function showNext() {
    if (currentModalIndex < filteredItems.length - 1) {
        currentModalIndex++;
        openModal(filteredItems[currentModalIndex], currentModalIndex);
    }
}

// Close modal
function closeModal() {
    modal.classList.remove('active');
    document.body.style.overflow = '';
    modalMedia.innerHTML = '';
}

// Event listeners
closeBtn.addEventListener('click', closeModal);
prevBtn.addEventListener('click', showPrevious);
nextBtn.addEventListener('click', showNext);

modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
});

document.addEventListener('keydown', (e) => {
    if (!modal.classList.contains('active')) return;

    if (e.key === 'Escape') closeModal();
    if (e.key === 'ArrowLeft') showPrevious();
    if (e.key === 'ArrowRight') showNext();
});

// Search and filter listeners with debounce
let searchTimeout;
searchInput.addEventListener('input', () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(renderGallery, 200);
});

dateFilter.addEventListener('change', renderGallery);
typeFilter.addEventListener('change', renderGallery);

// Initialize
loadData();
