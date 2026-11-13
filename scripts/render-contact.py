"""Render the shared contact setting in every static footer."""
import re, sys
from site_config import ROOT, contact_link
stale=[]
for p in [*ROOT.glob("*.html"), *(ROOT / "a-list").glob("*.html")]:
    original=p.read_text(encoding="utf-8")
    text=re.sub(r'<a href="mailto:[^"<>]*">[^<>]*</a>', '', original)
    text=re.sub(r'(<(?:span|p)>Contact</(?:span|p)>)', lambda m:m[0]+contact_link(), text)
    if text != original:
        stale.append(p.name)
        if "--check" not in sys.argv: p.write_text(text,encoding="utf-8")
if "--check" in sys.argv and stale: raise SystemExit("Contact output stale: "+", ".join(stale))
print("Contact configuration rendered and checked.")
