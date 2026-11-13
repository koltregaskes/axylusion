"""Regenerate skip links and main landmarks without changing page content."""
import sys
from pathlib import Path
from navigation import ensure_navigation
root=Path(__file__).resolve().parent.parent
stale=[]
for p in [*root.glob("*.html"),*(root/"a-list").glob("*.html")]:
    text=p.read_text(encoding="utf-8"); rendered=ensure_navigation(text)
    if text!=rendered:
        stale.append(p.name)
        if "--check" not in sys.argv: p.write_text(rendered,encoding="utf-8")
if "--check" in sys.argv and stale: raise SystemExit("Navigation output stale: "+", ".join(stale))
print("Skip links and main landmarks checked on every HTML route.")
