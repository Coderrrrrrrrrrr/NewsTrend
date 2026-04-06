from src.utils.orchestrator import IntelligenceOrchestrator
import sqlite3
import json
import sys

# Ensure UTF-8 output for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_v2_features():
    orch = IntelligenceOrchestrator()
    
    # 1. Test "Heavenly Eye" Active Search
    print("=== Step 1: Testing 'Heavenly Eye' (Agent Search) ===")
    category = "AI"
    collector = orch.agent_search_collector
    hunted_items = collector.hunt_for_materials(category, limit_per_query=1)
    saved = collector.save_items(hunted_items)
    print(f"[*] Heavenly Eye found {len(hunted_items)} items, saved {saved} new ones.")
    
    # 2. Test "House of Representatives" (Multi-Persona Scoring)
    print("\n=== Step 2: Testing 'House of Representatives' (Multi-Persona Scoring) ===")
    conn = sqlite3.connect("data/news_trend.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, raw_content_preview FROM materials WHERE score IS NULL ORDER BY created_at DESC LIMIT 1")
    item = cursor.fetchone()
    conn.close()
    
    if not item:
        print("[!] No unscored items found. Creating a mock high-potential item...")
        conn = sqlite3.connect("data/news_trend.db")
        cursor = conn.cursor()
        mock_content = "DeepSeek v3 is a massive breakthrough in open-source AI, achieving SOTA results on benchmarks and featuring an innovative MoE architecture. It is highly cost-effective and ready for enterprise deployment."
        cursor.execute("INSERT INTO materials (title, url, raw_content_preview, category) VALUES (?, ?, ?, ?)", 
                       ("DeepSeek v3 Breakthrough Mock", "https://example.com/mock-v3", mock_content, "AI"))
        mid = cursor.lastrowid
        title = "DeepSeek v3 Breakthrough Mock"
        content = mock_content
        conn.commit()
        conn.close()
    else:
        mid, title, content = item
    
    print(f"[*] Scoring item ID {mid}: {title}")
    result = orch.scorer.score_material(mid, content, "AI")
    
    if result and result.get('persona_audit'):
        print(f"[OK] Multi-Persona Audit triggered! Final Score: {result['score']}")
        print(f"[-] Tech Verdict: {result['persona_audit'].get('tech_critique', {}).get('score')}/5")
        print(f"[-] Visual Prompt generated: {result.get('visual_prompt', '')[:50]}...")
    else:
        score = result.get('score') if result else 'N/A'
        print(f"[!] Audit not triggered. Score: {score}")

if __name__ == "__main__":
    test_v2_features()
