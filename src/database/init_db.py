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
        permanent_url TEXT, -- V2.2: Redirect tracking
        content_summary TEXT, -- LLM generated summary
        raw_content_preview TEXT, -- Preview of raw content
        full_text_zip BLOB, -- V2.2: Deep Cold Storage (zlib compressed)
        category TEXT, -- 'AI', 'Economy'
        score REAL, -- Total score (0-5)
        score_details TEXT, -- JSON format
        reasoning TEXT, -- AI's reasoning
        logic_trace TEXT, -- AI's extracted logic
        is_published BOOLEAN DEFAULT 0,
        published_at DATETIME,
        status TEXT DEFAULT 'active', -- V2.2: 'active', 'deleted'
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
        tokens_used INTEGER DEFAULT 0, -- V2.2: Audit tokens
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        published_at DATETIME, -- V2.2: Track publishing time
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
        tokens_used INTEGER DEFAULT 0, -- V2.2: Track token consumption
        model_name TEXT, -- V2.2: Track model used
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()
