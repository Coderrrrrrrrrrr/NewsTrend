import sqlite3
import json
from datetime import datetime
from src.utils.logger import audit_logger

class TwitterCollector:
    """
    V2.3: Twitter/X Intelligence Collector.
    Processes trends, tweets, and identity anchors into 'Intelligence Packs'.
    """
    def __init__(self, db_path="data/news_trend.db"):
        self.db_path = db_path

    def save_intelligence(self, trend, tweets, anchors, category="AI"):
        """
        Saves a 'Trend Intelligence' pack to the database.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Format the content
        title = f"X Trend: {trend}"
        # Use a search URL as the unique identifier
        url = f"https://twitter.com/search?q={trend.replace(' ', '%20')}&f=live"
        
        # Discovery/Depth/Anchors context
        context = {
            "discovery": f"Trend detected via Pulse Sampling: {trend}",
            "depth_count": len(tweets),
            "anchors": anchors,
            "tweets": tweets
        }
        
        # Create a rich preview for the main pool
        preview = f"### 🔭 Discovery: {context['discovery']}\n\n"
        preview += f"### ⚓ Identity Anchors: {', '.join(anchors) if anchors else 'None'}\n\n"
        preview += "### 📥 Depth Tweets (Top 5):\n"
        for t in tweets[:5]:
            text = t.get('text', '').replace('\n', ' ')
            preview += f"- {text} (ID: {t.get('id')})\n"
        
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # Check for existing
            cursor.execute("SELECT id FROM materials WHERE url = ?", (url,))
            if cursor.fetchone():
                return 0

            cursor.execute('''
            INSERT INTO materials (title, url, raw_content_preview, intelligence_context, category, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, url, preview, json.dumps(context, ensure_ascii=False), category, created_at, 'active'))
            
            saved = cursor.rowcount
            conn.commit()
            if saved > 0:
                audit_logger.log_action("scraping", details=f"Captured X Intelligence for: {trend}", status="success")
            return saved
        except Exception as e:
            audit_logger.log_action("scraping", details=f"Error saving X Intelligence: {e}", status="failure")
            return 0
        finally:
            conn.close()

if __name__ == "__main__":
    collector = TwitterCollector()
    print("Twitter Intelligence Collector V2.3 Ready.")
