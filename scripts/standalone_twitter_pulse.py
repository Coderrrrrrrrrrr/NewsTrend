import os
import sys
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())

from src.collectors.twitter_scraper_standalone import TwitterScraperStandalone
from src.collectors.twitter_collector import TwitterCollector
from src.utils.orchestrator import IntelligenceOrchestrator
from src.utils.logger import audit_logger

load_dotenv()

def run_pulse_sampling_standalone(keywords=None, headless=True, use_cdp=False):
    """
    V2.5: Standalone X Intelligence Pulse Sampling.
    Supports CDP takeover.
    """
    audit_logger.log_action("scraping", details=f"Starting Standalone X Pulse Sampling (CDP={use_cdp})...", status="info")
    
    if not keywords:
        keywords = [
            "AI Agents autonomous 2026",
            "Superintelligence Sam Altman",
            "2026 Tech Job Market Rebound",
            "NVIDIA Blackwell chips AI training",
            "DeepSeek-V3 vs OpenAI o1"
        ]
    
    user_data_dir = os.getenv("CHROME_USER_DATA_DIR")
    cdp_url = os.getenv("CHROME_CDP_URL") if use_cdp else None
    
    if not use_cdp and not user_data_dir:
        print("[!] ERROR: CHROME_USER_DATA_DIR not set in .env. Please configure path to your Chrome profile.")
        return
        
    scraper = TwitterScraperStandalone(user_data_dir, headless=headless, cdp_url=cdp_url)
    collector = TwitterCollector()
    orchestrator = IntelligenceOrchestrator()
    
    total_new = 0
    for kw in keywords:
        print(f"[*] Pulse Sampling Trend: {kw}")
        try:
            tweets, anchors = scraper.scrape_trend(kw, count=10)
            if tweets:
                saved = collector.save_intelligence(kw, tweets, anchors, category="AI")
                total_new += saved
                print(f"    [+] Saved {saved} new intelligence pack for {kw}")
            else:
                print(f"    [-] No depth tweets found for {kw}. Skipping.")
        except Exception as e:
            print(f"    [!] Error scraping {kw}: {e}")
            continue
        
        # Jitter wait to avoid detection
        time.sleep(15)
        
    if total_new > 0:
        print(f"[*] Pulse Sampling Complete. Total New Items: {total_new}. Starting Scoring...")
        scored = orchestrator.run_scoring()
        print(f"[*] AI Scoring complete. Items scored: {scored}")
        audit_logger.log_action("scraping", details=f"Standalone X Pulse: {total_new} items found, {scored} scored.", status="success")
    else:
        print("[*] No new trends found in this pulse.")
        audit_logger.log_action("scraping", details="Standalone X Pulse complete: No new items.", status="info")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Standalone Twitter Pulse")
    parser.add_argument("--keywords", type=str, help="Comma separated keywords")
    parser.add_argument("--show-ui", action="store_true", help="Show browser UI (non-headless)")
    parser.add_argument("--use-cdp", action="store_true", help="Connect to existing browser via CDP")
    args = parser.parse_args()
    
    kws = None
    if args.keywords:
        kws = [k.strip() for k in args.keywords.split(",")]
        
    run_pulse_sampling_standalone(keywords=kws, headless=not args.show_ui, use_cdp=args.use_cdp)
