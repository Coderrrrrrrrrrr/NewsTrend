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
        """Fetches and processes RSS feed items."""
        feed = feedparser.parse(url)
        new_items = []
        
        for entry in feed.entries:
            summary_html = entry.get('summary', '') or entry.get('description', '')
            soup = BeautifulSoup(summary_html, 'html.parser')
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
                # V2.2: Add full_text_zip, permanent_url and status
                cursor.execute('''
                INSERT OR IGNORE INTO materials (title, url, raw_content_preview, full_text_zip, permanent_url, category, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item['title'], 
                    item['url'], 
                    item['raw_content_preview'], 
                    item.get('full_text_zip'), 
                    item.get('permanent_url', item['url']), 
                    item['category'], 
                    item['created_at'],
                    item.get('status', 'active')
                ))
                if cursor.rowcount > 0:
                    saved_count += 1
                conn.commit()
            except Exception as e:
                audit_logger.log_action("scraping", details=f"Error saving {item['url']}: {e}", status="failure")
        conn.close()
        return saved_count

if __name__ == "__main__":
    collector = RSSCollector()
    print("RSS Collector V2.2 ready.")
