// FIXED getFilteredItems function with aspect ratio filter and sorting
function getFilteredItems() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    const typeValue = typeFilter.value;
    const dateValue = dateFilter.value;
    const modelValue = modelFilter.value;
    const sortValue = sortFilter ? sortFilter.value : 'newest';
    const aspectValue = aspectFilter ? aspectFilter.value : '';

    let filtered = items.filter(item => {
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

        // Aspect ratio filter
        if (aspectValue && item.dimensions !== aspectValue) return false;

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

    // Apply sorting
    switch(sortValue) {
        case 'oldest':
            filtered.sort((a, b) => new Date(a.created) - new Date(b.created));
            break;
        case 'name-asc':
            filtered.sort((a, b) => a.name.localeCompare(b.name));
            break;
        case 'name-desc':
            filtered.sort((a, b) => b.name.localeCompare(a.name));
            break;
        case 'newest':
        default:
            filtered.sort((a, b) => new Date(b.created) - new Date(a.created));
            break;
    }

    return filtered;
}

// Event listeners to add
sortFilter.addEventListener('change', () => {
    currentPage = 1;
    renderGallery();
});

aspectFilter.addEventListener('change', () => {
    currentPage = 1;
    renderGallery();
});

// Update reset filters to include new filters
resetBtn.addEventListener('click', () => {
    searchInput.value = '';
    typeFilter.value = 'all';
    dateFilter.value = '';
    modelFilter.value = '';
    if (sortFilter) sortFilter.value = 'newest';
    if (aspectFilter) aspectFilter.value = '';
    activeTag = null;
    currentPage = 1;
    renderGallery();
});
