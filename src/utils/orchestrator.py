import sqlite3
import threading
import json
import zlib
from datetime import datetime, timedelta
from src.collectors.rss_collector import RSSCollector
from src.collectors.akshare_collector import EconomyCollector
from src.collectors.url_scraper import URLScraper
from src.engine.scorer import AIScorer
from src.utils.logger import audit_logger
from src.collectors.sogou_scraper import SogouWeChatScraper
from src.engine.formatter import OmniFormatter
from src.collectors.weibo_collector import WeiboCollector
from src.collectors.agent_search import AgentSearchCollector

class IntelligenceOrchestrator:
    def __init__(self, db_path="data/news_trend.db"):
        self.db_path = db_path
        self.rss_collector = RSSCollector(db_path)
        self.econ_collector = EconomyCollector(db_path)
        self.weibo_collector = WeiboCollector(db_path)
        self.agent_search_collector = AgentSearchCollector(db_path)
        self.url_scraper = URLScraper()
        self.sogou_scraper = SogouWeChatScraper()
        self.scorer = AIScorer(db_path)
        self.formatter = OmniFormatter(db_path)
        self.token_limit_daily = 1800000 

    def _is_duplicate(self, title, url, permanent_url=None):
        """Checks if a material already exists by URL, permanent_url or title."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check by exact URL or permanent_url
        if permanent_url:
            cursor.execute("SELECT id FROM materials WHERE url = ? OR permanent_url = ? OR url = ? OR permanent_url = ?", (url, url, permanent_url, permanent_url))
        else:
            cursor.execute("SELECT id FROM materials WHERE url = ? OR permanent_url = ?", (url, url))
            
        if cursor.fetchone():
            conn.close()
            return True
            
        # Check by title
        cursor.execute("SELECT id FROM materials WHERE title = ?", (title,))
        if cursor.fetchone():
            conn.close()
            return True
        
        conn.close()
        return False

    def fetch_source(self, source_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, type, url_or_key, category FROM sources WHERE id = ?", (source_id,))
        source = cursor.fetchone()
        conn.close()

        if not source:
            return 0

        name, stype, url, category = source
        stype_lower = stype.lower()
        print(f"[{datetime.now()}] [*] 侦察节点启动: {name} (类型: {stype})")
        audit_logger.log_action("scraping", target_id=source_id, details=f"Starting check for {name} ({stype})", status="info")
        
        items = []
        try:
            if 'wechat' in stype_lower:
                print(f"[{datetime.now()}] [Node 2.1] 执行微信专线爬取: {name}")
                items = self.rss_collector.fetch_feed(url, category) if url and url.startswith("http") else []
                if not items:
                    print(f"[{datetime.now()}] [Node 2.2] RSS 失败，切换三位一体爬虫: {name}")
                    items = self.sogou_scraper.fetch_latest_articles(name)
            elif 'weibo' in stype_lower:
                items = self.weibo_collector.fetch_latest_posts(url)
            elif any(x in stype_lower for x in ['rss', 'blog', 'arxiv']):
                items = self.rss_collector.fetch_feed(url, category)
            elif 'akshare' in stype_lower:
                items = self.econ_collector.fetch_macro_news()
            elif 'search' in stype_lower:
                items = self.agent_search_collector.hunt_for_materials(category)
            else:
                return 0

            final_items = []
            junk_keywords = ["搜狗搜索", "验证码", "Weixin", "用户您好，您的访问过于频繁", "Sogou", "VerifyCode", "请输入验证码", "机器人"]
            pdf_binary_markers = ["%PDF-", "obj", "stream", "endobj", "xref"]
            
            for item in items:
                title = item.get('title', '')
                preview = item.get('raw_content_preview', '')
                
                # Check for junk keywords
                if any(kw in title for kw in junk_keywords) or any(kw in preview for kw in junk_keywords):
                    continue
                
                # V2.3: Prevent PDF binary/garbled content
                if "%PDF" in preview[:20] or (any(m in preview for m in pdf_binary_markers) and "%PDF" in preview):
                    continue

                if self._is_duplicate(title, item['url'], item.get('permanent_url')):
                    continue
                if len(preview.strip()) < 100:
                    continue
                final_items.append(item)

            saved = 0
            if final_items:
                if 'akshare' in stype_lower:
                    saved = self.econ_collector.save_items(final_items)
                else:
                    saved = self.rss_collector.save_items(final_items)
                
                if saved > 0:
                    audit_logger.log_action("scraping", target_id=source_id, details=f"Found {saved} new items for {name}", status="success")
            
            conn = sqlite3.connect(self.db_path)
            conn.execute("UPDATE sources SET last_fetched_at = datetime('now') WHERE id = ?", (source_id,))
            conn.commit()
            conn.close()
            
            return saved
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            return 0

    def run_scoring(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Only score active items
        cursor.execute("SELECT id, title, category FROM materials WHERE score IS NULL AND status = 'active'")
        unscored = cursor.fetchall()
        conn.close()

        if not unscored:
            return 0

        for mid, title, category in unscored:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT raw_content_preview FROM materials WHERE id = ?", (mid,))
            content = cursor.fetchone()[0]
            conn.close()
            self.scorer.score_material(mid, content, category)
        return len(unscored)

    def crawl_all_active(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM sources WHERE is_active = 1")
        active_sources = cursor.fetchall()
        conn.close()

        total_saved = 0
        for sid, name in active_sources:
            saved = self.fetch_source(sid)
            total_saved += saved
        
        scored_count = self.run_scoring()
        return total_saved, scored_count

    def reread_material(self, material_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT url, category FROM materials WHERE id = ?", (material_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return False

        url, category = row
        data = self.url_scraper.scrape_url(url, ignore_filters=True)
        if not data:
            return False
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
        UPDATE materials 
        SET title = ?, url = ?, raw_content_preview = ?, full_text_zip = ?, permanent_url = ?, score = NULL, score_details = NULL, content_summary = NULL, reasoning = NULL, status = 'active'
        WHERE id = ?
        """, (data['title'], data['url'], data['raw_content_preview'], data.get('full_text_zip'), data.get('url'), material_id))
        conn.commit()
        conn.close()
        
        self.scorer.score_material(material_id, data['raw_content_preview'], category)
        return True

    def process_single_url(self, url, category):
        data = self.url_scraper.scrape_url(url)
        if not data:
            return None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
            INSERT OR IGNORE INTO materials (title, url, raw_content_preview, full_text_zip, permanent_url, category, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (data['title'], data['url'], data['raw_content_preview'], data.get('full_text_zip'), data.get('url'), category, data['created_at'], 'active'))
            conn.commit()
            
            cursor.execute("SELECT id FROM materials WHERE url = ?", (data['url'],))
            mid = cursor.fetchone()[0]
            conn.close()
            
            result = self.scorer.score_material(mid, data['raw_content_preview'], category)
            return result
        except Exception as e:
            return None

    def logical_delete_material(self, material_id):
        """Marks a material as 'deleted' to prevent re-scraping."""
        conn = sqlite3.connect(self.db_path, timeout=30)
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE materials SET status = 'deleted' WHERE id = ?", (material_id,))
            conn.commit()
            changes = conn.total_changes
            audit_logger.log_action("deletion", target_id=material_id, details=f"Logical delete status: {changes} rows affected", status="success")
            return changes > 0
        except Exception as e:
            print(f"Error logical deleting material {material_id}: {e}")
            audit_logger.log_action("deletion", target_id=material_id, details=f"Error: {e}", status="failure")
            return False
        finally:
            conn.close()

    def get_full_text(self, material_id):
        """Retrieves and decompresses the full text from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT full_text_zip FROM materials WHERE id = ?", (material_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row or not row[0]:
            return None
        
        try:
            decompressed_text = zlib.decompress(row[0]).decode('utf-8')
            return decompressed_text
        except Exception as e:
            print(f"Error decompressing text for material {material_id}: {e}")
            return None

    def check_token_budget(self):
        """V2.2: Ensure we don't exceed daily token budget (1.8M tokens)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate tokens used today in audit_logs and drafts
        cursor.execute("""
            SELECT SUM(tokens_used) FROM (
                SELECT tokens_used FROM audit_logs WHERE date(created_at, 'localtime') = date('now', 'localtime')
                UNION ALL
                SELECT tokens_used FROM drafts WHERE date(created_at, 'localtime') = date('now', 'localtime')
            )
        """)
        total_used = cursor.fetchone()[0] or 0
        conn.close()
        
        BUDGET = 1800000
        if total_used > BUDGET:
            audit_logger.warning(f"DAILY TOKEN BUDGET EXCEEDED: {total_used}/{BUDGET}. Pausing non-critical operations.")
            return False
        return True

    def run_pipeline(self, category="AI"):
        """Execute the full content production pipeline"""
        if not self.check_token_budget():
            return False

        audit_logger.log_action("pipeline", details=f"Starting NewsTrend Pipeline for {category}...", status="info")
        
        # 1. Crawl all active sources
        total_saved, scored_count = self.crawl_all_active()
        print(f"[*] Pipeline Status: Found {total_saved} new items, Scored {scored_count} items.")
        
        # 2. Get high-scoring items for user to review
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM materials 
            WHERE score >= 3.8 
            AND status = 'active' 
            AND id NOT IN (SELECT DISTINCT material_id FROM drafts)
            ORDER BY score DESC
        """)
        high_score_items = cursor.fetchall()
        conn.close()
        
        print(f"[*] Pipeline Status: {len(high_score_items)} high-score items found for review.")
            
        audit_logger.log_action("pipeline", details="Pipeline execution completed. High-score items ready for manual drafting.", status="success")
        return True
