import sqlite3
import os

DB_PATH = "data/news_trend.db"

def add_test_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # AI Test Item
    cursor.execute("""
    INSERT OR IGNORE INTO materials (title, url, raw_content_preview, category) 
    VALUES (?, ?, ?, ?)
    """, ('Sora 2.0 发布', 'https://test.com/sora2', 'OpenAI 今日发布了 Sora 2.0，支持 4K 分辨率的 1 分钟视频生成，物理引擎大幅升级。', 'AI'))
    
    # Economy Test Item (if needed, but Akshare will provide some)
    
    conn.commit()
    conn.close()
    print("Test data inserted.")

if __name__ == "__main__":
    add_test_data()
