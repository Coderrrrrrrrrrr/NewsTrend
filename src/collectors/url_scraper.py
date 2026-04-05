import httpx
import re
from bs4 import BeautifulSoup
from src.utils.logger import audit_logger
from datetime import datetime

class URLScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def extract_biz(self, html_content):
        """Extracts the 'biz' parameter from WeChat article HTML."""
        pattern = r'var\s+biz\s*=\s*[\'"]([^\'"]+)[\'"]'
        match = re.search(pattern, html_content)
        if match:
            return match.group(1)
        return None

    def scrape_url(self, url, ignore_filters=False):
        """Scrapes a single URL and returns basic metadata and content preview."""
        try:
            # We use a persistent client to handle cookies if needed for redirects
            with httpx.Client(headers=self.headers, timeout=12.0, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()
                
                # Logic to handle Meta Refresh or JS-based Redirects (Common in Sogou/WeChat)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 1. Check for Meta Refresh
                refresh = soup.find("meta", attrs={"http-equiv": "refresh"})
                if refresh and "content" in refresh.attrs:
                    content = refresh["content"]
                    if "url=" in content.lower():
                        new_url = content.lower().split("url=")[1].strip()
                        print(f"[*] Following Meta Refresh: {new_url}")
                        response = client.get(new_url)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.text, 'html.parser')
                
                # 2. Check for Sogou/WeChat JS Redirect "url.replace"
                if "url.replace" in response.text:
                    match = re.search(r"url\.replace\(['\"]([^'\"]+)['\"]\)", response.text)
                    if match:
                        new_url = match.group(1).replace("@", "")
                        print(f"[*] Following JS Redirect: {new_url}")
                        response = client.get(new_url)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.text, 'html.parser')

                # Title extraction
                title = soup.title.string if soup.title else "Untitled"
                biz = None
                
                # Check if we are now on a real WeChat page
                current_url = str(response.url)
                if "mp.weixin.qq.com" in current_url:
                    # WeChat specific title
                    wechat_title = soup.find("meta", property="og:title")
                    if wechat_title:
                        title = wechat_title.get("content", "Untitled")
                    
                    # Extract biz
                    biz = self.extract_biz(response.text)

                # Content extraction (Burn After Reading: only 500 chars)
                # For WeChat, main content is in id="js_content"
                content_div = soup.find(id="js_content")
                if content_div:
                    text = content_div.get_text(separator="\n", strip=True)
                else:
                    # Generic fallback
                    for script in soup(["script", "style"]):
                        script.decompose()
                    text = soup.get_text(separator="\n", strip=True)
                
                if not ignore_filters:
                    # Filtering: If content is too short or looks like a placeholder
                    if len(text.strip()) < 50:
                        print(f"[!] Warning: Scraped content too short ({len(text.strip())} chars) for {url}. Might be a blank page or CAPTCHA.")
                        return None
                    
                    # Additional check: If title is "搜狗搜索" or similar error pages
                    if "搜狗搜索" in title or "验证码" in title or "Weixin" == title:
                        print(f"[!] Warning: Detected error/placeholder page title: {title}")
                        return None

                preview = text[:800] # Slightly more for manual input to ensure AI has context
                
                audit_logger.log_action("scraping", details=f"Scraped URL: {url} (Final: {current_url})", status="success")
                
                return {
                    "title": title.strip(),
                    "url": current_url, # Return the final URL
                    "biz": biz,
                    "raw_content_preview": preview,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        except Exception as e:
            audit_logger.log_action("scraping", details=f"Failed to scrape URL {url}: {e}", status="failure")
            return None

if __name__ == "__main__":
    scraper = URLScraper()
    print("URL Scraper ready.")
