import sys
import os
sys.path.append(os.getcwd())
from src.utils.orchestrator import IntelligenceOrchestrator
import sqlite3

def check_dup():
    orchestrator = IntelligenceOrchestrator()
    conn = sqlite3.connect("data/news_trend.db")
    cursor = conn.cursor()
    cursor.execute("SELECT url FROM materials WHERE id = 153;")
    url = cursor.fetchone()[0]
    conn.close()
    
    is_dup = orchestrator._is_duplicate("Some Title", url)
    print(f">>> [结果] URL {url} 的重复校验结果: {is_dup} (期待: True)")

if __name__ == "__main__":
    check_dup()
