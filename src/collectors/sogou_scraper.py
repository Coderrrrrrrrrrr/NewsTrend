import httpx
from bs4 import BeautifulSoup
from datetime import datetime
from src.utils.logger import audit_logger
from src.collectors.url_scraper import URLScraper

class SogouWeChatScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://weixin.sogou.com/"
        }
        self.scraper = URLScraper()

    def fetch_latest_articles(self, account_name):
        """Searches Sogou for the latest articles. Tries Type 1 then Type 2."""
        articles = self._fetch_from_sogou(account_name, search_type=1)
        if not articles:
            print(f"[*] Sogou Type 1 failed, trying Type 2 for {account_name}...")
            articles = self._fetch_from_sogou(account_name, search_type=2)
        return articles

    def _fetch_from_sogou(self, account_name, search_type=1):
        """Internal method for Sogou search."""
        search_url = f"https://weixin.sogou.com/weixin?type={search_type}&query={account_name}&ie=utf8"
        try:
            print(f"[*] Searching Sogou (Type {search_type}) for {account_name}...")
            response = httpx.get(search_url, headers=self.headers, timeout=15.0, follow_redirects=True)
            if "用户您好，您的访问过于频繁" in response.text:
                print(f"[!] Sogou CAPTCHA for {account_name}.")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')
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
                
                # Scrape content and biz
                scraped_data = self.scraper.scrape_url(href)
                if scraped_data:
                    biz = scraped_data.get('biz')
                    if biz:
                         audit_logger.log_action("scraping", details=f"BIZ found for {account_name}: {biz}", status="info")
                    
                    results.append({
                        "title": scraped_data['title'],
                        "url": scraped_data['url'],
                        "raw_content_preview": scraped_data['raw_content_preview'],
                        "category": "AI",
                        "created_at": scraped_data['created_at']
                    })
                else:
                    # Fallback
                    results.append({
                        "title": title,
                        "url": href,
                        "raw_content_preview": f"Content not fetched. Title: {title}",
                        "category": "AI",
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
            return results
        except Exception as e:
            print(f"Sogou Search (Type {search_type}) failed: {e}")
            return []
