// Gallery data - embedded for local file:// access, also loads from data/gallery.json when served
const embeddedData = {
  "items": [
    {
      "id": "e055ca01-1d3c-433c-80f3-aa4818322225",
      "name": "Fantasy Heroine - Red Hair",
      "type": "image",
      "source": "midjourney",
      "model": "Midjourney v7",
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
      "model": "Midjourney v7",
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
      "model": "Midjourney v7",
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
      "model": "Midjourney v7",
      "url": "https://www.midjourney.com/jobs/9c76a821-7461-4d02-abc3-a09b685fe73d?index=0",
      "cdn_url": "https://cdn.midjourney.com/9c76a821-7461-4d02-abc3-a09b685fe73d/0_0.png",
      "prompt": "cinematic still of a sleek industrial black hover bike with a rider in matte black armor, desert terrain with scattered debris, dust trails behind the vehicle, low camera angle emphasizing speed and power, dramatic motion blur on background, golden hour lighting with warm amber tones, photorealistic rendering, high detail mechanical parts, weathered and battle-worn aesthetic",
      "parameters": "--ar 21:9 --style raw --stylize 300 --profile aztrg5w",
      "dimensions": "21:9",
      "created": "2024-12-14",
      "tags": ["sci-fi", "cinematic", "vehicle", "landscape", "desert", "action", "futuristic"]
    }
  ]
};

// State
let items = [];
let activeTag = null;
let currentModalIndex = -1;
let filteredItems = [];
let currentPage = 1;
const ITEMS_PER_PAGE = 30;

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
const typeFilter = document.getElementById('type-filter');
const dateFilter = document.getElementById('date-filter');
const modelFilter = document.getElementById('model-filter');
const resetBtn = document.getElementById('reset-filters');
const pagination = document.getElementById('pagination');

// URL History management
function updateURL(item) {
    if (item) {
        const url = new URL(window.location);
        url.searchParams.set('view', item.id);
        window.history.pushState({ itemId: item.id }, '', url);
    } else {
        const url = new URL(window.location);
        url.searchParams.delete('view');
        window.history.pushState({}, '', url);
    }
}

// Handle browser back/forward
window.addEventListener('popstate', (e) => {
    const url = new URL(window.location);
    const viewId = url.searchParams.get('view');

    if (viewId) {
        const item = items.find(i => i.id === viewId);
        if (item) {
            const index = filteredItems.indexOf(item);
            if (index !== -1) {
                openModal(item, index, false); // false = don't push to history
            }
        }
    } else {
        closeModal(false); // false = don't push to history
    }
});

// Check URL on load
function checkURLOnLoad() {
    const url = new URL(window.location);
    const viewId = url.searchParams.get('view');

    if (viewId) {
        const item = items.find(i => i.id === viewId);
        if (item) {
            const index = filteredItems.indexOf(item);
            if (index !== -1) {
                openModal(item, index, false);
            }
        }
    }
}

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
    // Sort by date descending (newest first)
    items.sort((a, b) => new Date(b.created) - new Date(a.created));

    // Populate date filter with available years
    populateDateFilter();

    // Populate model filter with available models
    populateModelFilter();

    renderGallery();
    checkURLOnLoad();
}

// Populate date filter dropdown
function populateDateFilter() {
    const years = new Set();
    items.forEach(item => {
        const year = item.created.substring(0, 4);
        years.add(year);
    });

    const sortedYears = Array.from(years).sort((a, b) => b - a);

    dateFilter.innerHTML = '<option value="">All Time</option>';
    sortedYears.forEach(year => {
        dateFilter.innerHTML += `<option value="${year}">${year}</option>`;
    });
}

// Populate model filter dropdown
function populateModelFilter() {
    const models = new Set();
    items.forEach(item => {
        if (item.model) {
            models.add(item.model);
        }
    });

    const sortedModels = Array.from(models).sort();

    modelFilter.innerHTML = '<option value="">All Models</option>';
    sortedModels.forEach(model => {
        modelFilter.innerHTML += `<option value="${model}">${model}</option>`;
    });
}

// Filter items
function getFilteredItems() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    const typeValue = typeFilter.value;
    const dateValue = dateFilter.value;
    const modelValue = modelFilter.value;

    return items.filter(item => {
        // Type filter
        if (typeValue !== 'all' && item.type !== typeValue) return false;

        // Tag filter
        if (activeTag && !item.tags.includes(activeTag)) return false;

        // Date filter (by year)
        if (dateValue) {
            const itemYear = item.created.substring(0, 4);
            if (itemYear !== dateValue) return false;
        }

        // Model filter
        if (modelValue && item.model !== modelValue) return false;

        // Keyword search (searches name, prompt, tags, and model)
        if (searchTerm) {
            const searchable = [
                item.name,
                item.prompt,
                item.model || '',
                ...item.tags
            ].join(' ').toLowerCase();
            if (!searchable.includes(searchTerm)) return false;
        }

        return true;
    });
}

