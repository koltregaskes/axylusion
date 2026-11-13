"""Public site settings. Leave email empty until a working address is confirmed."""
import json
from html import escape
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def contact_link():
    email = json.loads((ROOT / "data/site-config.json").read_text(encoding="utf-8"))["contact_email"]
    if not email:
        return ""
    if not isinstance(email, str) or email.count("@") != 1 or any(c.isspace() or c in "<>\"'?:&" for c in email):
        raise ValueError("Invalid public contact_email")
    return f'<a href="mailto:{escape(email, quote=True)}">{escape(email)}</a>'
