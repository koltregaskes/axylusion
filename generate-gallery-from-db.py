#!/usr/bin/env python3
"""
Generate gallery.json from universal.db

This script creates a fresh gallery.json from all items in the database,
preserving the existing gallery structure but using database as source of truth.
"""

import sqlite3
import json
import shutil
from datetime import datetime
from pathlib import Path

DB_PATH = Path("W:/Agent Workspace/System/Data/universal.db")
GALLERY_PATH = Path("W:/Agent Workspace/Projects/axylusion-repo/data/gallery.json")
BACKUP_PATH = GALLERY_PATH.with_suffix('.json.backup-before-rebuild')

def parse_midjourney_date(date_str):
    """
    Parse Midjourney date format: "Dec 21, 25, 8:36 PM"
    Returns ISO date string: "2025-12-21"
    """
    if not date_str:
        return "2026-02-10"  # Default fallback

    try:
        parts = date_str.split(',')
        month_day = parts[0].strip()
        year = f"20{parts[1].strip()}"
        dt = datetime.strptime(f"{month_day}, {year}", "%b %d, %Y")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return "2026-02-10"

def extract_version(raw_params):
    """Extract Midjourney version from raw parameters"""
    if not raw_params:
        return "Midjourney v7"

    # Look for version markers
    if "--v 7" in raw_params or "v7" in raw_params.lower():
        return "Midjourney v7"
    elif "--v 6" in raw_params or "v6" in raw_params.lower():
        return "Midjourney v6"
    elif "--v 5" in raw_params or "v5" in raw_params.lower():
        return "Midjourney v5"

    return "Midjourney v7"  # Default to v7

def extract_dimensions(aspect_ratio):
    """Convert aspect ratio to dimensions format"""
    if not aspect_ratio:
        return "16:9"

    # Common conversions
    ratio_map = {
        "1:1": "1:1",
        "16:9": "16:9",
        "9:16": "9:16",
        "3:2": "3:2",
        "2:3": "2:3",
        "4:3": "4:3",
        "3:4": "3:4"
    }

    return ratio_map.get(aspect_ratio, "16:9")

def categorize_prompt(prompt):
    """Auto-categorize based on prompt content"""
    if not prompt:
        return []

    tags = []
    prompt_lower = prompt.lower()

    # Subject detection
    if any(word in prompt_lower for word in ['portrait', 'face', 'headshot']):
        tags.append('portrait')
    if any(word in prompt_lower for word in ['woman', 'female', 'girl']):
        tags.append('woman')
    if any(word in prompt_lower for word in ['man', 'male', 'boy']):
        tags.append('man')

    # Style detection
    if any(word in prompt_lower for word in ['cinematic', 'film', 'movie']):
        tags.append('cinematic')
    if any(word in prompt_lower for word in ['fantasy', 'magic', 'dragon']):
        tags.append('fantasy')
    if any(word in prompt_lower for word in ['noir', 'dark', 'shadow']):
        tags.append('noir')
    if any(word in prompt_lower for word in ['comic', 'graphic novel', 'illustration']):
        tags.append('comic')
    if any(word in prompt_lower for word in ['photorealistic', 'realistic', 'photo']):
        tags.append('photorealistic')

    return tags if tags else ['general']

def main():
    print("=" * 70)
    print("GENERATING GALLERY.JSON FROM DATABASE")
    print("=" * 70)

    # Backup existing gallery.json
    print("\n[1/4] Creating backup of existing gallery.json...")
    if GALLERY_PATH.exists():
        shutil.copy2(GALLERY_PATH, BACKUP_PATH)
        print(f"   OK Backup saved to {BACKUP_PATH}")
    else:
        print("   OK No existing gallery.json to backup")

    # Load all items from database
    print("\n[2/4] Loading items from database...")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM midjourney_likes
        ORDER BY midjourney_created_at DESC
    """)

    db_items = cursor.fetchall()
    conn.close()
    print(f"   OK Loaded {len(db_items)} items from database")

    # Convert to gallery format
    print("\n[3/4] Converting to gallery format...")
    gallery_items = []

    for row in db_items:
        # Parse creation date
        created_date = parse_midjourney_date(row['midjourney_created_at'])

        # Build item
        item = {
            "id": row['job_id'],
            "name": f"Midjourney {row['job_id'][:8]}",  # Default name
            "type": "image",
            "source": "midjourney",
            "model": extract_version(row['raw_parameters']),
            "url": row['midjourney_url'] or f"https://www.midjourney.com/jobs/{row['job_id']}",
            "cdn_url": row['cdn_url'],
            "prompt": row['prompt'] or "",
            "parameters": row['raw_parameters'] or "",
            "dimensions": extract_dimensions(row['aspect_ratio']),
            "created": created_date,
            "tags": categorize_prompt(row['prompt'])
        }

        gallery_items.append(item)

    print(f"   OK Converted {len(gallery_items)} items")

    # Create gallery structure
    print("\n[4/4] Saving gallery.json...")
    gallery = {
        "items": gallery_items
    }

    with open(GALLERY_PATH, 'w', encoding='utf-8') as f:
        json.dump(gallery, f, indent=2, ensure_ascii=False)

    print(f"   OK Saved to {GALLERY_PATH}")

    # Final report
    print("\n" + "=" * 70)
    print("GENERATION COMPLETE")
    print("=" * 70)
    print(f"Total items:         {len(gallery_items)}")
    print(f"Items with dates:    {sum(1 for item in gallery_items if item['created'] != '2026-02-10')}")
    print(f"Backup location:     {BACKUP_PATH}")
    print(f"Gallery location:    {GALLERY_PATH}")
    print("=" * 70)
    print("\nNOTE: This is a complete rebuild. All previous gallery items have been")
    print("replaced with database content. Check the backup if you need old data.")
    print("=" * 70)

if __name__ == "__main__":
    main()
