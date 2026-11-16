"""Shared provenance wording for Kol's Midjourney image collections."""
from datetime import date

CREATOR = "Kol Tregaskes"
PRODUCTION = "AI-generated with Midjourney, directed and selected by Kol Tregaskes"
COPYRIGHT_NOTICE = "All rights reserved unless stated"
RIGHTS_PATH = "about.html#image-rights"
RIGHTS_NOTE = f"See {RIGHTS_PATH} for permitted use and rights."
# Shown, and searchable, in place of a prompt the archive never truly recorded.
PROMPT_NOT_LOGGED = "Prompt not logged"
TERMS_URL = "https://docs.midjourney.com/hc/en-us/articles/32083055291277-Terms-of-Service"
RIGHTS_STATEMENT = (
    "All rights reserved unless stated. Rights in AI-generated images are uncertain. "
    "This notice does not assert that every image has copyright protection or grant a reuse licence. "
    "Ask Kol Tregaskes before reusing an image; any permission is subject to applicable rights "
    "and Midjourney's terms. References to artists, characters or brands in prompts do not "
    "imply endorsement or permission from those parties."
)


def provenance_fields(item, source=None):
    source = source or item
    tool = str(source.get("model") or source.get("source") or source.get("tool") or "").strip()
    if not tool:
        raise ValueError(f"Missing tool/model evidence for {item.get('id', '<unknown>')}")
    return {"creator": CREATOR, "tool": tool, "production": PRODUCTION,
            "copyright_notice": COPYRIGHT_NOTICE, "rights_note": RIGHTS_NOTE}


def credit_text(item):
    creator = item.get("creator") or CREATOR
    tool = item.get("tool") or item.get("model") or item.get("source") or "Tool not recorded"
    raw = str(item.get("created") or "")
    try:
        created = date.fromisoformat(raw[:10])
        recorded_date = f"{created.day} {created.strftime('%b')} {created.year}"
    except ValueError:
        recorded_date = "Date not recorded"
    return f"{creator} / {tool} / {recorded_date} / AI-generated"


def image_object(item, url):
    fields = provenance_fields(item) if not item.get("tool") else item
    return {"@type": "ImageObject", "@id": url + "#image", "contentUrl": url,
            "creator": {"@type": "Person", "name": fields["creator"]},
            "creditText": credit_text({**item, **fields}),
            "copyrightNotice": fields["copyright_notice"]}
