"""Data-free A-List withdrawal, pending permission: hub #615 and #1508."""
from pathlib import Path
import re

from meta_csp import apply as apply_csp
from navigation import ensure_navigation

ROOT = Path(__file__).resolve().parent.parent
MESSAGE = "The A-List is being rebuilt from sources we have permission to publish."
ROUTES = (
    "a-list.html", "a-list/3d-generation.html", "a-list/image-editing.html",
    "a-list/image-generation.html", "a-list/music-generation.html",
    "a-list/upscaling.html", "a-list/video-generation.html", "a-list/voice-tts.html",
)
DATA_FILES = ("data/a-list-benchmarks.json", "data/aa-leaderboard-capture.json")


def holding_page(relative: str) -> str:
    prefix = "../" if relative.startswith("a-list/") else ""
    return ensure_navigation(apply_csp(f'''<!DOCTYPE html>
<html lang="en-GB">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, follow">
  <title>The A-List is being rebuilt | Axy Lusion</title>
  <meta name="description" content="{MESSAGE}">
  <link rel="canonical" href="https://axylusion.com/a-list.html">
  <link rel="icon" href="{prefix}favicon.svg" type="image/svg+xml">
  <link rel="manifest" href="{prefix}site.webmanifest">
  <link rel="stylesheet" href="{prefix}styles.css">
</head>
<body>
  <header style="position: static; transform: none; opacity: 1;"><a href="{prefix}index.html" style="color: var(--axyl-cream, #f5e6c8); text-decoration: underline;">Axy Lusion</a></header>
  <main id="main-content" tabindex="-1">
    <h1>The A-List</h1>
    <p>{MESSAGE}</p>
    <p><a href="{prefix}tools.html" style="color: var(--axyl-cream, #f5e6c8); text-decoration: underline;">Explore the creative tools directory</a></p>
  </main>
  <footer>
    <nav aria-label="Footer main pages">
      <a href="{prefix}gallery.html">Gallery</a>
      <a href="{prefix}tools.html">Tools</a>
    </nav>
  </footer>
  <script src="{prefix}cross-site-nav.js" defer></script>
</body>
</html>
'''))


def holding_outputs() -> dict[Path, str]:
    # Include unmanaged old category routes so a render cannot leave a stale board.
    routes = set(ROUTES) | {p.relative_to(ROOT).as_posix() for p in (ROOT / "a-list").glob("*.html")}
    return {ROOT / route: holding_page(route) for route in sorted(routes)}


def render_holding_pages(check: bool = False) -> int:
    stale = []
    for path, html in holding_outputs().items():
        if not path.exists() or path.read_text(encoding="utf-8") != html:
            stale.append(path.relative_to(ROOT).as_posix())
            if not check:
                path.parent.mkdir(exist_ok=True)
                path.write_text(html, encoding="utf-8", newline="\n")
    if check and stale:
        print("FAIL: A-List holding pages are stale: " + ", ".join(stale))
        return 1
    print(f"A-List holding pages {'checked' if check else 'rendered'}: {len(holding_outputs())}; acquisition disabled (hub #615, #1508).")
    return 0


def publication_issues() -> list[str]:
    issues = []
    for name in DATA_FILES:
        if (ROOT / name).exists():
            issues.append(f"Withdrawn A-List data must stay absent: {name}")
    for path, html in holding_outputs().items():
        if not path.exists() or path.read_text(encoding="utf-8") != html:
            issues.append(f"Expected a data-free noindex holding page: {path.relative_to(ROOT)}")
    for name in ("sitemap.xml", "feed.xml", "llms.txt"):
        text = (ROOT / name).read_text(encoding="utf-8")
        if re.search(r"(?:https://axylusion.com)?/a-list(?:\.html|/)", text):
            issues.append(f"Withdrawn A-List route appears in {name}")
    return issues
