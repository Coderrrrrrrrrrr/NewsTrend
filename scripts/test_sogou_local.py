import httpx
from bs4 import BeautifulSoup
import sys

def test_sogou(account_name):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://weixin.sogou.com/"
    }
    url = f"https://weixin.sogou.com/weixin?type=1&query={account_name}&ie=utf8&s_from=input&_sug_=n&_sug_type_="
    
    try:
        response = httpx.get(url, headers=headers, timeout=15.0)
        if "用户您好，您的访问过于频繁" in response.text:
            print("ERROR: Sogou CAPTCHA")
            return
            
        soup = BeautifulSoup(response.text, 'html.parser')
        account_li = soup.select_one("ul.news-list2 > li")
        if account_li:
            print(f"FOUND: {account_name}")
            links = account_li.select("dl dd a")
            for a in links:
                print(f"ARTICLE: {a.get_text(strip=True)} | URL: {a.get('href')}")
        else:
            print(f"NOT_FOUND: {account_name}")
            # Try type=2
            url2 = f"https://weixin.sogou.com/weixin?type=2&query={account_name}&ie=utf8"
            response2 = httpx.get(url2, headers=headers, timeout=15.0)
            soup2 = BeautifulSoup(response2.text, 'html.parser')
            # Extract articles from type=2
            # news-box -> li -> .txt-box -> h3 -> a
            article_links = soup2.select(".news-box li h3 a")
            for a in article_links[:5]:
                print(f"ARTICLE_SEARCH: {a.get_text(strip=True)} | URL: {a.get('href')}")
                
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == '__main__':
    test_sogou(sys.argv[1])
