import sqlite3
import threading
import json
from datetime import datetime, timedelta
from src.collectors.rss_collector import RSSCollector
from src.collectors.akshare_collector import EconomyCollector
from src.collectors.url_scraper import URLScraper
from src.engine.scorer import AIScorer
from src.utils.logger import audit_logger
from src.collectors.sogou_scraper import SogouWeChatScraper
from src.engine.formatter import OmniFormatter
from src.collectors.weibo_collector import WeiboCollector

class IntelligenceOrchestrator:
    def __init__(self, db_path="data/news_trend.db"):
        self.db_path = db_path
        self.rss_collector = RSSCollector(db_path)
        self.econ_collector = EconomyCollector(db_path)
        self.weibo_collector = WeiboCollector(db_path)
        self.url_scraper = URLScraper()
        self.sogou_scraper = SogouWeChatScraper()
        self.scorer = AIScorer(db_path)
        self.formatter = OmniFormatter(db_path)
        self.token_limit_daily = 500000 # Default daily token budget

    def create_historical_task(self, source_id, source_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO background_tasks (source_id, source_name, progress, status, last_message)
        VALUES (?, ?, ?, ?, ?)
        """, (source_id, source_name, "0%", "running", "Task started"))
        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Start in thread
        threading.Thread(target=self._run_historical_task, args=(task_id, source_id, source_name), daemon=True).start()
        return task_id

    def _run_historical_task(self, task_id, source_id, source_name):
        try:
            self._update_task(task_id, "10%", "running", f"Searching historical data for {source_name}...")
            
            # For WeChat, we use Sogou as a starting point for historical articles
            articles = self.sogou_scraper.fetch_latest_articles(source_name)
            
            if not articles:
                self._update_task(task_id, "100%", "failed", "No historical articles found.")
                return

            total = len(articles)
            processed = 0
            new_processed = 0
            
            for art in articles:
                self._update_task(task_id, f"{int(10 + (processed/total)*90)}%", "running", f"Checking: {art['title']}")
                
                # Deduplication Check
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM historical_archives WHERE url = ?", (art['url'],))
                existing = cursor.fetchone()
                
                if existing:
                    print(f"[*] Skipping existing article: {art['title']}")
                    self._log_task_item(task_id, art['title'], "skipped (exists)")
                    conn.close()
                    processed += 1
                    continue
                
                # 1. Save to historical_archives
                cursor.execute("""
                INSERT INTO historical_archives (source_id, title, url, category, published_at)
                VALUES (?, ?, ?, ?, ?)
                """, (source_id, art['title'], art['url'], art['category'], art['created_at']))
                archive_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                # 2. Score
                self._log_task_item(task_id, art['title'], "processing")
                self._score_historical(archive_id, art['raw_content_preview'], art['category'])
                self._log_task_item(task_id, art['title'], "completed")
                
                processed += 1
                new_processed += 1

            self._update_task(task_id, "100%", "completed", f"Finished. Processed {processed} items ({new_processed} new).")
            
        except Exception as e:
            print(f"Historical task error: {e}")
            self._update_task(task_id, "0%", "failed", f"Error: {str(e)}")

    def _log_task_item(self, task_id, title, status):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
        INSERT INTO task_logs (task_id, item_title, status)
        VALUES (?, ?, ?)
        """, (task_id, title, status))
        conn.commit()
        conn.close()

    def _update_task(self, task_id, progress, status, message):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
        UPDATE background_tasks 
        SET progress = ?, status = ?, last_message = ? 
        WHERE id = ?
        """, (progress, status, message, task_id))
        conn.commit()
        conn.close()

    def _score_historical(self, archive_id, content, category):
        # Use the general scoring method
        result = self.scorer.score_content(content, category)
        if result:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
            UPDATE historical_archives 
            SET score = ?, score_details = ?, content_summary = ? 
            WHERE id = ?
            """, (result['score'], json.dumps(result['details'], ensure_ascii=False), result['summary'], archive_id))
            conn.commit()
            conn.close()
            audit_logger.log_action("historical_scoring", target_id=archive_id, details=f"Historical Score: {result['score']}", status="success", tokens_used=result.get('tokens_used', 0))

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
            # Reordered: Check WeChat first to prevent it being caught by general RSS branch
            if 'wechat' in stype_lower:
                # Fallback to Sogou Search if it's a WeChat source
                print(f"[{datetime.now()}] [Node 2.1] 执行微信专线爬取: {name}")
                items = self.rss_collector.fetch_feed(url, category) if url and url.startswith("http") else []
                if not items:
                    print(f"[{datetime.now()}] [Node 2.2] RSS 失败，切换搜狗搜索策略: {name}")
                    items = self.sogou_scraper.fetch_latest_articles(name)
                
                if not items:
                    # Final fallback: Web Search
                    print(f"[{datetime.now()}] [Node 2.3] 搜狗失败，尝试全球搜索兜底: {name}")
                    try:
                        from src.utils.web_tools import perform_web_search
                        search_results = perform_web_search(f'site:mp.weixin.qq.com "{name}"')
                        for res in search_results[:5]:
                            data = self.url_scraper.scrape_url(res['url'])
                            if data:
                                items.append({
                                    "title": data['title'],
                                    "url": data['url'],
                                    "raw_content_preview": data['raw_content_preview'],
                                    "category": category,
                                    "created_at": data['created_at']
                                })
                    except Exception as e:
                        print(f"Web search fallback failed: {e}")
            elif 'weibo' in stype_lower:
                # Use Weibo UID (passed in url field)
                uid = url
                print(f"[{datetime.now()}] [Node 2.4] 执行微博 UID 抓取 (UID: {uid}): {name}")
                items = self.weibo_collector.fetch_latest_posts(uid)
            elif any(x in stype_lower for x in ['rss', 'blog', 'arxiv']):
                print(f"[{datetime.now()}] [Node 2.5] 执行标准 RSS 抓取: {name}")
                items = self.rss_collector.fetch_feed(url, category)
            elif 'akshare' in stype_lower:
                print(f"[{datetime.now()}] [Node 2.6] 执行宏观经济数据同步 (Akshare): {name}")
                items = self.econ_collector.fetch_macro_news()
            else:
                print(f"[!] Unsupported source type: {stype}")
                audit_logger.log_action("scraping", target_id=source_id, details=f"Unsupported source type: {stype}", status="warning")
                return 0

            # Filter duplicates and empty items
            final_items = []
            for item in items:
                # 1. Check for duplicates
                if self._is_duplicate(item['title'], item['url']):
                    continue
                
                # 2. Check for blank content
                if len(item.get('raw_content_preview', '').strip()) < 50:
                    continue
                
                final_items.append(item)

            # 统一保存新素材
            saved = 0
            if final_items:
                if 'akshare' in stype_lower:
                    saved = self.econ_collector.save_items(final_items)
                else:
                    saved = self.rss_collector.save_items(final_items)
                
                if saved > 0:
                    print(f"[{datetime.now()}] [OK] 捕获到 {saved} 条新素材: {name}")
                    audit_logger.log_action("scraping", target_id=source_id, details=f"Found {saved} new items for {name}", status="success")
                else:
                    print(f"[{datetime.now()}] [-] 未发现增量更新: {name}")
            else:
                print(f"[{datetime.now()}] [-] 采集返回 0 项 (可能无更新或触发反爬): {name}")
            
            # Update last_fetched_at
            conn = sqlite3.connect(self.db_path)
            conn.execute("UPDATE sources SET last_fetched_at = datetime('now') WHERE id = ?", (source_id,))
            conn.commit()
            conn.close()
            
            return saved

        except Exception as e:
            print(f"[{datetime.now()}] [!] 侦察失败 {name}: {e}")
            audit_logger.log_action("scraping", target_id=source_id, details=f"Error fetching {name}: {str(e)}", status="failure")
            return 0

    def _is_duplicate(self, title, url):
        """Checks if a material already exists by URL or title (to avoid similar content from different platforms)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check by exact URL
        cursor.execute("SELECT id FROM materials WHERE url = ?", (url,))
        if cursor.fetchone():
            conn.close()
            return True
            
        # Check by title
        cursor.execute("SELECT id FROM materials WHERE title = ?", (title,))
        if cursor.fetchone():
            conn.close()
            return True
        
        # Also check historical archives
        cursor.execute("SELECT id FROM historical_archives WHERE url = ? OR title = ?", (url, title))
        if cursor.fetchone():
            conn.close()
            return True
            
        conn.close()
        return False

    def check_token_budget(self):
        """Checks if today's token consumption exceeds the daily limit."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate tokens used in the last 24 hours
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("SELECT SUM(tokens_used) FROM audit_logs WHERE created_at > ?", (yesterday,))
        total_used = cursor.fetchone()[0] or 0
        conn.close()
        
        if total_used >= self.token_limit_daily:
            print(f"[!] Warning: Daily token budget ({self.token_limit_daily}) exceeded. Current: {total_used}")
            audit_logger.log_action("finance", details=f"Budget exceeded: {total_used}/{self.token_limit_daily}", status="warning")
            return False
        return True

    def run_scoring(self):
        if not self.check_token_budget():
            print(f"[{datetime.now()}] [!] 令牌预算不足，评分任务自动挂起。")
            return 0
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, category FROM materials WHERE score IS NULL")
        unscored = cursor.fetchall()
        conn.close()

        if not unscored:
            print(f"[{datetime.now()}] [-] 暂无需要评分的素材。")
            return 0

        print(f"[{datetime.now()}] >>> 发现 {len(unscored)} 条未评分素材，开始调用 DeepSeek 执行分析...")
        for mid, title, category in unscored:
            print(f"[{datetime.now()}] [*] 正在对 ID {mid} 进行深度打分: {title[:30]}...")
            # We need raw_content_preview for scoring
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT raw_content_preview FROM materials WHERE id = ?", (mid,))
            content = cursor.fetchone()[0]
            conn.close()
            
            self.scorer.score_material(mid, content, category)
        
        print(f"[{datetime.now()}] <<< AI 评分节点执行完毕。")
        return len(unscored)

    def generate_drafts_for_high_scores(self, threshold=4.5, platforms=['X', 'LinkedIn']):
        """Proactively generate drafts for highly rated materials."""
        if not self.check_token_budget():
            print("[!] Draft generation aborted due to budget constraints.")
            return 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM materials WHERE score >= ? AND id NOT IN (SELECT material_id FROM drafts)", (threshold,))
        high_score_ids = [r[0] for r in cursor.fetchall()]
        conn.close()
        
        count = 0
        for mid in high_score_ids:
            for platform in platforms:
                if self.formatter.generate_draft(mid, platform):
                    count += 1
        return count

    def crawl_all_active(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM sources WHERE is_active = 1")
        active_sources = cursor.fetchall()
        conn.close()

        print(f"[{datetime.now()}] >>> 发现 {len(active_sources)} 个活跃情报源，开始逐一侦察...")
        total_saved = 0
        for sid, name in active_sources:
            print(f"[{datetime.now()}] [*] 侦察节点: {name} (ID: {sid})")
            saved = self.fetch_source(sid)
            total_saved += saved
        
        print(f"[{datetime.now()}] [*] 抓取阶段结束。开始执行 AI 智能评分节点...")
        scored_count = self.run_scoring()
        return total_saved, scored_count

    def reread_material(self, material_id):
        """Re-scrapes a material, bypasses filters, follows redirects, and re-scores it."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT url, category FROM materials WHERE id = ?", (material_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return False

        url, category = row
        print(f"[*] Re-reading material ID {material_id}: {url}")
        
        # Scrape again with filters ignored and redirect following enabled
        data = self.url_scraper.scrape_url(url, ignore_filters=True)
        if not data:
            return False
        
        # Update material with new data, final URL, and reset score
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
        UPDATE materials 
        SET title = ?, url = ?, raw_content_preview = ?, score = NULL, score_details = NULL, content_summary = NULL, reasoning = NULL
        WHERE id = ?
        """, (data['title'], data['url'], data['raw_content_preview'], material_id))
        conn.commit()
        conn.close()
        
        # Immediately re-score
        print(f"[*] Re-scoring material ID {material_id}...")
        self.scorer.score_material(material_id, data['raw_content_preview'], category)
        return True

    def process_single_url(self, url, category):
        """Processes a single manually entered URL: Scrape -> Save -> Score."""
        data = self.url_scraper.scrape_url(url)
        if not data:
            return None
        
        # Save to materials
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
            INSERT OR IGNORE INTO materials (title, url, raw_content_preview, category, created_at)
            VALUES (?, ?, ?, ?, ?)
            ''', (data['title'], data['url'], data['raw_content_preview'], category, data['created_at']))
            conn.commit()
            
            # Get the newly created ID
            cursor.execute("SELECT id FROM materials WHERE url = ?", (data['url'],))
            mid = cursor.fetchone()[0]
            conn.close()
            
            # Score it
            print(f"[*] Scoring manual entry ID {mid}...")
            result = self.scorer.score_material(mid, data['raw_content_preview'], category)
            return result
        except Exception as e:
            print(f"Error processing manual URL: {e}")
            return None
