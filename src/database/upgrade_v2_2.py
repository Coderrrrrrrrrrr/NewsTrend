import sqlite3
import os

DB_PATH = "data/news_trend.db"

def upgrade_v2_2():
    """
    Upgrade database to V2.2:
    1. Add full_text_zip (BLOB) for compressed storage.
    2. Add permanent_url (TEXT) for redirect tracking.
    3. Add status (TEXT) for logical deletion ('active', 'deleted').
    """
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}, skipping upgrade.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check existing columns in materials table
    cursor.execute("PRAGMA table_info(materials)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Add status column if not exists
    if 'status' not in columns:
        print("Adding 'status' column to 'materials' table...")
        cursor.execute("ALTER TABLE materials ADD COLUMN status TEXT DEFAULT 'active'")
    
    # Add full_text_zip column if not exists
    if 'full_text_zip' not in columns:
        print("Adding 'full_text_zip' column to 'materials' table...")
        cursor.execute("ALTER TABLE materials ADD COLUMN full_text_zip BLOB")
        
    # Add columns to 'drafts' table
    cursor.execute("PRAGMA table_info(drafts)")
    d_columns = [row[1] for row in cursor.fetchall()]
    
    if 'published_at' not in d_columns:
        print("Adding 'published_at' column to 'drafts' table...")
        cursor.execute("ALTER TABLE drafts ADD COLUMN published_at DATETIME")
    
    if 'tokens_used' not in d_columns:
        print("Adding 'tokens_used' column to 'drafts' table...")
        cursor.execute("ALTER TABLE drafts ADD COLUMN tokens_used INTEGER DEFAULT 0")

    # Add columns to 'audit_logs' table
    cursor.execute("PRAGMA table_info(audit_logs)")
    a_columns = [row[1] for row in cursor.fetchall()]

    if 'tokens_used' not in a_columns:
        print("Adding 'tokens_used' column to 'audit_logs' table...")
        cursor.execute("ALTER TABLE audit_logs ADD COLUMN tokens_used INTEGER DEFAULT 0")

    if 'model_name' not in a_columns:
        print("Adding 'model_name' column to 'audit_logs' table...")
        cursor.execute("ALTER TABLE audit_logs ADD COLUMN model_name TEXT")
        
    conn.commit()
    conn.close()
    print("Database upgrade to V2.2 completed.")

if __name__ == "__main__":
    upgrade_v2_2()
