import sqlite3
import json

class AuditLogger:
    def __init__(self, db_path="data/news_trend.db"):
        self.db_path = db_path

    def log_action(self, action, target_id=None, details=None, status="success", tokens_used=0, model_name=None):
        """V2.2: Logs an action to the audit_logs table."""
        # V2.3: Automatic model_name attribution
        if tokens_used > 0 and (not model_name or model_name == "None"):
            import os
            model_name = os.getenv("LLM_MODEL", "deepseek-v3-2-251201")
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        details_str = json.dumps(details) if isinstance(details, (dict, list)) else details
        
        try:
            cursor.execute('''
            INSERT INTO audit_logs (action, target_id, details, status, tokens_used, model_name)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (action, target_id, details_str, status, tokens_used, model_name))
            conn.commit()
        except Exception as e:
            print(f"Failed to log action: {e}")
        finally:
            conn.close()

# Shared logger instance
audit_logger = AuditLogger()
