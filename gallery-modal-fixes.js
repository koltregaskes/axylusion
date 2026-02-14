// ============================================================================
// GALLERY MODAL FIXES
// ============================================================================
// This file contains fixes for:
// 1. Gallery->image transition jolt (smooth fade transitions)
// 2. Image page scroll resistance (better metadata scroll detection)
// 3. Click-to-fullscreen on images
// 4. Metadata display improvements (show empty state properly)
// ============================================================================

// FIX 1: Smooth transitions for modal opening/closing
// Add CSS transition and prevent layout shift
function openModalSmooth(item, index, pushHistory = true) {
    currentModalIndex = index;

    // Update URL for back button support
    if (pushHistory) {
        updateURL(item);
    }

    // Pre-load image before showing modal to prevent jolt
    if (item.type === 'image') {
        const img = new Image();
        img.onload = () => {
            setModalContent(item);
            modal.classList.add('active');
            // Add slight delay to ensure smooth fade-in
            requestAnimationFrame(() => {
                modal.classList.add('loaded');
            });
        };
        img.src = item.cdn_url;
    } else {
        setModalContent(item);
        modal.classList.add('active');
        requestAnimationFrame(() => {
            modal.classList.add('loaded');
        });
    }

    document.body.style.overflow = 'hidden';
}

// Separate function to set modal content
function setModalContent(item) {
    // Set media
    if (item.type === 'video') {
        modalMedia.innerHTML = `
            <video src="${item.cdn_url}" controls autoplay loop playsinline
                onerror="this.outerHTML='<div class=\\'video-error\\'>Video unavailable. <a href=\\'${item.url}\\' target=\\'_blank\\'>View on Midjourney</a></div>'">
                Your browser does not support video playback.
            </video>`;
    } else if (item.type === 'music') {
        if (item.cdn_url && item.cdn_url.endsWith('.mp4')) {
            modalMedia.innerHTML = `<video src="${item.cdn_url}" controls autoplay loop playsinline>
                Your browser does not support video playback.
            </video>`;
        } else {
            modalMedia.innerHTML = `<audio src="${item.cdn_url}" controls autoplay></audio>`;
        }
    } else {
        // FIX 3: Add click-to-fullscreen on images
        modalMedia.innerHTML = `<img src="${item.cdn_url}" alt="" class="modal-image" style="cursor: zoom-in;">`;

        // Add fullscreen click handler
        const modalImage = modalMedia.querySelector('img');
        if (modalImage) {
            modalImage.addEventListener('click', (e) => {
                e.stopPropagation(); // Prevent modal close
                toggleFullscreen(modalImage);
            });
        }
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

    // FIX 4: Better metadata display - show "Not available" instead of empty
    modalPrompt.textContent = item.prompt || 'Not available';
    modalParams.textContent = item.parameters || 'Not available';

    if (item.url) {
        modalLink.href = item.url;
        modalLink.style.display = 'inline-block';

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

    updateNavButtons();
}

// FIX 3: Fullscreen toggle function
function toggleFullscreen(element) {
    if (!document.fullscreenElement) {
        element.requestFullscreen().catch(err => {
            console.error('Error attempting to enable fullscreen:', err);
        });
        element.style.cursor = 'zoom-out';
    } else {
        document.exitFullscreen();
        element.style.cursor = 'zoom-in';
    }
}

// Listen for fullscreen changes to update cursor
document.addEventListener('fullscreenchange', () => {
    const modalImage = modalMedia.querySelector('img');
    if (modalImage) {
        modalImage.style.cursor = document.fullscreenElement ? 'zoom-out' : 'zoom-in';
    }
});

// Smooth close with fade-out
function closeModalSmooth(pushHistory = true) {
    modal.classList.remove('loaded');

    // Wait for fade-out transition before removing 'active'
    setTimeout(() => {
        modal.classList.remove('active');
        document.body.style.overflow = '';
        modalMedia.innerHTML = '';

        if (pushHistory) {
            updateURL(null);
        }
    }, 200); // Match CSS transition duration
}

// FIX 2: Improved scroll detection for metadata area
// More reliable detection of whether cursor is over scrollable content
modal.addEventListener('wheel', (e) => {
    if (!modal.classList.contains('active')) return;

    const mediaWrapper = document.querySelector('.modal-media-wrapper');
    const modalInfo = document.querySelector('.modal-info');

    if (!mediaWrapper || !modalInfo) return;

    // Check if cursor is over the metadata/info area
    const infoRect = modalInfo.getBoundingClientRect();
    const isOverMetadata = (
        e.clientX >= infoRect.left && e.clientX <= infoRect.right &&
        e.clientY >= infoRect.top && e.clientY <= infoRect.bottom
    );

    // If over metadata area, check if it's actually scrollable
    if (isOverMetadata) {
        const hasScroll = modalInfo.scrollHeight > modalInfo.clientHeight;
        const atTop = modalInfo.scrollTop === 0;
        const atBottom = modalInfo.scrollTop + modalInfo.clientHeight >= modalInfo.scrollHeight - 1;

        // Only allow image navigation if:
        // - No scrollable content, OR
        // - Scrolling up at top, OR
        // - Scrolling down at bottom
        const scrollingUp = e.deltaY < 0;
        const scrollingDown = e.deltaY > 0;

        const shouldNavigateImages = !hasScroll ||
                                    (scrollingUp && atTop) ||
                                    (scrollingDown && atBottom);

        if (!shouldNavigateImages) {
            // Let natural scroll happen in metadata
            return;
        }
    }

    // Over image area or at scroll boundaries: navigate images
    e.preventDefault();
    scrollAccumulator += e.deltaY;

    if (scrollAccumulator > SCROLL_THRESHOLD) {
        showNext();
        scrollAccumulator = 0;
    } else if (scrollAccumulator < -SCROLL_THRESHOLD) {
        showPrevious();
        scrollAccumulator = 0;
    }
}, { passive: false });

// Add CSS for smooth transitions
const style = document.createElement('style');
style.textContent = `
    /* Smooth modal transitions */
    .modal {
        opacity: 0;
        transition: opacity 0.2s ease-in-out;
        pointer-events: none;
    }

    .modal.active {
        opacity: 1;
        pointer-events: auto;
    }

    .modal.loaded .modal-content {
        transform: scale(1);
    }

    .modal-content {
        transform: scale(0.95);
        transition: transform 0.2s ease-out;
    }

    /* Smooth image loading */
    .modal-image {
        animation: fadeIn 0.15s ease-in;
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }

    /* Fullscreen image styling */
    .modal-image:fullscreen {
        object-fit: contain;
        width: 100%;
        height: 100%;
        background: #000;
    }

    /* Better metadata empty state */
    .modal-prompt:empty::before,
    .modal-params:empty::before {
        content: 'Not available';
        color: #999;
        font-style: italic;
    }
`;
document.head.appendChild(style);
