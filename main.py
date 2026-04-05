import time
import os
from dotenv import load_dotenv
from src.utils.orchestrator import IntelligenceOrchestrator

load_dotenv()

def run_background_task():
    print(f"[{datetime.now()}] >>> 玄境自动化引擎启动 (DeepSeek-V3 Engine)...")
    orchestrator = IntelligenceOrchestrator()
    
    print(f"[{datetime.now()}] [Node 1] 正在检查令牌预算 (Hubu Audit)...")
    if not orchestrator.check_token_budget():
        print(f"[{datetime.now()}] [!] 令牌预算不足，本次任务自动挂起。")
        return

    print(f"[{datetime.now()}] [Node 2] 正在抓取活跃情报源 (Collecting)...")
    # 1. 抓取所有激活的情报源并评分
    saved, scored = orchestrator.crawl_all_active()
    
    print(f"[{datetime.now()}] [Node 3] 任务总结 (Summary):")
    print(f"   - 本次新增素材: {saved}")
    print(f"   - 本次完成 AI 评分: {scored}")
    print(f"[{datetime.now()}] <<< 玄境引擎运行结束。")
    print("[*] 请在 Streamlit Dashboard ('streamlit run app.py') 中审阅素材。")

if __name__ == "__main__":
    run_background_task()
