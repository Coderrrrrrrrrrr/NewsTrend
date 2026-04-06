import sqlite3

def fix_encoding():
    db_path = "data/news_trend.db"
    conn = sqlite3.connect(db_path)
    # Re-update with correct encoding
    sources = [
        (1, '数字生命卡兹克', 'MzIyMzA5NjEyMA=='),
        (2, '饭统戴老板', 'MzU4NDY2MDMzMA=='),
        (3, '数字生命卡兹克 (Weibo)', '5700099573'),
        (4, '36Kr (36氪)', 'https://36kr.com/feed'),
        (5, '天眼·AI降本增效', 'AI 降本增效'),
        (6, '天眼·全球经济拐点', '全球宏观经济拐点')
    ]
    for sid, name, url in sources:
        conn.execute("UPDATE sources SET name = ?, url_or_key = ? WHERE id = ?", (name, url, sid))
    conn.commit()
    conn.close()
    print("Encoding fix applied successfully.")

if __name__ == "__main__":
    fix_encoding()
