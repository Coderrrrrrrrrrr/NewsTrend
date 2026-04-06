import httpx
import re
import asyncio
import os
from bs4 import BeautifulSoup
from datetime import datetime
from src.utils.logger import audit_logger
from src.collectors.url_scraper import URLScraper
from src.utils.browser_helper import BrowserHelper

class SogouWeChatScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://weixin.sogou.com/"
        }
        self.scraper = URLScraper()
        self.browser_helper = BrowserHelper()

    def fetch_latest_articles(self, account_name):
        """Searches Sogou for the latest articles using three layers of defense."""
        # Layer 1 & 2: Try Sogou with Stealth Cookie Injection
        articles = self._fetch_from_sogou(account_name, search_type=1)
        if not articles:
            articles = self._fetch_from_sogou(account_name, search_type=2)
        
        # Layer 3: DuckDuckGo Fallback
        if not articles:
            print(f"[*] Sogou failed for {account_name}, triggering DDG Fallback...")
            articles = self._fetch_from_ddg(account_name)
            
        return articles

    def _get_injected_cookies(self):
        """Extract cookies from persistent browser profile."""
        # In a real scenario, we might read the cookies file or launch a quick headless browser to grab them
        # For now, we rely on the fact that BrowserHelper uses the persistent profile.
        # If we need to inject them into httpx, we can use BrowserHelper.fetch_page_with_stealth first.
        pass

    def _fetch_from_sogou(self, account_name, search_type=1):
        """Internal method for Sogou search with cookie injection logic."""
        search_url = f"https://weixin.sogou.com/weixin?type={search_type}&query={account_name}&ie=utf8"
        try:
            print(f"[*] Searching Sogou (Type {search_type}) for {account_name}...")
            
            # Use BrowserHelper for the search page to handle CAPTCHA and get tokens
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            html_content, cookies = loop.run_until_complete(
                self.browser_helper.fetch_page_with_stealth(search_url)
            )
            loop.close()

            if not html_content or "用户您好，您的访问过于频繁" in html_content:
                print(f"[!] Sogou CAPTCHA detected for {account_name}.")
                return []

            soup = BeautifulSoup(html_content, 'html.parser')
            article_links = []
            
            if search_type == 1:
                account_li = soup.select_one("ul.news-list2 > li")
                if account_li:
                    article_links = account_li.select("dl dd a")
            else:
                article_links = soup.select(".news-box li h3 a")

            results = []
            for a in article_links[:8]:
                title = a.get_text(strip=True)
                href = a.get("href")
                if href and not href.startswith("http"):
                    href = "https://weixin.sogou.com" + href
                
                # Scrape content and compress
                scraped_data = self.scraper.scrape_url(href)
                if scraped_data:
                    results.append({
                        "title": scraped_data['title'],
                        "url": scraped_data['url'],
                        "raw_content_preview": scraped_data['raw_content_preview'],
                        "full_text_zip": scraped_data.get('full_text_zip'),
                        "category": "AI",
                        "created_at": scraped_data['created_at']
                    })
            return results
        except Exception as e:
            print(f"Sogou Search (Type {search_type}) failed: {e}")
            return []

    def _fetch_from_ddg(self, account_name):
        """Layer 3: Search DuckDuckGo for site:mp.weixin.qq.com {account_name}"""
        query = f"site:mp.weixin.qq.com {account_name}"
        search_url = f"https://duckduckgo.com/html/?q={query}"
        try:
            # DDG HTML version is easier to scrape without JS
            response = httpx.get(search_url, headers=self.headers, timeout=15.0)
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.select(".result__a")
            
            results = []
            for a in links[:5]:
                title = a.get_text(strip=True)
                href = a.get("href")
                
                if "mp.weixin.qq.com" in href:
                    scraped_data = self.scraper.scrape_url(href)
                    if scraped_data:
                        results.append({
                            "title": scraped_data['title'],
                            "url": scraped_data['url'],
                            "raw_content_preview": scraped_data['raw_content_preview'],
                            "full_text_zip": scraped_data.get('full_text_zip'),
                            "category": "AI",
                            "created_at": scraped_data['created_at']
                        })
            return results
        except Exception as e:
            print(f"DDG Fallback failed: {e}")
            return []

if __name__ == "__main__":
    scraper = SogouWeChatScraper()
    print("Sogou Scraper V2.2 Ready.")
