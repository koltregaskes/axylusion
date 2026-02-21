#!/usr/bin/env python3
"""
Image Migration Script for Axylusion
=====================================

Migrates gallery images from expired Midjourney CDN URLs to Cloudflare R2.

Usage:
    1. Download images from Midjourney (manually or via this script)
    2. Match downloaded files to gallery.json entries
    3. Upload to Cloudflare R2
    4. Update gallery.json and gallery.js with new URLs

Prerequisites:
    pip install boto3 requests

Environment variables (for R2 upload):
    R2_ACCOUNT_ID       - Cloudflare account ID
    R2_ACCESS_KEY_ID    - R2 API token access key
    R2_SECRET_ACCESS_KEY - R2 API token secret key
    R2_BUCKET_NAME      - R2 bucket name (e.g., "axylusion-images")
    R2_PUBLIC_URL       - Public URL for the bucket (e.g., "https://images.axylusion.com")
"""

import json
import os
import re
import sys
import hashlib
from pathlib import Path
from urllib.parse import urlparse


# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent
GALLERY_JSON = PROJECT_DIR / "data" / "gallery.json"
GALLERY_JS = PROJECT_DIR / "gallery.js"
DOWNLOAD_DIR = PROJECT_DIR / "scripts" / "downloaded-images"


def load_gallery():
    """Load gallery.json and return items."""
    with open(GALLERY_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    items = data if isinstance(data, list) else data.get("items", [])
    return items


def extract_job_id(cdn_url):
    """Extract Midjourney job ID from CDN URL.

    e.g., https://cdn.midjourney.com/4147cb5f-c531-47fd-b8a2-ab4ec1a424e9/0_0.png
    returns: 4147cb5f-c531-47fd-b8a2-ab4ec1a424e9
    """
    match = re.search(
        r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", cdn_url
    )
    return match.group(1) if match else None


def scan_downloaded_images(download_dir):
    """Scan a directory of downloaded images and extract job IDs from filenames.

    Midjourney downloads typically have the job ID in the filename.
    Supports formats like:
        - 4147cb5f-c531-47fd-b8a2-ab4ec1a424e9.png
        - koltregaskes_cinematic_portrait_4147cb5f-c531-47fd-b8a2-ab4ec1a424e9.png
        - Any file containing a UUID
    """
    download_path = Path(download_dir)
    if not download_path.exists():
        print(f"Download directory not found: {download_dir}")
        return {}

    image_map = {}  # job_id -> file_path
    extensions = {".png", ".jpg", ".jpeg", ".webp"}

    for file_path in download_path.rglob("*"):
        if file_path.suffix.lower() not in extensions:
            continue

        job_id = extract_job_id(file_path.name)
        if job_id:
            image_map[job_id] = file_path

    return image_map


def match_images(gallery_items, image_map):
    """Match gallery items to downloaded images by job ID."""
    matched = []
    unmatched = []

    for item in gallery_items:
        job_id = item.get("id") or extract_job_id(item.get("cdn_url", ""))
        if job_id and job_id in image_map:
            matched.append({"item": item, "file": image_map[job_id], "job_id": job_id})
        else:
            unmatched.append(item)

    return matched, unmatched


def upload_to_r2(matched_items):
    """Upload matched images to Cloudflare R2.

    Requires boto3 and R2 environment variables.
    """
    try:
        import boto3
    except ImportError:
        print("ERROR: boto3 not installed. Run: pip install boto3")
        return False

    account_id = os.environ.get("R2_ACCOUNT_ID")
    access_key = os.environ.get("R2_ACCESS_KEY_ID")
    secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")
    bucket_name = os.environ.get("R2_BUCKET_NAME", "axylusion-images")
    public_url = os.environ.get("R2_PUBLIC_URL", "")

    if not all([account_id, access_key, secret_key]):
        print("ERROR: R2 environment variables not set.")
        print("Required: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY")
        return False

    # Create R2 client
    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
    )

    uploaded = 0
    for entry in matched_items:
        file_path = entry["file"]
        job_id = entry["job_id"]
        ext = file_path.suffix.lower()

        # Use job_id as the R2 object key for clean URLs
        object_key = f"gallery/{job_id}{ext}"

        # Content type mapping
        content_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }

        try:
            s3.upload_file(
                str(file_path),
                bucket_name,
                object_key,
                ExtraArgs={
                    "ContentType": content_types.get(ext, "image/png"),
                    "CacheControl": "public, max-age=31536000",  # 1 year cache
                },
            )

            # Update the item's CDN URL
            if public_url:
                entry["item"]["cdn_url"] = f"{public_url}/{object_key}"

            uploaded += 1
            if uploaded % 50 == 0:
                print(f"  Uploaded {uploaded}/{len(matched_items)}...")

        except Exception as e:
            print(f"  Failed to upload {job_id}: {e}")

    print(f"Uploaded {uploaded}/{len(matched_items)} images to R2")
    return True


def update_gallery_json(items):
    """Save updated items back to gallery.json."""
    gallery = {"items": items}
    with open(GALLERY_JSON, "w", encoding="utf-8") as f:
        json.dump(gallery, f, indent=2, ensure_ascii=False)
    print(f"Updated {GALLERY_JSON}")


