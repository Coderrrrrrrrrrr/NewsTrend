import sqlite3
import os

DB_PATH = "data/news_trend.db"

def upgrade_v2_3_twitter():
    """V2.3: Add intelligence_context to materials for Twitter/X tracking."""
    if not os.path.exists(DB_PATH):
        print("Database not found. Run init_db.py first.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(materials)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'intelligence_context' not in columns:
        print("Adding intelligence_context column to materials...")
        cursor.execute("ALTER TABLE materials ADD COLUMN intelligence_context TEXT")
        print("Column added successfully.")
    else:
        print("intelligence_context column already exists.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    upgrade_v2_3_twitter()
