import feedparser
from datetime import datetime
from bs4 import BeautifulSoup
import sqlite3
import json
from src.utils.logger import audit_logger

class RSSCollector:
    def __init__(self, db_path="data/news_trend.db"):
        self.db_path = db_path

    def fetch_feed(self, url, category):
        """Fetches and processes RSS feed items with 'Burn After Reading' logic."""
        # Nitter integration for Twitter (X) RSS
        if 'twitter.com' in url or 'x.com' in url:
            # Reconstruct Twitter URL to Nitter (e.g., nitter.net)
            # This is a basic conversion, in reality user would provide Nitter RSS link
            print(f"⚠️ [刑部提示] 检测到 X (Twitter) 链接，建议使用 Nitter 镜像源以降低风险。")

        feed = feedparser.parse(url)
        new_items = []
        
        for entry in feed.entries:
            # Burn After Reading: Only extract preview, destroy full text in memory immediately
            summary_html = entry.get('summary', '') or entry.get('description', '')
            soup = BeautifulSoup(summary_html, 'html.parser')
            
            # 刑部铁律：严禁存储原文全篇，仅留存前 500 字概览用于 AI 摘要
            text_preview = soup.get_text()[:500] 

            item = {
                'title': entry.title,
                'url': entry.link,
                'raw_content_preview': text_preview,
                'category': category,
                'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            new_items.append(item)
            
        audit_logger.log_action("scraping", details=f"Fetched {len(new_items)} items from {url}", status="success")
        return new_items

    def save_items(self, items):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        saved_count = 0
        for item in items:
            try:
                cursor.execute('''
                INSERT OR IGNORE INTO materials (title, url, raw_content_preview, category, created_at)
                VALUES (?, ?, ?, ?, ?)
                ''', (item['title'], item['url'], item['raw_content_preview'], item['category'], item['created_at']))
                if cursor.rowcount > 0:
                    saved_count += 1
                conn.commit() # Commit each item
            except Exception as e:
                audit_logger.log_action("scraping", details=f"Error saving {item['url']}: {e}", status="failure")
        conn.commit()
        conn.close()
        return saved_count

if __name__ == "__main__":
    collector = RSSCollector()
    print("RSS Collector (Burn After Reading Edition) ready.")
