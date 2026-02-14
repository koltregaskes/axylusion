// Shared data loader for gallery.json
// This script loads gallery data and makes it available as window.galleryData
// Used by both index.html (homepage) and gallery.html

(async function() {
    try {
        const response = await fetch('data/gallery.json');
        if (response.ok) {
            const data = await response.json();
            window.galleryData = data;

            // Also create embeddedData for backward compatibility
            window.embeddedData = data;

            // Dispatch event so other scripts know data is loaded
            window.dispatchEvent(new CustomEvent('galleryDataLoaded', { detail: data }));

            console.log(`Gallery data loaded: ${data.items.length} items`);
        } else {
            console.error('Failed to load gallery data:', response.status);
        }
    } catch (error) {
        console.error('Error loading gallery data:', error);
    }
})();
