/**
 * AI News App - Axy Lusion
 * Dynamic news feed from markdown digest files
 * Adapted from Kol's Korner (koltregaskes.com)
 */

class NewsApp {
    constructor() {
        this.articles = [];
        this.filteredArticles = [];
        this.sources = new Set();
        this.decoder = document.createElement('textarea');
        this.favorites = new Set(this.loadStoredFavorites());
        this.init();
    }

    loadStoredFavorites() {
        try {
            const rawValue = window.localStorage.getItem('axyl-news-favorites');
            const parsedValue = JSON.parse(rawValue || '[]');
            return Array.isArray(parsedValue) ? parsedValue : [];
        } catch (_error) {
            return [];
        }
    }

    saveStoredFavorites() {
        try {
            window.localStorage.setItem('axyl-news-favorites', JSON.stringify(Array.from(this.favorites)));
        } catch (_error) {
            // Ignore storage failures so the page still works in strict privacy contexts.
        }
    }

    async init() {
        await this.loadArticles();
        this.setupEventListeners();

        const today = new Date();
        const lastWeek = new Date();
        lastWeek.setDate(today.getDate() - 7);

        const fromDate = document.getElementById('fromDate');
        const toDate = document.getElementById('toDate');
        const hasRecentArticles = this.articles.some(article => {
            const articleDate = new Date(article.date);
            return articleDate >= lastWeek && articleDate <= today;
        });

        if (hasRecentArticles) {
            if (fromDate) fromDate.value = lastWeek.toISOString().split('T')[0];
            if (toDate) toDate.value = today.toISOString().split('T')[0];
            this.updateQuickFilterButtons('week');
        } else {
            if (fromDate) fromDate.value = '';
            if (toDate) toDate.value = '';
            this.updateQuickFilterButtons('all');
        }

        this.filterArticles();
    }

    async loadArticles() {
        const fileList = await this.loadDigestList();

        const loadPromises = fileList.map(async (filename) => {
            try {
                const response = await fetch(`news-digests/${filename}`);
                if (response.ok) {
                    const rawContent = await response.text();
                    const content = this.repairDigestContent(rawContent);
                    return this.parseDigest(content, filename);
                }
            } catch (e) {
                // File doesn't exist, skip
            }
            return [];
        });

        const results = await Promise.all(loadPromises);
        results.forEach(articles => this.articles.push(...articles));

        this.articles.sort((a, b) => new Date(b.date) - new Date(a.date));
        this.filteredArticles = [...this.articles];
        this.populateFilters();
        this.updateOverview();

        const loading = document.getElementById('loading');
        if (loading) loading.style.display = 'none';
    }

    async loadDigestList() {
        const manifestFiles = [];

        try {
            const response = await fetch('news-digests/index.json', { cache: 'no-store' });
            if (response.ok) {
                const payload = await response.json();
                if (Array.isArray(payload.files)) {
                    manifestFiles.push(...payload.files);
                }
            }
        } catch (error) {
            console.warn('News digest manifest unavailable, falling back to generated date scan.', error);
        }

        if (manifestFiles.length > 0) {
            return this.sortDigestFiles(manifestFiles);
        }

        return this.sortDigestFiles(this.generateFileList());
    }

    generateFileList() {
        const files = [];
        const today = new Date();

        for (let i = 0; i < 120; i++) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');

            files.push(`${year}-${month}-${day}-digest.md`);
            files.push(`digest-${year}-${month}-${day}.md`);
        }

