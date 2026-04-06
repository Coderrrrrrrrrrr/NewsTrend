import httpx
import json
import os
import random
import time
from bs4 import BeautifulSoup
from src.utils.logger import audit_logger

def perform_web_search(query, count=10):
    """
    Performs a web search via DuckDuckGo (HTML version) to avoid extra API costs.
    This is the 'Heavenly Eye' active search logic.
    """
    url = f"https://html.duckduckgo.com/html/?q={query}"
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    ]
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://duckduckgo.com/"
    }
    
    results = []
    try:
        # Respectful delay
        time.sleep(random.uniform(1.0, 3.0))
        
        with httpx.Client(follow_redirects=True, timeout=15.0) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # DuckDuckGo HTML parsing
            search_items = soup.find_all('div', class_='result')
            for item in search_items[:count]:
                link_tag = item.find('a', class_='result__a')
                snippet_tag = item.find('a', class_='result__snippet')
                
                if link_tag:
                    title = link_tag.get_text(strip=True)
                    link = link_tag.get('href')
                    # DuckDuckGo links are often prefixed with /l/?kh=-1&uddg=...
                    if link.startswith('/l/'):
                        # Extract the actual URL from uddg param
                        try:
                            from urllib.parse import urlparse, parse_qs
                            link = parse_qs(urlparse(link).query).get('uddg', [link])[0]
                        except:
                            pass
                    
                    snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
                    results.append({
                        "title": title,
                        "url": link,
                        "snippet": snippet
                    })
        
        audit_logger.log_action("search", details=f"Found {len(results)} results for: {query}", status="success")
        return results
    except Exception as e:
        audit_logger.log_action("search", details=f"Search failed for {query}: {e}", status="failure")
        print(f"Web search error: {e}")
        return []

if __name__ == "__main__":
    print(perform_web_search("DeepSeek v3 benchmarks"))
