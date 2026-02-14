import json
import sqlite3

# Load gallery IDs
with open('W:/Agent Workspace/Projects/axylusion-repo/data/gallery.json', encoding='utf-8') as f:
    gallery = json.load(f)
    gallery_ids = set(item['id'] for item in gallery['items'])

# Load DB IDs
conn = sqlite3.connect('W:/Agent Workspace/System/Data/universal.db')
cursor = conn.cursor()
cursor.execute('SELECT job_id FROM midjourney_likes')
db_ids = set(row[0] for row in cursor.fetchall())
conn.close()

# Check overlap
overlap = gallery_ids.intersection(db_ids)

print(f'Gallery IDs: {len(gallery_ids)}')
print(f'DB IDs: {len(db_ids)}')
print(f'Overlap: {len(overlap)}')

if overlap:
    print(f'\nSample matching IDs:')
    for id in list(overlap)[:10]:
        print(f'  {id}')
