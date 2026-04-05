import os
import sqlite3
import json
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

    def generate_draft(self, material_id, platform):
        """Generates a cross-platform draft based on material scoring and summary."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT content_summary, score_details, category FROM materials WHERE id = ?", (material_id,))
        row = cursor.fetchone()
        conn.close()

        if not row or not row[0]:
            print(f"[!] No summary found for material {material_id}. Cannot generate draft.")
            return None

        summary, score_details_json, category = row
        score_details = json.loads(score_details_json) if score_details_json else {}
        plus_points = ", ".join(score_details.get("plus_points", []))
        
        style_guide = AI_GEEK_STYLE if category == 'AI' else ECONOMY_HISTORICAL_STYLE
        platform_constraint = PLATFORM_CONSTRAINTS.get(platform, "简洁大方，内容充实。")
        full_style_guide = f"{style_guide}\n平台特性：{platform_constraint}"

        prompt = OMNIFORMAT_PROMPT.format(
            platform=platform,
            style_guide=full_style_guide,
            summary=summary,
            plus_points=plus_points
        )

        try:
            print(f"[*] Generating {platform} draft for material {material_id}...")
            # Use chat completions for drafting
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
            self._save_draft(material_id, platform, draft_content)
            
            audit_logger.log_action(
                "publishing", 
                target_id=material_id, 
                details=f"Generated {platform} draft", 
                status="success",
                tokens_used=tokens_used
            )
            return draft_content
        except Exception as e:
            print(f"Draft generation error: {e}")
            audit_logger.log_action("publishing", target_id=material_id, details=f"Error generating {platform} draft: {e}", status="failure")
            return None

    def _save_draft(self, material_id, platform, content):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO drafts (material_id, platform, content, status)
        VALUES (?, ?, ?, 'pending')
        ''', (material_id, platform, content))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    formatter = OmniFormatter()
    print("OmniFormatter ready.")
