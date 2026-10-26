(function () {
  "use strict";

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

  function setPressed(buttons, activeButton) {
    buttons.forEach((button) => {
      const isActive = button === activeButton;
      button.classList.toggle("is-on", isActive);
      button.setAttribute("aria-pressed", String(isActive));
    });
  }

  // Keep the gradient visible if an archive image becomes unavailable.
  document.addEventListener("error", (event) => {
    if (event.target.matches?.(".cn-frame__img")) event.target.hidden = true;
  }, true);

  function setupHero() {
    const bg = $("[data-hero-bg]");
    const strip = $("[data-hero-strip]");
    if (!bg || !strip) return;

    let items = [];
    try {
      items = JSON.parse(strip.getAttribute("data-hero-items") || "[]");
    } catch (_error) {
      items = [];
    }

    const ref = $("[data-hero-ref]");
    const date = $("[data-hero-date]");
    const prompt = $("[data-hero-prompt]");
    const buttons = $$("[data-hero-index]", strip);

    buttons.forEach((button) => {
      button.addEventListener("click", () => {
        const item = items[Number(button.dataset.heroIndex)];
        if (!item) return;
        bg.setAttribute("style", item.style || "");
        if (ref) ref.textContent = item.ref || "";
        if (date) date.textContent = item.date || "";
        if (prompt) prompt.textContent = `"${item.prompt || ""}"`;
        buttons.forEach((cell) => cell.classList.toggle("is-on", cell === button));
      });
    });
  }

  function setupGalleryKeyboardFocus() {
    document.addEventListener("keydown", (event) => {
      if (event.key !== "/" || event.ctrlKey || event.metaKey || event.altKey) return;
      const target = event.target;
      if (target && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)) return;
      const search = $("[data-gallery-search]") || $("[data-news-search]");
      if (search) {
        event.preventDefault();
        search.focus();
      }
    });
  }

  function setupGallery() {
    const grid = $("[data-gallery-grid]");
    if (!grid) return;

    const cards = $$("[data-search]", grid);
    const search = $("[data-gallery-search]");
    const typeButtons = $$("[data-gallery-type]");
    const sortButtons = $$("[data-gallery-sort]");
    const modelSelect = $("[data-gallery-model]");
    const captionToggle = $("[data-caption-toggle]");
    const moreButton = $("[data-gallery-more]");
    const resetButtons = $$("[data-gallery-reset]");
    const empty = $("[data-gallery-empty]");
    const count = $("[data-gallery-count]");

    const state = {
      search: "",
      type: "All",
      sort: "newest",
      model: "All",
      captions: false,
      visibleLimit: 24,
      randomSeed: 0,
    };

    function sortedCards(list) {
      const copy = [...list];
      if (state.sort === "oldest") {
        copy.sort((a, b) => (a.dataset.date || "").localeCompare(b.dataset.date || ""));
      } else if (state.sort === "random") {
        copy.sort((a, b) => {
          const aKey = `${a.dataset.index || "0"}-${state.randomSeed}`;
          const bKey = `${b.dataset.index || "0"}-${state.randomSeed}`;
          return aKey.localeCompare(bKey);
        });
      } else {
        copy.sort((a, b) => (b.dataset.date || "").localeCompare(a.dataset.date || ""));
      }
      return copy;
    }

    function matches(card) {
      const haystack = card.dataset.search || "";
      const matchesSearch = !state.search || haystack.includes(state.search);
      const matchesType = state.type === "All" || card.dataset.type === state.type;
      const matchesModel = state.model === "All" || card.dataset.model === state.model;
      return matchesSearch && matchesType && matchesModel;
    }

    function render() {
      const matching = sortedCards(cards.filter(matches));
      matching.forEach((card) => grid.appendChild(card));

      cards.forEach((card) => {
        card.classList.add("is-collapsed");
        card.removeAttribute("aria-setsize");
        card.removeAttribute("aria-posinset");
      });

      matching.slice(0, state.visibleLimit).forEach((card, index) => {
        card.classList.remove("is-collapsed");
        card.setAttribute("aria-setsize", String(matching.length));
        card.setAttribute("aria-posinset", String(index + 1));
      });

      $$("[data-search] .cn-frame__cap--optional", grid).forEach((caption) => {
        caption.hidden = !state.captions;
      });

      if (captionToggle) {
        captionToggle.classList.toggle("is-on", state.captions);
        captionToggle.setAttribute("aria-pressed", String(state.captions));
        captionToggle.textContent = state.captions ? "Hide prompt captions" : "Show prompt captions";
      }

      if (moreButton) {
        moreButton.hidden = matching.length <= state.visibleLimit;
      }

      if (empty) {
        empty.classList.toggle("cn-hidden", matching.length > 0);
      }

      if (count) {
        const visible = Math.min(matching.length, state.visibleLimit);
        const start = matching.length ? "0001" : "0000";
        count.textContent = `${start} - ${String(visible).padStart(4, "0")} of ${String(matching.length).padStart(4, "0")}`;
      }
    }

    function reset() {
      state.search = "";
      state.type = "All";
      state.sort = "newest";
      state.model = "All";
      state.visibleLimit = 24;
      state.randomSeed = 0;
      if (search) search.value = "";
      if (modelSelect) modelSelect.value = "All";
      setPressed(typeButtons, typeButtons.find((button) => button.dataset.galleryType === "All"));
      setPressed(sortButtons, sortButtons.find((button) => button.dataset.gallerySort === "newest"));
      render();
    }

    search?.addEventListener("input", () => {
      state.search = search.value.trim().toLowerCase();
      state.visibleLimit = 24;
      render();
    });

    typeButtons.forEach((button) => {
      button.addEventListener("click", () => {
        state.type = button.dataset.galleryType || "All";
        state.visibleLimit = 24;
        setPressed(typeButtons, button);
        render();
      });
    });

    sortButtons.forEach((button) => {
      button.addEventListener("click", () => {
        state.sort = button.dataset.gallerySort || "newest";
        state.visibleLimit = 24;
        if (state.sort === "random") state.randomSeed += 1;
        setPressed(sortButtons, button);
        render();
      });
    });

    modelSelect?.addEventListener("change", () => {
      state.model = modelSelect.value;
      state.visibleLimit = 24;
      render();
    });

    captionToggle?.addEventListener("click", () => {
      state.captions = !state.captions;
      render();
    });

    moreButton?.addEventListener("click", () => {
      state.visibleLimit += 24;
      render();
    });

    resetButtons.forEach((button) => button.addEventListener("click", reset));
    render();
  }

  const TOPIC_BY_TAG = {
    image_gen: "Image",
    video_gen: "Video",
    music_gen: "Audio",
    voice_synthesis: "Audio",
    "3d_gen": "3D",
    creative_tool: "Tools",
    creative_workflow: "Tools",
    art_ai: "Image",
  };

  function escapeNewsText(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function topicForRoutedArticle(article) {
    const tags = [...(article.matching_tags || []), ...(article.tags || [])];
    for (const tag of tags) {
      if (TOPIC_BY_TAG[tag]) return TOPIC_BY_TAG[tag];
    }
    return "Tools";
  }

  async function insertRoutedFeed(list) {
    let payload;
    try {
      const response = await fetch("news-digests/news-feed-latest.json", { cache: "no-store" });
      if (!response.ok) return;
      payload = await response.json();
    } catch {
      return;
    }
    if (payload?.site !== "Axy Lusion" || !Array.isArray(payload.articles) || payload.articles.length === 0) return;

    const head = list.querySelector(".cn-digests__head");
    if (!head) return;
    const byDate = new Map();
    for (const article of payload.articles) {
      if (!article?.title || !/^https?:\/\//i.test(article.url || "")) continue;
      const day = String(article.date || "").slice(0, 10);
      if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) continue;
      if (!byDate.has(day)) byDate.set(day, []);
      byDate.get(day).push(article);
    }

    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    let cursor = head;
    for (const day of [...byDate.keys()].sort().reverse()) {
      const articles = byDate.get(day);
      const date = new Date(`${day}T00:00:00Z`);
      const items = articles.map((article) => {
        const topic = topicForRoutedArticle(article);
        return `<li data-topic="${escapeNewsText(topic)}"><a href="${escapeNewsText(article.url)}" target="_blank" rel="noopener noreferrer">${escapeNewsText(article.title)}</a><span class="cn-digest__topic">${escapeNewsText(topic)}</span></li>`;
      }).join("");
      const row = document.createElement("article");
      row.className = "cn-digest";
      row.dataset.digestDate = day;
      row.dataset.digestSearch = articles.map((article) => article.title).join(" ").toLowerCase();
      row.innerHTML = `<div class="cn-digest__date"><span class="cn-digest__day">${date.getUTCDate()}</span><span class="cn-digest__mon">${months[date.getUTCMonth()]}</span><span class="cn-digest__yr">${date.getUTCFullYear()}</span></div><ul class="cn-digest__heads">${items}</ul>`;
      cursor.insertAdjacentElement("afterend", row);
      cursor = row;
    }
  }

  async function setupNews() {
    const list = $("[data-news-list]");
    if (!list) return;
    await insertRoutedFeed(list);

    const rows = $$("[data-digest-date]", list);
    const search = $("[data-news-search]");
    const rangeButtons = $$("[data-news-range]");
    const topicButtons = $$("[data-news-topic]");
    const clearButtons = $$("[data-news-clear], [data-news-empty-reset]");
    const empty = $("[data-news-empty]");
    const latestDate = rows.length ? new Date(`${rows[0].dataset.digestDate}T00:00:00`) : null;

    const state = {
      search: "",
      range: "all",
      topic: "All",
    };

    function inRange(row) {
      if (state.range === "all" || !latestDate) return true;
      const rowDate = new Date(`${row.dataset.digestDate}T00:00:00`);
      const diffDays = Math.round((latestDate.getTime() - rowDate.getTime()) / 86400000);
      if (state.range === "day") return diffDays === 0;
      return diffDays >= 0 && diffDays <= 7;
    }

    function render() {
      let visibleRows = 0;
      rows.forEach((row) => {
        const rowMatchesSearch = !state.search || (row.dataset.digestSearch || "").includes(state.search);
        let visibleItems = 0;
        $$("li[data-topic]", row).forEach((item) => {
          const topicMatches = state.topic === "All" || item.dataset.topic === state.topic;
          const show = topicMatches && rowMatchesSearch;
          item.classList.toggle("is-hidden", !show);
          if (show) visibleItems += 1;
        });
        const showRow = inRange(row) && rowMatchesSearch && visibleItems > 0;
        row.classList.toggle("is-hidden", !showRow);
        if (showRow) visibleRows += 1;
      });

      if (empty) empty.classList.toggle("cn-hidden", visibleRows > 0);
      const hasFilters = state.search || state.range !== "all" || state.topic !== "All";
      clearButtons.forEach((button) => button.classList.toggle("cn-hidden", !hasFilters));
    }

    function reset() {
      state.search = "";
      state.range = "all";
      state.topic = "All";
      if (search) search.value = "";
      setPressed(rangeButtons, rangeButtons.find((button) => button.dataset.newsRange === "all"));
      setPressed(topicButtons, topicButtons.find((button) => button.dataset.newsTopic === "All"));
      render();
    }

    search?.addEventListener("input", () => {
      state.search = search.value.trim().toLowerCase();
      render();
    });

    rangeButtons.forEach((button) => {
      button.addEventListener("click", () => {
        state.range = button.dataset.newsRange || "all";
        setPressed(rangeButtons, button);
        render();
      });
    });

    topicButtons.forEach((button) => {
      button.addEventListener("click", () => {
        state.topic = button.dataset.newsTopic || "All";
        setPressed(topicButtons, button);
        render();
      });
    });

    clearButtons.forEach((button) => button.addEventListener("click", reset));
    render();
  }

  document.addEventListener("DOMContentLoaded", () => {
    $$(".cn-frame__img").forEach((img) => {
      if (img.complete && !img.naturalWidth) img.hidden = true;
    });
    setupHero();
    setupGalleryKeyboardFocus();
    setupGallery();
    setupNews();
  });
})();
