import time
import random
import httpx
from src.utils.logger import audit_logger

class SafeFetcher:
    """
    Utility to perform web requests with rate limiting and random delays 
    to minimize risk of IP blocking or 'account blocking' signals.
    """
    def __init__(self, min_delay=2.0, max_delay=5.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/115.0"
        ]

    def _wait_if_needed(self):
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        target_delay = random.uniform(self.min_delay, self.max_delay)
        
        if elapsed < target_delay:
            wait_time = target_delay - elapsed
            time.sleep(wait_time)
        
        self.last_request_time = time.time()

    def fetch(self, url, headers=None):
        """Perform a safe GET request with randomized headers and timing."""
        self._wait_if_needed()
        
        default_headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.google.com/"
        }
        
        if headers:
            default_headers.update(headers)
            
        try:
            with httpx.Client(follow_redirects=True, timeout=15.0) as client:
                response = client.get(url, headers=default_headers)
                response.raise_for_status()
                return response
        except Exception as e:
            audit_logger.log_action("network", details=f"Fetch failed for {url}: {e}", status="failure")
            raise e

# Shared fetcher instance
safe_fetcher = SafeFetcher()
