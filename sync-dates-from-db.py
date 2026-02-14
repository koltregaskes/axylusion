#!/usr/bin/env python3
"""
Sync creation dates from universal.db to gallery.json

This script:
1. Reads all Midjourney creation dates from System/Data/universal.db
2. Updates corresponding items in data/gallery.json
3. Creates a backup before modification
4. Reports on success/failure statistics
"""

import sqlite3
import json
import shutil
from datetime import datetime
from pathlib import Path

# Paths
DB_PATH = Path("W:/Agent Workspace/System/Data/universal.db")
GALLERY_PATH = Path("W:/Agent Workspace/Projects/axylusion-repo/data/gallery.json")
BACKUP_PATH = GALLERY_PATH.with_suffix('.json.backup')

def parse_midjourney_date(date_str):
    """
    Parse Midjourney date format: "Dec 21, 25, 8:36 PM"
    Returns ISO date string: "2025-12-21"
    """
    if not date_str:
        return None

    try:
        # Parse format: "Dec 21, 25, 8:36 PM"
        parts = date_str.split(',')
        month_day = parts[0].strip()  # "Dec 21"
        year = f"20{parts[1].strip()}"  # "25" -> "2025"

        # Parse month and day
        dt = datetime.strptime(f"{month_day}, {year}", "%b %d, %Y")
        return dt.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Warning: Failed to parse date '{date_str}': {e}")
        return None

def main():
    print("=" * 60)
    print("SYNCING CREATION DATES FROM DATABASE TO GALLERY.JSON")
    print("=" * 60)

    # 1. Load dates from database
    print("\n[1/5] Loading creation dates from database...")
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("""
        SELECT job_id, midjourney_created_at
        FROM midjourney_likes
        WHERE midjourney_created_at IS NOT NULL
    """)

    date_map = {}
    for mj_id, date_str in cursor.fetchall():
        iso_date = parse_midjourney_date(date_str)
        if iso_date:
            date_map[mj_id] = iso_date

    conn.close()
    print(f"   OK Loaded {len(date_map)} dates from database")

    # 2. Backup gallery.json
    print("\n[2/5] Creating backup...")
    shutil.copy2(GALLERY_PATH, BACKUP_PATH)
    print(f"   OK Backup saved to {BACKUP_PATH}")

    # 3. Load gallery.json
    print("\n[3/5] Loading gallery.json...")
    with open(GALLERY_PATH, 'r', encoding='utf-8') as f:
        gallery = json.load(f)

    total_items = len(gallery['items'])
    print(f"   OK Loaded {total_items} items from gallery")

    # 4. Update dates
    print("\n[4/5] Updating creation dates...")
    updated = 0
    missing = 0
    already_correct = 0

    for item in gallery['items']:
        item_id = item.get('id')

        if item_id in date_map:
            new_date = date_map[item_id]
            old_date = item.get('created')

            if old_date != new_date:
                item['created'] = new_date
                updated += 1
            else:
                already_correct += 1
        else:
            missing += 1

    print(f"   OK Updated: {updated}")
    print(f"   - Already correct: {already_correct}")
    print(f"   - Missing from DB: {missing}")

    # 5. Save updated gallery.json
    print("\n[5/5] Saving updated gallery.json...")
    with open(GALLERY_PATH, 'w', encoding='utf-8') as f:
        json.dump(gallery, f, indent=2, ensure_ascii=False)

    print(f"   OK Saved to {GALLERY_PATH}")

    # Final report
    print("\n" + "=" * 60)
    print("SYNC COMPLETE")
    print("=" * 60)
    print(f"Total items:       {total_items}")
    print(f"Updated:           {updated}")
    print(f"Already correct:   {already_correct}")
    print(f"Missing from DB:   {missing}")
    print(f"Success rate:      {((updated + already_correct) / total_items * 100):.1f}%")
    print("\nBackup location:", BACKUP_PATH)
    print("=" * 60)

if __name__ == "__main__":
    main()
