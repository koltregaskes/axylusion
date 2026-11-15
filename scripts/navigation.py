"""Shared skip navigation and privacy link for static pages and renderers."""
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
    def privacy_link(match):
        group = match[0]
        if re.search(r'href=["\'][^"\']*privacy\.html["\']', group):
            return group
        # Follow the group's existing relative, nested or root-relative links.
        gallery = re.search(r'href=["\']([^"\']*)gallery\.html["\']', group)
        if not gallery:
            raise ValueError("Footer main navigation is missing its gallery link")
        link = f'<a href="{escape(gallery[1])}privacy.html">Privacy</a>'
        return re.sub(r'(\s*</nav>)$', lambda end: '\n        ' + link + end[0], group)
    text = re.sub(r'<nav\b[^>]*aria-label=["\'](?:Footer main pages|Main pages)["\'][^>]*>.*?</nav>',
                  privacy_link, text, flags=re.I | re.S)
    return text
