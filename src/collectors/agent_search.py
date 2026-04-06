import os
import json
import sqlite3
import random
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from src.utils.web_tools import perform_web_search
from src.collectors.url_scraper import URLScraper
from src.utils.logger import audit_logger

load_dotenv()

class AgentSearchCollector:
    """
    The 'Heavenly Eye' Active Search Agent.
    Proactively generates search queries and hunts for trending content across the web.
    """
    def __init__(self, db_path="data/news_trend.db"):
        self.db_path = db_path
        self.url_scraper = URLScraper()
        self.model = os.getenv("LLM_MODEL", "deepseek-v3-2-251201")
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

    def generate_trend_queries(self, category):
        """Generates a list of targeted search queries based on the category."""
        prompt = f"""
        你是一位顶尖的自媒体情报官，擅长发现前沿趋势。
        请针对【{category}】领域，生成 5 个目前最值得关注、最具有“谈资”或“技术突破性”的搜索关键词或短语。
        要求：
        1. 必须是中文或英文关键词。
        2. 避开大路货（如“AI 发展”），关注具体动态（如“DeepSeek v3 对比测试”、“Sora 竞品进展”）。
        3. 直接返回 JSON 数组格式，例如: ["keyword1", "keyword2", ...]
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            queries = json.loads(content)
            return queries if isinstance(queries, list) else []
        except Exception as e:
            print(f"Query generation error: {e}")
            return ["DeepSeek", "AI Agents", "Large Language Models"] if category == "AI" else ["China Economy", "Stock Market Trends"]

    def hunt_for_materials(self, category, limit_per_query=3):
        """Proactively searches and collects new materials."""
        queries = self.generate_trend_queries(category)
        print(f"[*] Heavenly Eye generated {len(queries)} queries for {category}: {queries}")
        
        all_new_items = []
        for query in queries:
            print(f"[*] Hunting for: {query}...")
            results = perform_web_search(query, count=limit_per_query)
            
            for res in results:
                # Scrape each result
                data = self.url_scraper.scrape_url(res['url'])
                if data and len(data.get('raw_content_preview', '')) > 200:
                    item = {
                        "title": data['title'],
                        "url": data['url'],
                        "raw_content_preview": data['raw_content_preview'],
                        "category": category,
                        "created_at": data['created_at']
                    }
                    all_new_items.append(item)
                    print(f"[+] Captured new material: {item['title'][:40]}...")
        
        return all_new_items

    def save_items(self, items):
        """Saves hunted items to the database, ensuring no duplicates."""
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
                print(f"Error saving hunted item: {e}")
        
        conn.commit()
        conn.close()
        return saved_count

if __name__ == "__main__":
    collector = AgentSearchCollector()
    items = collector.hunt_for_materials("AI")
    print(f"Saved {collector.save_items(items)} new items.")
