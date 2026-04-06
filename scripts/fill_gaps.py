import sys
import os
sys.path.append(os.getcwd())
from src.utils.orchestrator import IntelligenceOrchestrator

def fill_gaps():
    orchestrator = IntelligenceOrchestrator()
    ids = [128, 27, 83, 73, 130]
    for mid in ids:
        print(f">>> [兵部] 补全 ID {mid} 的矩阵草稿...")
        orchestrator.formatter.create_omni_draft(mid)

if __name__ == "__main__":
    fill_gaps()
