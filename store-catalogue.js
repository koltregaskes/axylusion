(() => {
    const catalogueRoot = document.querySelector('[data-music-catalogue]');
    if (!catalogueRoot) return;

    const dataUrl = catalogueRoot.dataset.catalogueUrl;

    function appendTextElement(parent, tagName, text, className) {
        const element = document.createElement(tagName);
        if (className) element.className = className;
        element.textContent = text;
        parent.append(element);
        return element;
    }

    function renderCard(item) {
        const card = document.createElement('article');
        card.className = 'store-product-card';

        const topline = document.createElement('div');
        topline.className = 'store-product-topline';
        appendTextElement(topline, 'span', item.type);
        appendTextElement(topline, 'span', item.duration);
        card.append(topline);

        appendTextElement(card, 'h2', item.title);
        appendTextElement(card, 'p', item.description);

        const pills = document.createElement('div');
        pills.className = 'store-pill-row';
        pills.setAttribute('aria-label', `${item.title} labels`);
        item.labels.forEach((label) => appendTextElement(pills, 'span', label));
        card.append(pills);

        const metadata = document.createElement('dl');
        metadata.className = 'store-product-meta';
        const useCaseRow = document.createElement('div');
        appendTextElement(useCaseRow, 'dt', 'Good for');
        appendTextElement(useCaseRow, 'dd', item.useCases.join(', '));
        metadata.append(useCaseRow);
        const marketplaceRow = document.createElement('div');
        appendTextElement(marketplaceRow, 'dt', 'Marketplace');
        appendTextElement(marketplaceRow, 'dd', 'ElevenLabs');
        metadata.append(marketplaceRow);
        card.append(metadata);

        const link = appendTextElement(card, 'a', 'Open on ElevenLabs', 'cta-button primary');
        link.href = item.url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';

        return card;
    }

    fetch(dataUrl, { credentials: 'same-origin' })
        .then((response) => {
            if (!response.ok) throw new Error(`Catalogue request failed: ${response.status}`);
            return response.json();
        })
        .then((catalogue) => {
            if (catalogue.schemaVersion !== 1 || !Array.isArray(catalogue.items) || catalogue.items.length === 0) {
                throw new Error('Catalogue schema is invalid.');
            }
            catalogueRoot.replaceChildren(...catalogue.items.map(renderCard));
        })
        .catch((error) => {
            console.error('Could not refresh the music catalogue; keeping the static fallback.', error);
        });
})();
