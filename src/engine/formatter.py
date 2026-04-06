import os
import sqlite3
import json
import httpx
from openai import OpenAI
from src.engine.prompts import OMNIFORMAT_PROMPT, PLATFORM_CONSTRAINTS, AI_GEEK_STYLE, ECONOMY_HISTORICAL_STYLE
from dotenv import load_dotenv
from src.utils.logger import audit_logger

load_dotenv()

class OmniFormatter:
    def __init__(self, db_path="data/news_trend.db"):
        self.db_path = db_path
        self.model = os.getenv("LLM_MODEL", "deepseek-v3-2-251201")
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        self.webhook_url = os.getenv("DISTRIBUTION_WEBHOOK", "")

    def generate_draft(self, material_id, platform):
        """Generates a cross-platform draft based on material scoring and summary."""
        # ... existing selection logic ...
        try:
            print(f"[*] Generating {platform} draft for material {material_id}...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位顶尖的自媒体运营官，擅长创作多平台爆款内容。"},
                    {"role": "user", "content": prompt}
                ]
            )
            draft_content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            # Save to drafts table
            self._save_draft(material_id, platform, draft_content, tokens_used)
            
            audit_logger.log_action(
                "publishing", 
                target_id=material_id, 
                details=f"Generated {platform} draft", 
                status="success",
                tokens_used=tokens_used,
                model_name=self.model
            )
            return draft_content, tokens_used
        except Exception as e:
            # ...
            return None, 0

    def create_omni_draft(self, material_id, target_platforms=None):
        """V2.2+: Generates drafts for multiple target platforms at once.
        Includes a safeguard: if cumulative tokens for one material exceed 20k, 
        it stops generating for remaining platforms (Degraded Mode).
        """
        platforms = target_platforms or ['X', 'LinkedIn', 'Substack', 'WeChat']
        results = {}
        cumulative_tokens = 0
        TOKEN_THRESHOLD = 20000 # 20k tokens per material safeguard (Hubu Rule)

        for p in platforms:
            if cumulative_tokens > TOKEN_THRESHOLD:
                print(f"[!] Token threshold ({TOKEN_THRESHOLD}) reached for material {material_id}. Skipping platform: {p}")
                audit_logger.log_action(
                    "publishing", 
                    target_id=material_id, 
                    details=f"Degraded Mode: Skipped {p} due to token threshold.", 
                    status="warning"
                )
                break
                
            draft, tokens = self.generate_draft(material_id, p)
            if draft:
                results[p] = draft
                cumulative_tokens += tokens
        return results

    def push_to_webhook(self, draft_id):
        """Pushes a draft to an external webhook."""
        if not self.webhook_url:
            print("[!] DISTRIBUTION_WEBHOOK not configured.")
            return False, "Webhook URL not configured."

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.platform, d.content, m.title, m.url 
            FROM drafts d 
            JOIN materials m ON d.material_id = m.id 
            WHERE d.id = ?
        """, (draft_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return False, "Draft not found."

        platform, content, title, original_url = row
        payload = {
            "platform": platform,
            "title": title,
            "content": content,
            "original_url": original_url,
            "timestamp": datetime.now().isoformat()
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(self.webhook_url, json=payload)
                response.raise_for_status()
                
                # Update status in DB
                conn = sqlite3.connect(self.db_path)
                conn.execute("UPDATE drafts SET status = 'published', published_at = CURRENT_TIMESTAMP WHERE id = ?", (draft_id,))
                conn.commit()
                conn.close()
                
                audit_logger.log_action("publishing", details=f"Pushed draft {draft_id} to webhook", status="success")
                return True, "Successfully pushed to webhook."
        except Exception as e:
            audit_logger.log_action("publishing", details=f"Webhook push failed for draft {draft_id}: {e}", status="failure")
            return False, str(e)

    def push_to_github(self, draft_id, repo_path="content/posts"):
        """V2.2: Placeholder for GitHub Pages integration (via GitHub API)."""
        # This would require GITHUB_TOKEN and repository info
        # For now, we simulate the success if tokens are not configured
        print(f"[*] Simulating GitHub Push for draft {draft_id} to {repo_path}...")
        return True, "GitHub Push simulated (requires GITHUB_TOKEN for real action)."

    def _save_draft(self, material_id, platform, content, tokens_used=0):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO drafts (material_id, platform, content, tokens_used, status)
        VALUES (?, ?, ?, ?, 'pending')
        ''', (material_id, platform, content, tokens_used))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    from datetime import datetime
    formatter = OmniFormatter()
    print("OmniFormatter V2.2+ ready.")
