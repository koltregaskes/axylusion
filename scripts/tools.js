(() => {
  const header = document.getElementById("header");
  const filterLinks = Array.from(document.querySelectorAll(".tool-filter-link"));
  const filterableSections = Array.from(document.querySelectorAll(".tools-category[data-filter]"));
  const supportIntro = document.querySelector(".tools-support-intro");

  function applyFilter(filter, options = {}) {
    const { scroll = true } = options;

    filterLinks.forEach((link) => {
      link.classList.toggle("active", link.dataset.filter === filter);
    });

    filterableSections.forEach((section) => {
      const matches = filter === "all" || section.dataset.filter === filter;
      section.classList.toggle("is-hidden", !matches);
    });

    if (supportIntro) {
      supportIntro.hidden = filter !== "all";
    }

    if (!scroll) return;

    const target = filter === "all"
      ? document.querySelector(".tools-directory")
      : document.querySelector(`.tools-category[data-filter="${filter}"]`);

    if (!target) return;

    const headerHeight = Math.max(header?.offsetHeight || 0, 72);
    const targetTop = target.getBoundingClientRect().top + window.scrollY - headerHeight - 18;
    window.scrollTo({ top: targetTop, behavior: "smooth" });
  }

  filterLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      const filter = link.dataset.filter || "all";
      applyFilter(filter);
      const nextHash = filter === "all" ? "" : `#${filter}`;
      window.history.replaceState({}, "", `${window.location.pathname}${nextHash}`);
    });
  });

  const initialFilter = window.location.hash.replace("#", "");
  const validInitialFilter = filterLinks.some((link) => link.dataset.filter === initialFilter)
    ? initialFilter
    : "all";
  applyFilter(validInitialFilter, { scroll: false });
})();