def update_gallery_js(items):
    """Update the embedded data in gallery.js."""
    gallery_data = json.dumps({"items": items}, indent=2, ensure_ascii=False)

    with open(GALLERY_JS, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the embedded data block
    # Pattern: const embeddedData = {...};
    # Then everything up to the next top-level code
    pattern = r"const embeddedData = \{.*?\n\};"
    replacement = f"const embeddedData = {gallery_data};"

    # Use a simpler approach: find start and end markers
    start_marker = "const embeddedData = {"
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("WARNING: Could not find embeddedData in gallery.js")
        return

    # Find the matching closing brace by counting braces
    brace_count = 0
    end_idx = start_idx + len(start_marker) - 1  # Position of opening {
    for i in range(end_idx, len(content)):
        if content[i] == "{":
            brace_count += 1
        elif content[i] == "}":
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1
                break

    # Find the semicolon after the closing brace
    if end_idx < len(content) and content[end_idx] == ";":
        end_idx += 1

    new_content = content[:start_idx] + replacement + content[end_idx:]

    with open(GALLERY_JS, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Updated {GALLERY_JS}")


def cmd_scan(args):
    """Scan downloaded images and report matches."""
    download_dir = args[0] if args else str(DOWNLOAD_DIR)

    print("=" * 60)
    print("SCANNING DOWNLOADED IMAGES")
    print("=" * 60)

    items = load_gallery()
    print(f"Gallery items: {len(items)}")

    image_map = scan_downloaded_images(download_dir)
    print(f"Downloaded images found: {len(image_map)}")

    matched, unmatched = match_images(items, image_map)
    print(f"Matched: {len(matched)}")
    print(f"Unmatched (need downloading): {len(unmatched)}")

    if unmatched:
        print(f"\nFirst 10 unmatched items:")
        for item in unmatched[:10]:
            print(f"  {item['id'][:8]}... - {item['name']}")

    print(f"\nTo download unmatched images, visit each on midjourney.com:")
    print(f"  https://www.midjourney.com/jobs/<job_id>")


def cmd_upload(args):
    """Upload matched images to R2 and update gallery files."""
    download_dir = args[0] if args else str(DOWNLOAD_DIR)

    print("=" * 60)
    print("UPLOADING IMAGES TO CLOUDFLARE R2")
    print("=" * 60)

    items = load_gallery()
    image_map = scan_downloaded_images(download_dir)

    matched, unmatched = match_images(items, image_map)
    print(f"Matched: {len(matched)} | Unmatched: {len(unmatched)}")

    if not matched:
        print("No matched images to upload.")
        return

    if upload_to_r2(matched):
        # Update both gallery.json and gallery.js
        update_gallery_json(items)
        update_gallery_js(items)
        print("\nDone! CDN URLs updated in gallery.json and gallery.js")
    else:
        print("\nUpload failed. Gallery files not updated.")


def cmd_export_urls(args):
    """Export all Midjourney URLs for manual download."""
    items = load_gallery()
    output_file = args[0] if args else str(SCRIPT_DIR / "download-urls.txt")

    with open(output_file, "w") as f:
        for item in items:
            job_id = item.get("id", "")
            url = f"https://www.midjourney.com/jobs/{job_id}"
            f.write(f"{url}\n")

    print(f"Exported {len(items)} URLs to {output_file}")
    print("Visit each URL on midjourney.com to download the image.")


def cmd_status(args):
    """Show current status of CDN URLs."""
    items = load_gallery()

    midjourney_cdn = 0
    r2_cdn = 0
    other = 0

    for item in items:
        url = item.get("cdn_url", "")
        if "cdn.midjourney.com" in url:
            midjourney_cdn += 1
        elif "r2" in url or "cloudflare" in url:
            r2_cdn += 1
        else:
            other += 1

    print("=" * 60)
    print("IMAGE HOSTING STATUS")
    print("=" * 60)
    print(f"Total items:          {len(items)}")
    print(f"Midjourney CDN (403): {midjourney_cdn}")
    print(f"Cloudflare R2:        {r2_cdn}")
    print(f"Other:                {other}")
    print()

    if midjourney_cdn > 0:
        print(f"WARNING: {midjourney_cdn} images still use Midjourney CDN (returns 403)")
        print("Run 'python migrate-images.py scan <download-dir>' to check progress")


if __name__ == "__main__":
    commands = {
        "scan": cmd_scan,
        "upload": cmd_upload,
        "export-urls": cmd_export_urls,
        "status": cmd_status,
    }

    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("Axylusion Image Migration Tool")
        print("=" * 40)
        print()
        print("Commands:")
        print("  status                    - Show current CDN URL status")
        print("  export-urls [output.txt]  - Export Midjourney URLs for manual download")
        print("  scan <download-dir>       - Scan downloaded images and match to gallery")
        print("  upload <download-dir>     - Upload matched images to R2 and update gallery")
        print()
        print("Workflow:")
        print("  1. Run 'status' to see how many images need migrating")
        print("  2. Run 'export-urls' to get list of Midjourney pages")
        print("  3. Download images from Midjourney (bulk download from archive)")
        print("  4. Run 'scan <dir>' to match downloads to gallery entries")
        print("  5. Set R2 environment variables (see script header)")
        print("  6. Run 'upload <dir>' to upload and update gallery")
        sys.exit(0)

    cmd = sys.argv[1]
    cmd_args = sys.argv[2:]
    commands[cmd](cmd_args)
