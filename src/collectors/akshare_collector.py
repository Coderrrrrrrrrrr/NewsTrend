import akshare as ak
import pandas as pd
from datetime import datetime
import sqlite3
from src.utils.logger import audit_logger

class EconomyCollector:
    """Uses Akshare to collect macro economic news and financial metrics."""
    def __init__(self, db_path="data/news_trend.db"):
        self.db_path = db_path

    def fetch_macro_news(self):
        # Fetch news from mainstream sources via Akshare
        try:
            # Using stock_news_em for real URLs
            news_df = ak.stock_news_em(symbol="sh600519") # Example: 茅台新闻作为宏观参考
            items = []
            for i, row in news_df.head(10).iterrows():
                # 刑部铁律：严禁存储原文全篇，仅留存前 500 字概览用于 AI 摘要
                content = row['内容'] if '内容' in row else row['文章标题']
                preview = content[:500]
                items.append({
                    'title': row['文章标题'],
                    'url': row['文章链接'],
                    'raw_content_preview': preview,
                    'category': 'Economy',
                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            audit_logger.log_action("scraping", details=f"Fetched {len(items)} macro news items", status="success")
            return items
        except Exception as e:
            # Fallback to CCTV if EM news fails, though CCTV links are harder to get
            print(f"EM News fetch failed: {e}, falling back to CCTV...")
            try:
                news_df = ak.news_cctv()
                items = []
                for i, row in news_df.head(5).iterrows():
                    # Handle case where column might be missing
                    content = row.get('content', row.get('内容', ''))
                    items.append({
                        'title': content[:50] + "...",
                        'url': f"https://tv.cctv.com/lm/xwlb/index.shtml?date={row['date']}", # Link to XWLB index
                        'raw_content_preview': content[:500],
                        'category': 'Economy',
                        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                return items
            except Exception as e2:
                audit_logger.log_action("scraping", details=f"Akshare news fetch error: {e2}", status="failure")
                return []
        except Exception as e:
            audit_logger.log_action("scraping", details=f"Akshare news fetch error: {e}", status="failure")
            return []

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
            except Exception as e:
                pass
        conn.commit()
        conn.close()
        return saved_count

if __name__ == "__main__":
    collector = EconomyCollector()
    print("Akshare Economy Collector ready.")
