import os
import json
import sqlite3
from openai import OpenAI
from dotenv import load_dotenv
from src.engine.prompts import SCORING_PROMPT, AI_GEEK_STYLE, ECONOMY_HISTORICAL_STYLE
from src.engine.persona_prompts import MULTI_PERSONA_SCORING_PROMPT
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

    def _call_llm(self, system_prompt, user_prompt):
        """Helper to call LLM with error handling and fallback."""
        try:
            # Try Ark Responses API
            try:
                response = self.client.responses.create(
                    model=self.model,
                    input=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                if hasattr(response, 'output'):
                    choice = response.output.choices[0]
                    message = choice.message
                    result_text = message.content if hasattr(message, 'content') else message.get('content', '')
                else:
                    result_text = response['output']['choices'][0]['message']['content']
                
                tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else response.get('usage', {}).get('total_tokens', 0)
            except (AttributeError, KeyError, TypeError):
                # Fallback to standard chat completions
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                choice = response.choices[0]
                message = choice.message
                result_text = message.content if hasattr(message, 'content') else message.get('content', '')
                tokens_used = response.usage.total_tokens if hasattr(response, 'usage') else 0
            
            # Cleanup markdown
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
                
            return json.loads(result_text), tokens_used
        except Exception as e:
            print(f"LLM Call Error: {e}")
            return None, 0

    def score_material(self, material_id, content, category):
        """
        Two-stage scoring:
        1. Fast screening with standard scoring.
        2. Multi-persona 'Agentic Evaluation' for high-potential materials.
        """
        system_prompt = AI_GEEK_STYLE if category == 'AI' else ECONOMY_HISTORICAL_STYLE
        fast_result, tokens1 = self._call_llm(system_prompt, SCORING_PROMPT.format(content=content))
        
        if not fast_result:
            return None
            
        final_result = fast_result
        total_tokens = tokens1
        
        # If score is high (>= 3.5), trigger Multi-Persona 'Zhongyiyuan' Audit
        if fast_result.get('score', 0) >= 3.5:
            persona_audit, tokens2 = self._call_llm(
                "You are an AI trend analyzer. Perform a multi-persona audit.",
                MULTI_PERSONA_SCORING_PROMPT.format(content=content)
            )
            if persona_audit:
                # Merge persona audit into result
                final_result['persona_audit'] = persona_audit
                final_result['score'] = persona_audit.get('final_verdict', {}).get('total_score', final_result['score'])
                final_result['visual_prompt'] = persona_audit.get('final_verdict', {}).get('visual_prompt', '')
                total_tokens += tokens2
        
        self._update_db(material_id, final_result)
        audit_logger.log_action("scoring", target_id=material_id, details=f"Scored {category} item: {final_result.get('score')}", status="success", tokens_used=total_tokens)
        return final_result

    def _update_db(self, material_id, result):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Store comprehensive audit context in score_details
        score_details = {
            "details": result.get('details', {}),
            "plus_points": result.get('plus_points', []),
            "minus_points": result.get('minus_points', []),
            "persona_audit": result.get('persona_audit', {}),
            "visual_prompt": result.get('visual_prompt', '')
        }
        
        cursor.execute('''
        UPDATE materials
        SET score = ?, score_details = ?, reasoning = ?, content_summary = ?, logic_trace = ?
        WHERE id = ?
        ''', (
            result.get('score', 0),
            json.dumps(score_details, ensure_ascii=False),
            result.get('reasoning', ''),
            result.get('summary', ''),
            result.get('logic_trace', ''),
            material_id
        ))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    print("AI Scorer with Agentic Evaluation ready.")
