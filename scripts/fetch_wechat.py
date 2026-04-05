import httpx
from bs4 import BeautifulSoup
import sys
import json
import random
import time
from datetime import datetime

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
]

def fetch_wechat_articles(account_name):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": "https://weixin.sogou.com/"
    }
    articles = []
    
    # Try Type 1 (Accounts)
    try:
        url = f"https://weixin.sogou.com/weixin?type=1&query={account_name}&ie=utf8"
        response = httpx.get(url, headers=headers, timeout=15.0)
        if "用户您好，您的访问过于频繁" in response.text:
             # If blocked, try Type 2 immediately or fail
             pass
        else:
            soup = BeautifulSoup(response.text, 'html.parser')
            account_li = soup.select_one("ul.news-list2 > li")
            if account_li:
                links = account_li.select("dl dd a")
                for a in links:
                    articles.append({"title": a.get_text(strip=True), "url": a.get("href")})
    except Exception as e:
        sys.stderr.write(f"Type 1 Search Error: {e}\n")

    # Try Type 2 (Articles) if not enough
    if len(articles) < 5:
        try:
            url2 = f"https://weixin.sogou.com/weixin?type=2&query={account_name}&ie=utf8"
            response2 = httpx.get(url2, headers=headers, timeout=15.0)
            if "用户您好，您的访问过于频繁" not in response2.text:
                soup2 = BeautifulSoup(response2.text, 'html.parser')
                article_links = soup2.select(".news-box li h3 a")
                for a in article_links:
                    title = a.get_text(strip=True)
                    href = a.get("href")
                    if any(art['title'] == title for art in articles): continue
                    articles.append({"title": title, "url": href})
        except Exception as e:
             sys.stderr.write(f"Type 2 Search Error: {e}\n")

    # Process and Follow Redirects
    final_articles = []
    client = httpx.Client(headers=headers, follow_redirects=True, timeout=10.0)
    
    for art in articles[:8]: # limit to top 8
        href = art['url']
        if href.startswith("/"):
            href = "https://weixin.sogou.com" + href
        
        try:
            # First hit the Sogou link to get the real WeChat URL
            res = client.get(href)
            # Sogou redirect links often lead to a JS redirect or a real redirect
            real_url = str(res.url)
            
            # If still on Sogou, try extracting from JS if present
            if "weixin.sogou.com" in real_url and "url.replace" in res.text:
                 import re
                 match = re.search(r"url\.replace\(['\"]([^'\"]+)['\"]\)", res.text)
                 if match:
                      real_url = match.group(1).replace("@", "") # Sogou JS trick
            
            if "mp.weixin.qq.com" in real_url:
                # Scrape Content Preview
                res_art = client.get(real_url)
                soup_art = BeautifulSoup(res_art.text, 'html.parser')
                
                # Content
                content_div = soup_art.find(id="js_content")
                if content_div:
                    preview = content_div.get_text(separator="\n", strip=True)[:800]
                else:
                    preview = f"Content not fetched (js_content missing). URL: {real_url}"
                
                final_articles.append({
                    "title": art['title'],
                    "url": real_url,
                    "raw_content_preview": preview,
                    "category": "AI", # default
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                time.sleep(random.uniform(0.5, 1.5)) # anti-ban
        except Exception as e:
            sys.stderr.write(f"Error processing link {href}: {e}\n")

    return final_articles

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(1)
    results = fetch_wechat_articles(sys.argv[1])
    print(json.dumps(results, ensure_ascii=False))
