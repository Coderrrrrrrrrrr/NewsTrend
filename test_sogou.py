from src.collectors.sogou_scraper import SogouWeChatScraper

scraper = SogouWeChatScraper()
account = "数字生命卡兹克"
results = scraper.fetch_latest_articles(account)

print(f"Results for {account}:")
if results:
    for item in results:
        print(f"Title: {item['title']}")
        print(f"URL: {item['url']}")
else:
    print("No results or CAPTCHA.")
