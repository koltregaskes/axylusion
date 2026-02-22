#!/usr/bin/env python3
"""
Update gallery.js embedded data from data/gallery.json.

Reads the current gallery.js, locates the embedded data section
(lines 2 through the closing '};'), replaces it with the contents
of data/gallery.json, and preserves all JS code that follows.
"""

import json
import os
import sys

REPO = os.path.dirname(os.path.abspath(__file__))
GALLERY_JS = os.path.join(REPO, "gallery.js")
GALLERY_JSON = os.path.join(REPO, "data", "gallery.json")

def main():
    # --- Read gallery.js ---
    with open(GALLERY_JS, "r", encoding="utf-8") as f:
        lines = f.readlines()

    print(f"Read {len(lines)} lines from gallery.js")

    # --- Find the embedded data boundaries ---
    # Line 1 (index 0): comment
    # Line 2 (index 1): const embeddedData = {
    # We need to find the closing '};' that ends the data block.
    # Strategy: scan from top for the first line that is exactly '};'
    # (the embedded JSON object close), which marks the end of data.

    data_end_idx = None
    for i, line in enumerate(lines):
        if line.strip() == '};' and i > 1:
            data_end_idx = i
            break

    if data_end_idx is None:
        print("ERROR: Could not find closing '};' for embedded data.", file=sys.stderr)
        sys.exit(1)

    print(f"Embedded data ends at line {data_end_idx + 1} (0-indexed: {data_end_idx})")

    # Everything after the '};' line is JS code we must preserve
    js_code_lines = lines[data_end_idx + 1:]
    print(f"JS code section: {len(js_code_lines)} lines (starting at line {data_end_idx + 2})")

    # --- Read the new JSON data ---
    with open(GALLERY_JSON, "r", encoding="utf-8") as f:
        new_data = json.load(f)

    # Pretty-print JSON with 2-space indent to match original style
    new_json_str = json.dumps(new_data, indent=2, ensure_ascii=False)
    print(f"New JSON data: {len(new_json_str)} characters, "
          f"{new_json_str.count(chr(10)) + 1} lines")

    # --- Reconstruct gallery.js ---
    # Line 1: original comment
    header = lines[0]  # "// Gallery data - embedded for local file:// access...\n"

    with open(GALLERY_JS, "w", encoding="utf-8") as f:
        # 1. Write header comment
        f.write(header)
        # 2. Write the embedded data assignment
        f.write(f"const embeddedData = {new_json_str};\n")
        # 3. Write the preserved JS code
        for line in js_code_lines:
            f.write(line)

    # --- Verify ---
    with open(GALLERY_JS, "r", encoding="utf-8") as f:
        result_lines = f.readlines()

    print(f"\nResult: {len(result_lines)} lines written to gallery.js")

    # Verify the header
    assert result_lines[0].startswith("//"), "First line should be a comment"
    assert "const embeddedData" in result_lines[1], "Second line should declare embeddedData"

    # Verify JS code is still present at end
    last_line = result_lines[-1].strip()
    print(f"Last line: {last_line!r}")
    assert "loadData" in result_lines[-1] or any(
        "loadData" in l for l in result_lines[-5:]
    ), "loadData() call should be near the end"

    # Verify we can find key JS constructs
    full_text = "".join(result_lines)
    for keyword in ["renderGallery", "openModal", "addEventListener", "loadData"]:
        assert keyword in full_text, f"Missing JS keyword: {keyword}"

    print("All verification checks passed.")

if __name__ == "__main__":
    main()
