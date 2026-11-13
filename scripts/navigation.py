"""Shared skip navigation for static pages and page renderers."""
import re
from html import escape

def ensure_navigation(text):
    main=re.search(r'<main\b([^>]*)>', text, re.I)
    if not main: raise ValueError("Page is missing its main landmark")
    identity=re.search(r'\bid=["\']([^"\']+)',main[1])
    target=identity[1] if identity else "main-content"
    if not identity:
        text=text[:main.start()]+f'<main id="{target}"{main[1]}>'+text[main.end():]
    if not re.search(r'class=["\'][^"\']*\bskip-link\b',text):
        text=re.sub(r'(<body\b[^>]*>)',lambda m:m[0]+f'\n    <a class="skip-link" href="#{escape(target)}">Skip to content</a>',text,count=1,flags=re.I)
    return text
