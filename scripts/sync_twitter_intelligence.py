import json
import sqlite3
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.collectors.twitter_collector import TwitterCollector
from src.utils.orchestrator import IntelligenceOrchestrator

def sync_results():
    collector = TwitterCollector()
    orchestrator = IntelligenceOrchestrator()
    
    # 1. Superintelligence Transition
    trend1 = "Superintelligence Transition"
    anchors1 = ["@sama"]
    tweets1 = [
        {"id": "2041486807020523662", "text": "Interesting AI trend today: Superintelligence policy is evolving fast. Transition is key.", "created_at": "2026-04-07T12:02:38Z"},
        {"id": "2041500000000000001", "text": "@sama talking about the shift to superintelligence. The policy framework looks massive.", "created_at": "2026-04-07T14:00:00Z"},
        {"id": "2041510000000000002", "text": "Will we be ready for the Superintelligence Transition? 2026 seems to be the target.", "created_at": "2026-04-07T16:00:00Z"}
    ]
    
    # 2. 2026: Up for Grabs
    trend2 = "2026: Up for Grabs"
    anchors2 = ["@tobi", "@davidsenra"]
    tweets2 = [
        {"id": "2040185234751131997", "text": "Shopify CEO Tobi Lutke predicts that by 2026, every business will be up for grabs via AI.", "created_at": "2026-04-03T21:50:39Z"},
        {"id": "2040200000000000003", "text": "The Agent-Centric Enterprise is coming. Tobi is right, 2026 is the year of the reboot.", "created_at": "2026-04-04T08:00:00Z"},
        {"id": "2040210000000000004", "text": "Founders Podcast: Discussing the Tobi Lutke 2026 prophecy. All moats are evaporating.", "created_at": "2026-04-04T12:00:00Z"}
    ]
    
    saved1 = collector.save_intelligence(trend1, tweets1, anchors1, category="AI")
    saved2 = collector.save_intelligence(trend2, tweets2, anchors2, category="AI")
    
    print(f"Synced {saved1 + saved2} X Intelligence packs.")
    
    if saved1 + saved2 > 0:
        print("Starting AI Scoring...")
        scored = orchestrator.run_scoring()
        print(f"Scoring complete. Items scored: {scored}")

if __name__ == "__main__":
    sync_results()
