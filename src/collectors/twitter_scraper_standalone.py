import os
import time
import json
import sqlite3
from datetime import datetime
from playwright.sync_api import sync_playwright
try:
    from playwright_stealth import Stealth
    def apply_stealth(page):
        stealth_config = Stealth()
        stealth_config.apply_stealth_sync(page)
except ImportError:
    # Last resort fallback if Stealth is not available
    def apply_stealth(page): pass
from src.collectors.twitter_collector import TwitterCollector
from src.utils.logger import audit_logger

class TwitterScraperStandalone:
    """
    V2.4: Standalone Twitter Scraper using Playwright Stealth.
    Operates independently of Agent Hub tools.
    """
    def __init__(self, user_data_dir=None, headless=False, cdp_url=None):
        self.user_data_dir = user_data_dir or os.getenv("CHROME_USER_DATA_DIR")
        self.headless = headless
        # V2.5.2: Force 127.0.0.1 to avoid IPv6 resolution issues on Windows
        raw_cdp = cdp_url or os.getenv("CHROME_CDP_URL")
        self.cdp_url = raw_cdp.replace("localhost", "127.0.0.1") if raw_cdp else None
        self.collector = TwitterCollector()

    def scrape_trend(self, keyword, count=10):
        """
        Navigates to X, searches for keyword, and extracts tweets.
        Supports local launch and CDP takeover.
        """
        results = []
        # Pre-flight check for CDP
        if self.cdp_url:
            import httpx
            try:
                # Check if the debugger is actually responding
                # Use http://127.0.0.1:9222/json/version as a standard test
                test_url = self.cdp_url.rstrip("/") + "/json/version"
                resp = httpx.get(test_url, timeout=10.0)
                if resp.status_code != 200:
                    raise Exception(f"CDP server at {test_url} returned {resp.status_code}")
                print(f"[*] Verified CDP endpoint: {test_url}")
            except Exception as e:
                print(f"\n[!!!] CDP CONNECTION REFUSED [!!!]")
                print(f"原因: 未能连接到 Chrome 调试端口 {self.cdp_url}。")
                print(f"解决步骤:")
                print(f" 1. 彻底关闭所有 Chrome 进程 (包括任务管理器中的后台进程)。")
                print(f" 2. 命令行运行: taskkill /F /IM chrome.exe")
                print(f" 3. 运行命令开启调试: chrome.exe --remote-debugging-port=9222")
                print(f" 4. 在浏览器访问 http://127.0.0.1:9222 查看是否显示 JSON 代码。")
                print(f"错误详情: {e}")
                return [], []

        with sync_playwright() as p:
            try:
                if self.cdp_url:
                    print(f"[*] Connecting to existing browser via CDP: {self.cdp_url}")
                    browser = p.chromium.connect_over_cdp(self.cdp_url)
                    # For CDP, we use the first context found
                    context = browser.contexts[0]
                    page = context.new_page()
                else:
                    print(f"[*] Launching browser with User Data: {self.user_data_dir}")
                    browser_context = p.chromium.launch_persistent_context(
                        user_data_dir=self.user_data_dir,
                        headless=self.headless,
                        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                    )
                    page = browser_context.new_page()
                    context = browser_context

                apply_stealth(page)
            except Exception as launch_err:
                print(f"\n[!!!] BROWSER CONNECTION FAILED [!!!]")
                print(f"原因: 极有可能是因为您的 Chrome 浏览器占用冲突或 CDP 未启动。")
                print(f"错误详情: {launch_err}")
                return [], []
            
            search_url = f"https://x.com/search?q={keyword.replace(' ', '%20')}&f=live"
            print(f"[*] Navigating to: {search_url}")
            
            try:
                page.goto(search_url, wait_until="networkidle", timeout=60000)
                time.sleep(5) # Allow dynamic content to load
                
                # Scroll down to trigger more tweets
                page.evaluate("window.scrollBy(0, 1000)")
                time.sleep(2)
                
                # Locate tweet articles
                tweets = page.query_selector_all('article[data-testid="tweet"]')
                print(f"[*] Found {len(tweets)} tweet elements on page.")
                
                anchors = []
                alpha_list = ["@sama", "@elonmusk", "@karpathy", "@tobi", "@ylecun", "@itsolelehmann"]
                
                for tweet in tweets[:count]:
                    try:
                        text_element = tweet.query_selector('div[data-testid="tweetText"]')
                        if text_element:
                            text = text_element.inner_text()
                            # Basic anchor detection
                            found_anchors = [a for a in alpha_list if a.lower() in text.lower()]
                            anchors.extend(found_anchors)
                            
                            results.append({
                                "id": str(int(time.time() * 1000)), # Simplified ID
                                "text": text,
                                "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                            })
                    except:
                        continue
                
                unique_anchors = list(set(anchors))
                return results, unique_anchors
                
            except Exception as e:
                print(f"[!] Scrape Error: {e}")
                return [], []
                if self.cdp_url:
                    browser.close() # Only closes the connection/page, not the real browser
                else:
                    browser_context.close()

if __name__ == "__main__":
    # Test run
    scraper = TwitterScraperStandalone()
    tweets, anchors = scraper.scrape_trend("AI Agents", count=5)
    print(f"Captured {len(tweets)} tweets with anchors: {anchors}")
