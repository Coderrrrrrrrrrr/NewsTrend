import sys
import os
sys.path.append(os.getcwd())
from src.utils.orchestrator import IntelligenceOrchestrator
import sqlite3
import zlib

def drill_test():
    orchestrator = IntelligenceOrchestrator()
    print(">>> [兵部] 启动“天眼”全球打捞实战演练...")
    
    # Run the full pipeline
    success = orchestrator.run_pipeline(category="AI")
    if not success:
        print("Pipeline failed (possibly budget exceeded)")
        return
    
    success_econ = orchestrator.run_pipeline(category="Economy")
    
    # Verification
    conn = sqlite3.connect("data/news_trend.db")
    cursor = conn.cursor()
    
    # 1. Check if new materials from Heavenly Eye were saved with compression
    cursor.execute("""
        SELECT id, title, length(full_text_zip) FROM materials 
        WHERE created_at >= date('now', 'localtime') 
        AND full_text_zip IS NOT NULL
        ORDER BY id DESC LIMIT 5
    """)
    rows = cursor.fetchall()
    print("\n>>> [验证] 深冷存储状态 (Zlib Compression):")
    for row in rows:
        print(f"ID: {row[0]}, Title: {row[1][:40]}..., ZipSize: {row[2]} bytes")
        
    # 2. Check Logical Deletion closure
    # Let's pick an item and logical delete it, then try to search its URL again
    if rows:
        test_id = rows[0][0]
        cursor.execute("SELECT url FROM materials WHERE id = ?", (test_id,))
        test_url = cursor.fetchone()[0]
        
        print(f"\n>>> [验证] 逻辑删除闭环测试 (ID: {test_id}):")
        orchestrator.logical_delete_material(test_id)
        cursor.execute("SELECT status FROM materials WHERE id = ?", (test_id,))
        status = cursor.fetchone()[0]
        print(f"Status changed to: {status}")
        
        is_dup = orchestrator._is_duplicate("Test Title", test_url)
        print(f"Duplicate check for deleted URL: {is_dup} (Expected: True)")
        
    # 3. Token Audit
    cursor.execute("""
        SELECT model_name, SUM(tokens_used) FROM audit_logs 
        WHERE date(created_at, 'localtime') = date('now', 'localtime')
        GROUP BY model_name
    """)
    audit = cursor.fetchall()
    print("\n>>> [审计] 24小时分模型 Token 消耗:")
    for a in audit:
        print(f"Model: {a[0]}, Total: {a[1]}")
        
    conn.close()

if __name__ == "__main__":
    drill_test()
