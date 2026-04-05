import json
from datetime import datetime
from src.utils.logger import audit_logger

class WeiboCollector:
    """
    Weibo Collector using web_fetch (for better proxy/IP handling).
    """
    def __init__(self, db_path="data/news_trend.db"):
        self.db_path = db_path

    def fetch_latest_posts(self, uid):
        """Fetches the latest posts for a given Weibo UID using the PC AJAX API."""
        url = f"https://weibo.com/ajax/statuses/mymblog?uid={uid}&page=1&feature=0"
        
        try:
            from src.utils.web_tools import perform_web_fetch # Helper for web_fetch tool
            print(f"[*] Fetching Weibo via web_fetch for UID: {uid}...")
            
            # Since we can't call web_fetch tool directly from Python without agent context,
            # we rely on the agent to provide results via a cache or similar.
            # However, for the user's local execution, we should try a direct call with more headers.
            
            import httpx
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://weibo.com/u/" + uid
            }
            # Add Cookie if possible (user's environment might have one)
            # For now, we'll try a visitor cookie or similar if redirected.
            
            client = httpx.Client(headers=headers, follow_redirects=True, timeout=15.0)
            response = client.get(url)
            
            if response.status_code != 200:
                print(f"[!] Weibo API error: {response.status_code}")
                # Try m.weibo.cn as fallback
                m_url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}&containerid=107603{uid}"
                response = client.get(m_url)
                if response.status_code != 200:
                    return []
            
            data = response.json()
            posts = []
            
            # Parse PC AJAX format
            if 'data' in data and 'list' in data['data']:
                for post in data['data']['list']:
                    text = post.get('text_raw', post.get('text', ''))
                    mid = post.get('mid')
                    posts.append({
                        "title": text[:50].replace("\n", " ") + "...",
                        "url": f"https://weibo.com/{uid}/{mid}",
                        "raw_content_preview": text[:800],
                        "category": "AI",
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
            # Parse Mobile format
            elif 'data' in data and 'cards' in data['data']:
                for card in data['data']['cards']:
                    if card.get('card_type') == 9:
                        mblog = card.get('mblog', {})
                        text = mblog.get('text', '')
                        from bs4 import BeautifulSoup
                        clean_text = BeautifulSoup(text, "html.parser").get_text(separator="\n", strip=True)
                        posts.append({
                            "title": clean_text[:50].replace("\n", " ") + "...",
                            "url": card.get('scheme'),
                            "raw_content_preview": clean_text[:800],
                            "category": "AI",
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })

            return posts
        except Exception as e:
            print(f"Weibo Fetch failed for {uid}: {e}")
            return []

if __name__ == "__main__":
    collector = WeiboCollector()
    # Test with Khazix UID
    posts = collector.fetch_latest_posts("5700099573")
    for p in posts:
        print(f"Title: {p['title']}\nURL: {p['url']}\n")
