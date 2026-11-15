#!/usr/bin/env python3
"""Add provenance to both manifests without changing existing fields or order."""
import argparse
import json
from pathlib import Path
from provenance import provenance_fields

ROOT = Path(__file__).resolve().parent.parent


def migrate(root=ROOT, check=False):
    paths = [root / "data" / name for name in ("gallery.json", "homepage-gallery.json")]
    payloads = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    lookup = {item["id"]: item for item in payloads[0]["items"]}
    # Validate every item before writing either file.
    for payload in payloads:
        for item in payload["items"]:
            item.update(provenance_fields(item, lookup[item["id"]]))
    stale = []
    for path, payload in zip(paths, payloads):
        original = path.read_bytes()
        newline = "\r\n" if b"\r\n" in original else "\n"
        # Retain each file's existing two-space JSON, escaping and newline style.
        ensure_ascii = b"\\u" in original
        rendered = (json.dumps(payload, indent=2, ensure_ascii=ensure_ascii) + "\n").replace("\n", newline).encode("utf-8")
        if original != rendered:
            stale.append(path.name)
            if not check:
                path.write_bytes(rendered)
        print(f"{path.name}: {len(payload['items'])} provenance records; "
              f"{'stale' if check and original != rendered else 'current' if check else 'migrated'}")
    return int(check and bool(stale))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    raise SystemExit(migrate(check=parser.parse_args().check))
