import sqlite3
import os

DB_PATH = "data/news_trend.db"

def init_db():
    if not os.path.exists("data"):
        os.makedirs("data")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # --- Sources Table (RSS, X Users, Akshare Keywords) ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL, -- 'rss', 'twitter', 'akshare', 'wechat'
        url_or_key TEXT NOT NULL,
        category TEXT, -- 'AI', 'Economy'
        last_fetched_at DATETIME,
        is_active BOOLEAN DEFAULT 1
    )
    ''')
    
    # --- News/Material Table (The "Materials Pool") ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id INTEGER,
        title TEXT NOT NULL,
        url TEXT UNIQUE,
        content_summary TEXT, -- LLM generated summary
        raw_content_preview TEXT, -- Preview of raw content (not stored full text)
        category TEXT, -- 'AI', 'Economy'
        score REAL, -- Total score (0-5)
        score_details TEXT, -- JSON format: {novelty: 4, utility: 5, ...}
        reasoning TEXT, -- AI's reasoning for the score
        logic_trace TEXT, -- AI's extracted logic for deep dive
        is_published BOOLEAN DEFAULT 0,
        published_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (source_id) REFERENCES sources (id)
    )
    ''')
    
    # --- Drafts Table (Drafts for different platforms) ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id INTEGER,
        platform TEXT, -- 'X', 'LinkedIn', 'WeChat', 'Substack'
        content TEXT,
        status TEXT DEFAULT 'pending', -- 'pending', 'published'
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (material_id) REFERENCES materials (id)
    )
    ''')
    
    # --- Audit Logs Table (Xingbu Audit) ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL, -- 'scraping', 'scoring', 'publishing', 'deletion'
        target_id INTEGER,
        details TEXT,
        status TEXT, -- 'success', 'failure', 'warning'
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()
