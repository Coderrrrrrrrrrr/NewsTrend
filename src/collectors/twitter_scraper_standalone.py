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
    def __init__(self, user_data_dir=None, headless=False):
        # V2.5.6: Use a dedicated local profile within the project to avoid conflicts with system Chrome
        project_root = os.getcwd()
        default_profile = os.path.join(project_root, "data", "chrome_profile")
        if not os.path.exists(default_profile):
            os.makedirs(default_profile, exist_ok=True)
            
        self.user_data_dir = user_data_dir or default_profile
        self.headless = headless
        self.collector = TwitterCollector()

    def scrape_trend(self, keyword, count=10):
        """
        Navigates to X, searches for keyword, and extracts tweets.
        Uses a project-local persistent context to avoid conflicts.
        """
        results = []
        with sync_playwright() as p:
            print(f"[*] Launching browser with Profile: {self.user_data_dir}")
            try:
                browser_context = p.chromium.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=self.headless,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                )
                page = browser_context.new_page()
                apply_stealth(page)
            except Exception as launch_err:
                print(f"\n[!!!] BROWSER LAUNCH FAILED [!!!]")
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
            finally:
                try:
                    browser_context.close()
                except:
                    pass

if __name__ == "__main__":
    # Test run
    scraper = TwitterScraperStandalone()
    tweets, anchors = scraper.scrape_trend("AI Agents", count=5)
    print(f"Captured {len(tweets)} tweets with anchors: {anchors}")
