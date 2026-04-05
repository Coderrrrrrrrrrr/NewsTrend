import os
import json
from openai import OpenAI
from src.engine.prompts import SCORING_PROMPT, AI_GEEK_STYLE, ECONOMY_HISTORICAL_STYLE
import sqlite3
from dotenv import load_dotenv
from src.utils.logger import audit_logger

load_dotenv()

class AIScorer:
    def __init__(self, db_path="data/news_trend.db"):
        self.db_path = db_path
        self.model = os.getenv("LLM_MODEL", "deepseek-v3-2-251201")
        self.api_key = os.getenv("LLM_API_KEY")
        self.base_url = os.getenv("LLM_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )

    def score_content(self, content, category):
        """Pure scoring function that returns the result without DB side effects."""
        system_prompt = AI_GEEK_STYLE if category == 'AI' else ECONOMY_HISTORICAL_STYLE
        
        try:
            tokens_used = 0
            # Try Ark Responses API
            try:
                response = self.client.responses.create(
                    model=self.model,
                    input=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": SCORING_PROMPT.format(content=content)}
                    ]
                )
                # Handle both object and dict-like responses
                if hasattr(response, 'output'):
                    choice = response.output.choices[0]
                    message = choice.message
                    result_text = message.content if hasattr(message, 'content') else message.get('content', '')
                else:
                    # In case it's a dict
                    result_text = response['output']['choices'][0]['message']['content']
                
                tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else response.get('usage', {}).get('total_tokens', 0)
            except (AttributeError, KeyError, TypeError):
                # Fallback to standard chat completions
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": SCORING_PROMPT.format(content=content)}
                    ]
                )
                choice = response.choices[0]
                message = choice.message
                result_text = message.content if hasattr(message, 'content') else message.get('content', '')
                tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            # Cleanup potential markdown code blocks
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(result_text)
            result['tokens_used'] = tokens_used
            return result
        except Exception as e:
            print(f"Scoring logic error: {e}")
            return None

    def score_material(self, material_id, content, category):
        result = self.score_content(content, category)
        if result:
            self._update_db(material_id, result)
            audit_logger.log_action("scoring", target_id=material_id, details=f"Scored {category} item: {result['score']}", status="success", tokens_used=result.get('tokens_used', 0))
            return result
        return None

    def _update_db(self, material_id, result):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # We store the full details object (which now includes justifications)
        # plus any plus/minus points in score_details as JSON.
        full_scoring_context = {
            "details": result.get('details', {}),
            "plus_points": result.get('plus_points', []),
            "minus_points": result.get('minus_points', [])
        }
        
        cursor.execute('''
        UPDATE materials
        SET score = ?, score_details = ?, reasoning = ?, content_summary = ?, logic_trace = ?
        WHERE id = ?
        ''', (
            result.get('score', 0),
            json.dumps(full_scoring_context, ensure_ascii=False),
            result.get('reasoning', ''),
            result.get('summary', ''),
            result.get('logic_trace', ''),
            material_id
        ))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    print("AI Scorer ready.")
