import sys
import os
sys.path.append(os.getcwd())
from src.utils.orchestrator import IntelligenceOrchestrator
import sqlite3

def score_selected():
    orchestrator = IntelligenceOrchestrator()
    ids = [152, 153]
    conn = sqlite3.connect("data/news_trend.db")
    cursor = conn.cursor()
    for mid in ids:
        cursor.execute("SELECT raw_content_preview, category FROM materials WHERE id = ?", (mid,))
        row = cursor.fetchone()
        if row:
            content, category = row
            print(f">>> [兵部] 正在评分 ID {mid}: {category}...")
            orchestrator.scorer.score_material(mid, content, category)
    conn.close()

if __name__ == "__main__":
    score_selected()