        return files;
    }

    sortDigestFiles(files) {
        return Array.from(new Set(files))
            .filter(filename => this.getDigestDate(filename))
            .sort((left, right) => {
                const leftDate = this.getDigestDate(left);
                const rightDate = this.getDigestDate(right);
                return rightDate - leftDate || left.localeCompare(right);
            });
    }

    parseDigest(content, filename) {
        const fileDate = this.getDigestDate(filename);
        if (!fileDate) return [];

        if (/^##\s+\[/m.test(content)) {
            return this.parsePublishedDigest(content, fileDate);
        }

        if (/^###\s+\d+\.\s+/m.test(content)) {
            return this.parseStructuredDigest(content, fileDate);
        }

        return [];
    }

    getDigestDate(filename) {
        const match = String(filename).match(/(?:(\d{4})-(\d{2})-(\d{2})-digest|digest-(\d{4})-(\d{2})-(\d{2}))\.md$/);
        if (!match) return null;

        const year = Number(match[1] || match[4]);
        const month = Number(match[2] || match[5]);
        const day = Number(match[3] || match[6]);
        return new Date(year, month - 1, day);
    }

    parsePublishedDigest(content, fileDate) {
        const articles = [];
        const fallbackDateString = this.formatLongDate(fileDate);
        const blocks = content.replace(/\r/g, '').split(/\n-{3,}\n+/);
        let articleCount = 0;

        blocks.forEach((block) => {
            const headingMatch = block.match(/^##\s+\[([\s\S]+?)\]\((https?:\/\/[^\s)]+)\)/m);
            if (!headingMatch) return;

            const [, rawTitle, url] = headingMatch;
            if (this.isJunkItem(rawTitle, url)) return;

            articleCount++;

            const title = this.normalizeText(
                rawTitle
                    .split('\n')
                    .map(line => line.trim())
                    .find(Boolean) || rawTitle
            );

            const metadataMatch = block.match(/^\*(.+?)\*(?:\s*\|\s*([^|\n]+))?(?:\s*\|\s*Score:\s*[0-9.]+)?$/m);
            const source = this.normalizeText(
                metadataMatch && metadataMatch[1] ? metadataMatch[1] : this.extractSource(url)
            );

            let articleDate = fileDate;
            let articleDateString = fallbackDateString;
            if (metadataMatch && metadataMatch[2] && !/score:/i.test(metadataMatch[2])) {
                const parsed = this.parseArticleDate(metadataMatch[2], fileDate);
                articleDate = parsed.date;
                articleDateString = parsed.dateString;
            }

            const tagMatch = block.match(/^Tags:\s*(.+)$/m);
            const summaryBody = block
                .replace(headingMatch[0], '')
                .replace(metadataMatch ? metadataMatch[0] : '', '')
                .replace(tagMatch ? tagMatch[0] : '');
            const quotedSummary = summaryBody
                .split('\n')
                .filter(line => line.trim().startsWith('>'))
                .map(line => line.replace(/^\s*>\s?/, '').trim())
                .join('\n');
            const summary = this.buildSummary(quotedSummary || summaryBody);
            const tags = tagMatch
                ? tagMatch[1]
                    .split(',')
                    .map(tag => this.normalizeText(tag))
                    .filter(Boolean)
                    .slice(0, 5)
                : this.generateTags(rawTitle, summary);

            articles.push(this.buildArticle({
                title,
                source,
                url,
                summary,
                category: articleCount <= 5 ? 'Top Stories' : 'News',
                date: articleDate,
                dateString: articleDateString,
                tags
            }));
        });

        return articles;
    }

    parseStructuredDigest(content, fileDate) {
        const articles = [];
        const fallbackDateString = this.formatLongDate(fileDate);
        const lines = content.replace(/\r/g, '').split('\n');
        let currentSection = 'Top Stories';

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            const sectionMatch = line.match(/^##\s+(.+)$/);
            if (sectionMatch && !sectionMatch[1].startsWith('[')) {
                currentSection = this.normalizeText(sectionMatch[1]);
                continue;
            }

            const titleMatch = line.match(/^###\s+\d+\.\s+(.+)$/);
            if (!titleMatch) continue;

            const title = this.normalizeText(titleMatch[1]);
            let source = 'Unknown';
            let url = '';
            let summary = '';
            let category = this.getCategoryFromSection(currentSection, articles.length + 1);
            let articleDate = fileDate;
            let articleDateString = fallbackDateString;
            let j = i + 1;

            while (j < lines.length) {
                const nextLine = lines[j].trim();

                if (/^###\s+\d+\.\s+/.test(nextLine) || (/^##\s+/.test(nextLine) && !nextLine.startsWith('## ['))) {
                    break;
                }

                const metadataMatch = nextLine.match(/^\*\*Category:\*\*\s*(.*?)\s*\|\s*\*\*Source:\*\*\s*(.*?)\s*\|\s*\*\*Date:\*\*\s*(.+)$/);
                if (metadataMatch) {
                    category = this.normalizeText(metadataMatch[1]) || category;
                    source = this.normalizeText(metadataMatch[2]) || source;

                    const parsed = this.parseArticleDate(metadataMatch[3], fileDate);
                    articleDate = parsed.date;
                    articleDateString = parsed.dateString;
                    j++;
                    continue;
                }

                if (!url) {
                    const urlMatch = nextLine.match(/\bhttps?:\/\/[^\s)]+/);
                    if (urlMatch) {
                        url = urlMatch[0];
                    }
                }

                if (nextLine === '**Summary:**') {
                    const extracted = this.collectBlockText(lines, j + 1);
                    summary = extracted.text;
                    j = extracted.nextIndex;
                    continue;
                }

                if (!summary && nextLine && !nextLine.startsWith('**') && !nextLine.startsWith('```') && nextLine !== '---') {
                    const extracted = this.collectBlockText(lines, j);
                    summary = extracted.text;
                    j = extracted.nextIndex;
                    continue;
                }

                j++;
            }

            articles.push(this.buildArticle({
                title,
                source,
                url,
                summary,
                category,
                date: articleDate,
                dateString: articleDateString,
                tags: this.generateTags(title, summary)
            }));

            i = j - 1;
        }

        return articles;
    }

    collectBlockText(lines, startIndex) {
        const collected = [];
        let i = startIndex;

        while (i < lines.length) {
            const line = lines[i].trim();

            if (!line) {
                if (collected.length > 0) break;
                i++;
                continue;
            }

            if (
                /^###\s+\d+\.\s+/.test(line) ||
                (/^##\s+/.test(line) && !line.startsWith('## [')) ||
                /^\*\*(X Post|LinkedIn Post|Newsletter Bullet):/.test(line) ||
                line === '---'
            ) {
                break;
            }

            if (line.startsWith('```')) {
                i++;
                while (i < lines.length && !lines[i].trim().startsWith('```')) {
                    i++;
                }
                i++;
                continue;
            }

            collected.push(line);
            i++;
        }

        return {
            text: this.normalizeText(collected.join(' ')),
            nextIndex: i
        };
    }

    buildSummary(rawBody) {
        const lines = String(rawBody || '')
            .split('\n')
            .map(line => this.normalizeText(line))
            .filter(Boolean)
            .filter(line => !/^undefined$/i.test(line))
            .filter(line => !/^by$/i.test(line))
            .filter(line => !/^published\b/i.test(line))
            .filter(line => !/^(opinion|review|news|announcement|lens|guide)$/i.test(line))
            .filter(line => !/^[A-Z0-9\s/&-]{3,}$/.test(line));

        if (lines.length === 0) return '';

        const summary = lines.join(' ');
        return summary.length > 240 ? `${summary.slice(0, 237).trim()}...` : summary;
    }

    buildArticle({ title, source, url, summary, category, date, dateString, tags }) {
        const cleanTitle = this.normalizeText(title);
        const cleanSource = this.normalizeText(source || this.extractSource(url));
        const cleanSummary = this.normalizeText(summary);
        const cleanDate = date instanceof Date && !isNaN(date.getTime()) ? date : new Date();
        const cleanTags = Array.isArray(tags) && tags.length > 0
            ? tags.map(tag => this.normalizeText(tag)).filter(Boolean).slice(0, 5)
            : this.generateTags(cleanTitle, cleanSummary);

        this.sources.add(cleanSource);

        return {
            title: cleanTitle,
            source: cleanSource,
            url: String(url || '').trim(),
            summary: cleanSummary,
            category: this.normalizeText(category || 'News'),
            date: cleanDate,
            dateString: dateString || this.formatLongDate(cleanDate),
            tags: cleanTags
        };
    }

    formatLongDate(date) {
        if (!(date instanceof Date) || isNaN(date.getTime())) return '-';
        return date.toLocaleDateString('en-GB', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    parseArticleDate(value, fallbackDate) {
        const cleanValue = this.normalizeText(value);
        const slashMatch = cleanValue.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
        if (slashMatch) {
            const [, day, month, year] = slashMatch;
            const parsedDate = new Date(Number(year), Number(month) - 1, Number(day));
            if (!isNaN(parsedDate.getTime())) {
                return { date: parsedDate, dateString: this.formatLongDate(parsedDate) };
            }
        }

        const parsedDate = new Date(cleanValue);
        if (!isNaN(parsedDate.getTime())) {
            return { date: parsedDate, dateString: this.formatLongDate(parsedDate) };
        }

        return {
            date: fallbackDate,
            dateString: this.formatLongDate(fallbackDate)
        };
    }

    getCategoryFromSection(sectionName, articleCount) {
        const section = String(sectionName || '').toLowerCase();
        if (section.includes('youtube')) return 'YouTube';
        if (section.includes('top stories') || articleCount <= 5) return 'Top Stories';
        if (section.includes('other')) return 'Briefing';
        return 'News';
    }

    escapeHTML(value) {
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    repairDigestContent(value) {
        return this.repairMojibake(
            String(value || '')
            .replace(/\uFEFF/g, '')
            .replace(/\r\n?/g, '\n')
            .trim()
        );
    }

    repairMojibake(value) {
        let text = String(value || '');
        const suspiciousPattern = /(?:Â|Ã.|â€|â€™|â€œ|â€�|â€”|â€“|â€¦|ðŸ)/;
        if (!suspiciousPattern.test(text)) {
            return text;
        }

        try {
            const decoded = decodeURIComponent(escape(text));
            if (this.getMojibakeScore(decoded) < this.getMojibakeScore(text)) {
                text = decoded;
            }
        } catch (_error) {
            // Fall back to the manual replacements below.
        }

        return text
            .replace(/Â /g, ' ')
            .replace(/Â/g, '')
            .replace(/â€™/g, "'")
            .replace(/â€˜/g, "'")
            .replace(/â€œ/g, '"')
            .replace(/â€�/g, '"')
            .replace(/â€”/g, '—')
            .replace(/â€“/g, '–')
            .replace(/â€¦/g, '...')
            .replace(/â€¢/g, '•')
            .replace(/ðŸŽ¨/g, '🎨')
            .replace(/ðŸŽ›ï¸/g, '🎛️')
            .replace(/ðŸŽ™ï¸/g, '🎙️')
            .replace(/ðŸ”¥/g, '🔥');
    }

    getMojibakeScore(value) {
        return (String(value || '').match(/(?:Â|Ã.|â€|â€™|â€œ|â€�|â€”|â€“|â€¦|ðŸ|�)/g) || []).length;
    }

    normalizeText(value) {
        const text = this.repairMojibake(String(value || ''));
        this.decoder.innerHTML = text;
        return this.decoder.value
            .replace(/\u00a0/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }

    formatCompactDate(date) {
        if (!(date instanceof Date) || isNaN(date.getTime())) return '-';
        return date.toLocaleDateString('en-GB', {
            day: 'numeric',
            month: 'short',
            year: 'numeric'
        });
    }

    isJunkItem(title, url) {
        const junkTitles = ['Browse Business', 'Browse Sustainability', 'Sponsored Content', 'View All Latest', 'Momentum AI', 'Computer Vision', 'Machine Learning'];
        const junkUrlPatterns = [/\/business\/?$/, /\/sustainability\/?$/, /\/sponsored\/?$/, /events\.reutersevents\.com/, /artificial-intelligence-news\/?$/, /\/categories\//, /\/events\//, /\/resources\/on-demand/];
        if (junkTitles.some(t => title.includes(t))) return true;
        if (junkUrlPatterns.some(p => p.test(url))) return true;
        return false;
    }

    generateTags(title, summary) {
        const text = `${title} ${summary || ''}`;
        const tagPatterns = {
            'agents': /\b(agent|agents|agentic)\b/i,
            'models': /\b(gpt|claude|gemini|llama|mistral|model|llm|foundation)\b/i,
            'research': /\b(research|paper|study|breakthrough|discover)\b/i,
            'funding': /\b(raises|funding|invest|valuation|series [a-c]|million|billion|\$\d+[mb])\b/i,
            'product': /\b(launch|release|announce|feature|update|new|beta)\b/i,
            'open-source': /\b(open source|open-source|opensource|github|hugging face)\b/i,
            'safety': /\b(safety|alignment|ethics|regulation|govern|policy)\b/i,
            'robotics': /\b(robot|robotics|hardware|humanoid|physical)\b/i,
            'image': /\b(image|images|imaging|midjourney|dall-e|dallÂ·e|stable diffusion|flux|ideogram|leonardo|firefly|photoshop|illustration|portrait|artwork|art\b|artis)/i,
            'video': /\b(video|videos|runway|kling|pika|sora|luma|veo|animate|animation|film|cinema|minimax|hailuo|gen-3)\b/i,
            'audio': /\b(voice|speech|audio|sound|music|suno|elevenlabs|udio|singing|song|tts|text.to.speech)\b/i,
            'coding': /\b(code|coding|developer|programming|copilot|codex)\b/i,
            'creative': /\b(creative|creativ|generat.*art|generat.*image|generat.*video|generat.*music|ai.art|ai.music|ai.video|ai.film|visual|render|3d|comfyui|diffusion|gan\b|style.transfer)/i,
            '3d': /\b(3d|blender|unreal|unity|mesh|texture|rendering|cgi|vfx)\b/i,
            'design': /\b(design|figma|canva|adobe|photoshop|graphic|typography|ui.ux)\b/i
        };
        const tags = [];
        for (const [tag, pattern] of Object.entries(tagPatterns)) {
            if (pattern.test(text)) tags.push(tag);
        }
        if (tags.length === 0) tags.push('news');
        return tags.slice(0, 5);
    }

    extractSource(url) {
        if (!url) return 'Unknown';
        try {
            const hostname = new URL(url).hostname.toLowerCase();
            const sourceMap = {
                'techcrunch.com': 'TechCrunch',
                'reuters.com': 'Reuters',
                'theverge.com': 'The Verge',
                'wired.com': 'Wired',
                'arstechnica.com': 'Ars Technica',
                'bbc.com': 'BBC', 'bbc.co.uk': 'BBC',
                'nytimes.com': 'New York Times',
                'theguardian.com': 'The Guardian',
                'bloomberg.com': 'Bloomberg',
                'technologyreview.com': 'MIT Tech Review',
                'venturebeat.com': 'VentureBeat',
                'anthropic.com': 'Anthropic',
                'openai.com': 'OpenAI',
                'deepmind.com': 'DeepMind',
                'artificialintelligence-news.com': 'AI News'
            };
            for (const [domain, name] of Object.entries(sourceMap)) {
                if (hostname.includes(domain)) return name;
            }
            return hostname.replace('www.', '').split('.')[0];
        } catch { return 'Unknown'; }
    }

    populateFilters() {
        const sourceContainer = document.getElementById('sourceCheckboxes');
        if (!sourceContainer) return;

        const sortedSources = Array.from(this.sources).sort();
        sourceContainer.textContent = '';
        sortedSources.forEach(source => {
            const label = document.createElement('label');
            const input = document.createElement('input');
            input.type = 'checkbox';
            input.value = source;
            input.checked = true;
            const text = document.createTextNode(` ${source}`);
            label.appendChild(input);
            label.appendChild(text);
            sourceContainer.appendChild(label);
        });
    }

    setupEventListeners() {
        const searchInput = document.getElementById('searchInput');
        const fromDate = document.getElementById('fromDate');
        const toDate = document.getElementById('toDate');
        const sourceContainer = document.getElementById('sourceCheckboxes');
        const quick24h = document.getElementById('quick24h');
        const quickLastWeek = document.getElementById('quickLastWeek');
        const quickAll = document.getElementById('quickAll');
        const groupBy = document.getElementById('groupBy');

        if (searchInput) searchInput.addEventListener('input', () => this.filterArticles());
        if (fromDate) fromDate.addEventListener('change', () => { this.updateQuickFilterButtons(); this.filterArticles(); });
        if (toDate) toDate.addEventListener('change', () => { this.updateQuickFilterButtons(); this.filterArticles(); });
        if (sourceContainer) sourceContainer.addEventListener('change', () => this.filterArticles());
        if (groupBy) groupBy.addEventListener('change', () => this.displayArticles());

        if (quick24h) quick24h.addEventListener('click', () => {
            const today = new Date();
            const yesterday = new Date();
            yesterday.setDate(today.getDate() - 1);
            if (fromDate) fromDate.value = yesterday.toISOString().split('T')[0];
            if (toDate) toDate.value = today.toISOString().split('T')[0];
            this.updateQuickFilterButtons('24h');
            this.filterArticles();
        });

        if (quickLastWeek) quickLastWeek.addEventListener('click', () => {
            const today = new Date();
            const lastWeek = new Date();
            lastWeek.setDate(today.getDate() - 7);
            if (fromDate) fromDate.value = lastWeek.toISOString().split('T')[0];
            if (toDate) toDate.value = today.toISOString().split('T')[0];
            this.updateQuickFilterButtons('week');
            this.filterArticles();
        });

        if (quickAll) quickAll.addEventListener('click', () => {
            if (fromDate) fromDate.value = '';
            if (toDate) toDate.value = '';
            this.updateQuickFilterButtons('all');
            this.filterArticles();
        });

        const clearBtn = document.getElementById('clearFilters');
        if (clearBtn) clearBtn.addEventListener('click', () => {
            if (searchInput) searchInput.value = '';
            if (fromDate) fromDate.value = '';
            if (toDate) toDate.value = '';
            document.querySelectorAll('#sourceCheckboxes input').forEach(cb => cb.checked = true);
            this.updateQuickFilterButtons('all');
            this.filterArticles();
        });
    }

    updateQuickFilterButtons(active = null) {
        const map = { quick24h: '24h', quickLastWeek: 'week', quickAll: 'all' };
        Object.entries(map).forEach(([id, value]) => {
            const btn = document.getElementById(id);
            if (btn) btn.classList.toggle('active', active === value);
        });
    }

    filterArticles() {
        const searchInput = document.getElementById('searchInput');
        const fromDateEl = document.getElementById('fromDate');
        const toDateEl = document.getElementById('toDate');

        const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
        const fromDate = fromDateEl ? fromDateEl.value : '';
        const toDate = toDateEl ? toDateEl.value : '';
        const selectedSources = Array.from(document.querySelectorAll('#sourceCheckboxes input:checked')).map(i => i.value);
        this.noSourcesSelected = document.querySelectorAll('#sourceCheckboxes input').length > 0 && selectedSources.length === 0;

        this.filteredArticles = this.articles.filter(article => {
            const articleDate = new Date(article.date);

            const matchesSearch = !searchTerm ||
                article.title.toLowerCase().includes(searchTerm) ||
                article.summary.toLowerCase().includes(searchTerm) ||
                article.source.toLowerCase().includes(searchTerm);

            let matchesRange = true;
            if (fromDate) matchesRange = matchesRange && articleDate >= new Date(fromDate);
            if (toDate) matchesRange = matchesRange && articleDate <= new Date(toDate + 'T23:59:59');

            const matchesSource = selectedSources.length > 0 && selectedSources.includes(article.source);

            return matchesSearch && matchesRange && matchesSource;
        });

        this.updateFilterSummary();
        this.displayArticles();
    }

    updateFilterSummary() {
        const summary = document.getElementById('filterSummary');
        const text = document.getElementById('filterSummaryText');
        if (summary && text) {
            const total = this.articles.length;
            if (total === 0) {
                text.textContent = 'No articles loaded yet.';
            } else {
                const sourceCount = Array.from(document.querySelectorAll('#sourceCheckboxes input:not(:checked)')).length;
                const activeFilters = [
                    document.getElementById('searchInput')?.value?.trim(),
                    document.getElementById('fromDate')?.value,
                    document.getElementById('toDate')?.value,
                    sourceCount > 0 ? 'sources' : ''
                ].filter(Boolean).length;
                text.textContent = activeFilters > 0
                    ? `Showing ${this.filteredArticles.length} of ${total} articles`
                    : `Showing all ${total} articles`;
            }
            summary.style.display = total > 0 ? 'block' : 'none';
        }
    }

    updateOverview() {
        const articleCount = document.getElementById('news-article-count');
        const sourceCount = document.getElementById('news-source-count');
        const latestDate = document.getElementById('news-latest-date');

        if (articleCount) articleCount.textContent = String(this.articles.length);
        if (sourceCount) sourceCount.textContent = String(this.sources.size);
        if (latestDate) {
            latestDate.textContent = this.articles.length > 0
                ? this.formatCompactDate(this.articles[0].date)
                : '-';
        }
    }

    setNoResultsMessage(message) {
        const noResults = document.getElementById('noResults');
        if (!noResults) return;
        const paragraph = noResults.querySelector('p');
        if (paragraph) paragraph.textContent = message;
    }

    displayArticles() {
        const groupByEl = document.getElementById('groupBy');
        const groupBy = groupByEl ? groupByEl.value : 'date';
        const container = document.getElementById('articlesContainer');
        const noResults = document.getElementById('noResults');

        if (!container) return;
        container.innerHTML = '';

        if (this.articles.length === 0) {
            if (noResults) {
                this.setNoResultsMessage('No digest files were found in the local news feed yet. Once the digests are generated, the feed will appear here automatically.');
                noResults.style.display = 'block';
            }
            return;
        }

        if (this.filteredArticles.length === 0) {
            if (noResults) {
                this.setNoResultsMessage(
                    this.noSourcesSelected
                        ? 'Select at least one source to see results again.'
                        : 'No articles matched the current filters. Try widening the date range or clearing one of the source filters.'
                );
                noResults.style.display = 'block';
            }
            return;
        }
        if (noResults) noResults.style.display = 'none';

        const getRelativeDate = (dateString) => {
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            const yesterday = new Date(today);
            yesterday.setDate(yesterday.getDate() - 1);

            const parts = dateString.match(/(\d+)\s+(\w+)\s+(\d+)/);
            if (parts) {
                const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
                const articleDate = new Date(parseInt(parts[3]), months.indexOf(parts[2]), parseInt(parts[1]));
                if (articleDate.getTime() === today.getTime()) return 'Today';
                if (articleDate.getTime() === yesterday.getTime()) return 'Yesterday';
            }
            return dateString;
        };

        if (groupBy === 'source') {
            const groups = {};
            this.filteredArticles.forEach(a => {
                groups[a.source] = groups[a.source] || [];
                groups[a.source].push(a);
            });
            Object.keys(groups).sort().forEach(src => {
                const h = document.createElement('h3');
                h.className = 'an-group-title';
                h.textContent = src;
                container.appendChild(h);
                const g = document.createElement('div');
                g.className = 'an-grid';
                groups[src].forEach(a => g.appendChild(this.createCard(a)));
                container.appendChild(g);
            });
        } else {
            const groups = {};
            this.filteredArticles.forEach(a => {
                groups[a.dateString] = groups[a.dateString] || [];
                groups[a.dateString].push(a);
            });

            const sortedDates = Object.keys(groups).sort((a, b) => {
                const parse = (str) => {
                    const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
                    const parts = str.match(/(\d+)\s+(\w+)\s+(\d+)/);
                    if (parts) return new Date(parseInt(parts[3]), months.indexOf(parts[2]), parseInt(parts[1]));
                    return new Date(0);
                };
                return parse(b) - parse(a);
            });

            sortedDates.forEach(date => {
                const h = document.createElement('h3');
                h.className = 'an-group-title';
                h.textContent = getRelativeDate(date);
                container.appendChild(h);
                const g = document.createElement('div');
                g.className = 'an-grid';
                groups[date].forEach(a => g.appendChild(this.createCard(a)));
                container.appendChild(g);
            });
        }
    }

    createCard(article) {
        const card = document.createElement('article');
        card.className = 'an-card';

        const isFav = this.favorites.has(article.title);
        if (isFav) card.classList.add('highlight');

        const header = document.createElement('div');
        header.className = 'an-card-header';

        const source = document.createElement('span');
        source.className = 'an-card-source';
        source.textContent = article.source;

        const date = document.createElement('span');
        date.className = 'an-card-date';
        date.textContent = article.dateString;

        header.append(source, date);

        const title = document.createElement('h3');
        title.className = 'an-card-title';

        if (article.url) {
            const link = document.createElement('a');
            link.href = article.url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.textContent = article.title;
            title.appendChild(link);
        } else {
            title.textContent = article.title;
        }

        const summary = document.createElement('p');
        summary.className = 'an-card-summary';
        if (article.summary) {
            summary.textContent = article.summary.length > 180
                ? `${article.summary.slice(0, 180)}...`
                : article.summary;
        }

        const footer = document.createElement('div');
        footer.className = 'an-card-footer';

        const category = document.createElement('span');
        category.className = 'an-card-category';
        category.textContent = article.category;

        const actions = document.createElement('div');
        actions.className = 'an-card-actions';

        const favBtn = document.createElement('button');
        favBtn.className = `an-fav-btn${isFav ? ' active' : ''}`;
        favBtn.type = 'button';
        favBtn.title = 'Highlight';
        favBtn.setAttribute('aria-pressed', isFav ? 'true' : 'false');
        favBtn.innerHTML = `<svg viewBox="0 0 24 24" fill="${isFav ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2"><path d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.563 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z"/></svg>`;

        actions.appendChild(favBtn);
        if (article.url) {
            const readMore = document.createElement('a');
            readMore.href = article.url;
            readMore.target = '_blank';
            readMore.rel = 'noopener noreferrer';
            readMore.className = 'an-read-more';
            readMore.textContent = 'Read';
            actions.appendChild(readMore);
        }
        footer.append(category, actions);

        card.append(header, title);
        if (article.summary) card.appendChild(summary);
        card.appendChild(footer);

        if (article.tags.length > 0) {
            const tags = document.createElement('div');
            tags.className = 'an-tags';
            article.tags.forEach(tag => {
                const span = document.createElement('span');
                span.className = 'an-tag';
                span.textContent = tag;
                tags.appendChild(span);
            });
            card.appendChild(tags);
        }

        favBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this.favorites.has(article.title)) {
                    this.favorites.delete(article.title);
                } else {
                    this.favorites.add(article.title);
                }
                this.saveStoredFavorites();
                this.displayArticles();
            });

        return card;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new NewsApp();
});
