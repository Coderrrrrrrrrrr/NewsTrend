import requests
import re
import random
import sys
from urllib3.exceptions import InsecureRequestWarning

# 禁用 SSL 警告
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

def fetch_and_extract_biz(url):
    try:
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.encoding = 'utf-8'
        
        # Check for CAPTCHA/Error
        if "环境异常" in response.text:
            print("ERROR: Environment Anomaly (Blocked)")
            return None

        pattern = r'var\s+biz\s*=\s*[\'"]([^\'"]+)[\'"]'
        match = re.search(pattern, response.text)
        if match:
            return match.group(1)
        return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None

if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else 'https://mp.weixin.qq.com/s/vIWtXMH5b_A5g3FaxUsFHg'
    biz = fetch_and_extract_biz(url)
    if biz:
        print(f"BIZ: {biz}")
    else:
        print("BIZ: Not found")
