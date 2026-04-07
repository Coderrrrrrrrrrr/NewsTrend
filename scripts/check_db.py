import sqlite3
conn = sqlite3.connect('data/news_trend.db')
results = conn.execute('SELECT id, title, score FROM materials WHERE title LIKE "X Trend:%"').fetchall()
print(f"Found {len(results)} X Trend items:")
for r in results:
    print(r)
conn.close()