// Get paginated items
function getPaginatedItems() {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = startIndex + ITEMS_PER_PAGE;
    return filteredItems.slice(startIndex, endIndex);
}

// Get total pages
function getTotalPages() {
    return Math.ceil(filteredItems.length / ITEMS_PER_PAGE);
}

// Render pagination
function renderPagination() {
    const totalPages = getTotalPages();

    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let html = '';

    // Previous button
    html += `<button ${currentPage === 1 ? 'disabled' : ''} data-page="${currentPage - 1}">Previous</button>`;

    // Page numbers - show max 5 pages around current
    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);

    if (endPage - startPage < maxVisible - 1) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }

    if (startPage > 1) {
        html += `<button data-page="1">1</button>`;
        if (startPage > 2) html += `<span class="pagination-info">...</span>`;
    }

    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) html += `<span class="pagination-info">...</span>`;
        html += `<button data-page="${totalPages}">${totalPages}</button>`;
    }

    // Next button
    html += `<button ${currentPage === totalPages ? 'disabled' : ''} data-page="${currentPage + 1}">Next</button>`;

    pagination.innerHTML = html;

    // Add click handlers
    pagination.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => {
            const page = parseInt(btn.dataset.page);
            if (page && page !== currentPage) {
                currentPage = page;
                renderGallery();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        });
    });
}

// Render gallery
function renderGallery() {
    filteredItems = getFilteredItems();
    const paginatedItems = getPaginatedItems();

    if (filteredItems.length === 0) {
        gallery.innerHTML = '<div class="empty-state"><h3>No results found</h3><p>Try adjusting your search or filters</p></div>';
        pagination.innerHTML = '';
        return;
    }

    // Calculate the starting index for the current page
    const pageStartIndex = (currentPage - 1) * ITEMS_PER_PAGE;

    gallery.innerHTML = paginatedItems.map((item, localIndex) => {
        const index = pageStartIndex + localIndex;
        let mediaHtml = '';
        let badgeHtml = '';
        let overlayHtml = '';

        if (item.type === 'video') {
            // For videos, use thumbnail_url if provided, otherwise show placeholder
            if (item.thumbnail_url) {
                mediaHtml = `<img src="${item.thumbnail_url}" alt="${item.name}" loading="lazy">`;
            } else {
                // Video placeholder with play icon
                mediaHtml = '<div class="video-placeholder"></div>';
            }
            badgeHtml = '<div class="video-play-icon"></div>';
        } else if (item.type === 'music') {
            // For music, use thumbnail_url if available, otherwise placeholder
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

    // Render pagination
    renderPagination();
}

// Open modal
function openModal(item, index, pushHistory = true) {
    currentModalIndex = index;

    // Update URL for back button support
    if (pushHistory) {
        updateURL(item);
    }

    // Set media
    if (item.type === 'video') {
        // Check if CDN URL is accessible - show message if not
        modalMedia.innerHTML = `
            <video src="${item.cdn_url}" controls autoplay loop playsinline
                onerror="this.outerHTML='<div class=\\'video-error\\'>Video unavailable. <a href=\\'${item.url}\\' target=\\'_blank\\'>View on Midjourney</a></div>'">
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
    modalType.textContent = item.model || item.type;
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
    currentPage = 1;

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
function closeModal(pushHistory = true) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
    modalMedia.innerHTML = '';

    if (pushHistory) {
        updateURL(null);
    }
}

// Event listeners
closeBtn.addEventListener('click', () => closeModal());
prevBtn.addEventListener('click', showPrevious);
nextBtn.addEventListener('click', showNext);

modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
});

// Keyboard navigation
document.addEventListener('keydown', (e) => {
    if (!modal.classList.contains('active')) return;

    if (e.key === 'Escape') closeModal();
    if (e.key === 'ArrowLeft') showPrevious();
    if (e.key === 'ArrowRight') showNext();
});

// Mouse wheel navigation in modal
modal.addEventListener('wheel', (e) => {
    if (!modal.classList.contains('active')) return;

    // Prevent default scroll
    e.preventDefault();

    if (e.deltaY > 0) {
        // Scroll down = next
        showNext();
    } else if (e.deltaY < 0) {
        // Scroll up = previous
        showPrevious();
    }
}, { passive: false });

// Search and filter listeners with debounce
let searchTimeout;
searchInput.addEventListener('input', () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        currentPage = 1;
        renderGallery();
    }, 200);
});

typeFilter.addEventListener('change', () => {
    currentPage = 1;
    renderGallery();
});

dateFilter.addEventListener('change', () => {
    currentPage = 1;
    renderGallery();
});

modelFilter.addEventListener('change', () => {
    currentPage = 1;
    renderGallery();
});

// Reset all filters
resetBtn.addEventListener('click', () => {
    searchInput.value = '';
    typeFilter.value = 'all';
    dateFilter.value = '';
    modelFilter.value = '';
    activeTag = null;
    currentPage = 1;
    renderGallery();
});

// Initialize
loadData();
