import sys
import os
sys.path.append(os.getcwd())
from src.utils.orchestrator import IntelligenceOrchestrator
import sqlite3
from datetime import datetime

def mass_dist_drill():
    orchestrator = IntelligenceOrchestrator()
    print(">>> [兵部] 启动 Task #25 大规模分发实战测试...")
    
    # 1. Selection & Drafting
    # run_pipeline will now select Top 5 (Score >= 3.8) and generate drafts
    success = orchestrator.run_pipeline(category="AI")
    success_econ = orchestrator.run_pipeline(category="Economy")
    
    # 2. Results Verification
    conn = sqlite3.connect("data/news_trend.db")
    cursor = conn.cursor()
    
    # Check drafts generated today
    cursor.execute("""
        SELECT d.id, m.title, d.platform, d.tokens_used 
        FROM drafts d 
        JOIN materials m ON d.material_id = m.id 
        WHERE date(d.created_at, 'localtime') = date('now', 'localtime')
        ORDER BY d.id DESC LIMIT 10
    """)
    rows = cursor.fetchall()
    
    print("\n>>> [结果] 今日分发草稿产出 (Top 10):")
    for row in rows:
        print(f"DraftID: {row[0]}, Platform: {row[2]}, Tokens: {row[3]}, Title: {row[1][:40]}...")
    
    # 3. Token Sync to Hubu (Audit)
    cursor.execute("""
        SELECT model_name, SUM(tokens_used) 
        FROM (
            SELECT model_name, tokens_used FROM audit_logs WHERE date(created_at, 'localtime') = date('now', 'localtime')
            UNION ALL
            SELECT 'deepseek-v3' as model_name, tokens_used FROM drafts WHERE date(created_at, 'localtime') = date('now', 'localtime')
        )
        GROUP BY model_name
    """)
    token_audit = cursor.fetchall()
    print("\n>>> [财务同步] 今日累计 Token 消耗 (供户部审计):")
    for a in token_audit:
        print(f"Model: {a[0] or 'System/Other'}, Total: {a[1]}")
        
    conn.close()

if __name__ == "__main__":
    mass_dist_drill()
