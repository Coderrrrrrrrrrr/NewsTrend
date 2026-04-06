import httpx
import re
import zlib
from bs4 import BeautifulSoup
from src.utils.logger import audit_logger
from datetime import datetime

class URLScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def compress_text(self, text):
        """Compress text using zlib."""
        if not text:
            return None
        return zlib.compress(text.encode('utf-8'))

    def decompress_text(self, compressed_data):
        """Decompress zlib compressed data."""
        if not compressed_data:
            return None
        try:
            return zlib.decompress(compressed_data).decode('utf-8')
        except Exception as e:
            print(f"Decompression error: {e}")
            return None

    def extract_biz(self, html_content):
        """Extracts the 'biz' parameter from WeChat article HTML."""
        pattern = r'var\s+biz\s*=\s*[\'"]([^\'"]+)[\'"]'
        match = re.search(pattern, html_content)
        if match:
            return match.group(1)
        return None

    def scrape_url(self, url, ignore_filters=False):
        """Scrapes a single URL and returns basic metadata and compressed content."""
        try:
            with httpx.Client(headers=self.headers, timeout=12.0, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()
                
                # V2.3: Prevent PDF binary/garbled content from entering the DB
                content_type = response.headers.get("Content-Type", "").lower()
                if "application/pdf" in content_type or response.text.startswith("%PDF"):
                    audit_logger.log_action("scraping", details=f"Blocked PDF binary: {url}", status="warning")
                    return None
                
                # Check for PDF-like markers in decoded text (garbled case)
                pdf_markers = ["obj", "stream", "xref", "trailer", "startxref"]
                if any(m in response.text[:2000] for m in pdf_markers) and "%PDF" in response.text[:500]:
                    audit_logger.log_action("scraping", details=f"Blocked garbled PDF content: {url}", status="warning")
                    return None

                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Handle Meta Refresh
                refresh = soup.find("meta", attrs={"http-equiv": "refresh"})
                if refresh and "content" in refresh.attrs:
                    content = refresh["content"]
                    if "url=" in content.lower():
                        new_url = content.lower().split("url=")[1].strip()
                        response = client.get(new_url)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.text, 'html.parser')
                
                # Handle JS Redirect
                if "url.replace" in response.text:
                    match = re.search(r"url\.replace\(['\"]([^'\"]+)['\"]\)", response.text)
                    if match:
                        new_url = match.group(1).replace("@", "")
                        response = client.get(new_url)
                        response.raise_for_status()
                        soup = BeautifulSoup(response.text, 'html.parser')

                title = soup.title.string if soup.title else "Untitled"
                biz = None
                current_url = str(response.url)

                if "mp.weixin.qq.com" in current_url:
                    wechat_title = soup.find("meta", property="og:title")
                    if wechat_title:
                        title = wechat_title.get("content", "Untitled")
                    biz = self.extract_biz(response.text)

                # Extract Full Content for Deep Cold Storage
                content_div = soup.find(id="js_content")
                if content_div:
                    full_text = content_div.get_text(separator="\n", strip=True)
                else:
                    for script in soup(["script", "style"]):
                        script.decompose()
                    full_text = soup.get_text(separator="\n", strip=True)
                
                if not ignore_filters:
                    # V2.2: Aggressive filtering for CAPTCHAs and Junk content
                    junk_keywords = ["搜狗搜索", "验证码", "Weixin", "用户您好，您的访问过于频繁", "Sogou", "VerifyCode", "请输入验证码", "机器人"]
                    if len(full_text.strip()) < 100:
                        audit_logger.log_action("scraping", details=f"Blocked short content: {title}", status="warning")
                        return None
                    if any(kw in title for kw in junk_keywords) or any(kw in full_text for kw in junk_keywords):
                        audit_logger.log_action("scraping", details=f"Blocked junk content: {title}", status="warning")
                        return None
                    if any(x in full_text for x in ["验证码", "VerifyCode", "访问过于频繁", "机器人"]):
                        return None

                preview = full_text[:800]
                full_text_zip = self.compress_text(full_text)
                
                audit_logger.log_action("scraping", details=f"Scraped URL: {url} (Compressed: {len(full_text_zip) if full_text_zip else 0} bytes)", status="success")
                
                return {
                    "title": title.strip() if title else "Untitled",
                    "url": current_url,
                    "biz": biz,
                    "raw_content_preview": preview,
                    "full_text_zip": full_text_zip,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        except Exception as e:
            audit_logger.log_action("scraping", details=f"Failed to scrape URL {url}: {e}", status="failure")
            return None

if __name__ == "__main__":
    scraper = URLScraper()
    print("URL Scraper V2.2 ready.")
