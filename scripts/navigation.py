"""Shared skip navigation and privacy link for static pages and renderers."""
import re
from html import escape
from html.parser import HTMLParser
from urllib.parse import quote


class Attributes(HTMLParser):
    def handle_starttag(self, tag, attrs):
        self.values = dict(attrs)


def attributes(tag):
    parser = Attributes()
    parser.feed(tag)
    return parser.values


def set_attribute(tag, name, value):
    # Require an actual attribute, not data-id/data-href or a class-name prefix.
    pattern = r'''(\s+)([^\s=/>]+)(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+))?'''
    rendered = f'{name}="{escape(value, quote=True)}"'
    if name in attributes(tag):
        return re.sub(pattern, lambda match: match[1] + rendered
                      if match[2].lower() == name else match[0], tag)
    return tag[:-1] + ' ' + rendered + '>'

def ensure_navigation(text):
    main=re.search(r'<main\b([^>]*)>', text, re.I)
    if not main: raise ValueError("Page is missing its main landmark")
    target=attributes(main[0]).get('id') or "main-content"
    text=text[:main.start()]+set_attribute(main[0], 'id', target)+text[main.end():]
    href = '#' + quote(target, safe='')
    found = False
    def skip_link(match):
        nonlocal found
        if 'skip-link' not in attributes(match[0]).get('class', '').split():
            return match[0]
        found = True
        return set_attribute(match[0], 'href', href)
    text = re.sub(r'<a\b[^>]*>', skip_link, text, flags=re.I)
    if not found:
        if not re.search(r'<body\b[^>]*>', text, re.I):
            raise ValueError("Page is missing its body for skip navigation")
        text=re.sub(r'(<body\b[^>]*>)',lambda m:m[0]+f'\n    <a class="skip-link" href="{escape(href)}">Skip to content</a>',text,count=1,flags=re.I)
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
