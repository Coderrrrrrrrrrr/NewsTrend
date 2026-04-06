import sqlite3

db_path = "data/news_trend.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Find trash items
trash_keywords = ["搜狗搜索", "验证码", "VerifyCode", "机器人", "访问过于频繁"]
trash_ids = []

cursor.execute("SELECT id, title, raw_content_preview FROM materials WHERE status = 'active'")
rows = cursor.fetchall()

for mid, title, preview in rows:
    is_trash = False
    if title and any(kw in title for kw in trash_keywords):
        is_trash = True
    if preview and any(kw in preview for kw in trash_keywords):
        is_trash = True
    
    if is_trash:
        trash_ids.append(mid)

if trash_ids:
    print(f"Found {len(trash_ids)} trash items: {trash_ids}")
    # Batch delete
    placeholders = ','.join(['?'] * len(trash_ids))
    cursor.execute(f"UPDATE materials SET status = 'deleted' WHERE id IN ({placeholders})", trash_ids)
    conn.commit()
    print("Batch logical deletion complete.")
else:
    print("No trash items found in active list.")

conn.close()
