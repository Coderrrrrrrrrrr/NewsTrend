import sqlite3
import json

class AuditLogger:
    def __init__(self, db_path="data/news_trend.db"):
        self.db_path = db_path

    def log_action(self, action, target_id=None, details=None, status="success", tokens_used=0):
        """Logs an action to the audit_logs table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        details_str = json.dumps(details) if isinstance(details, (dict, list)) else details
        
        try:
            cursor.execute('''
            INSERT INTO audit_logs (action, target_id, details, status, tokens_used)
            VALUES (?, ?, ?, ?, ?)
            ''', (action, target_id, details_str, status, tokens_used))
            conn.commit()
        except Exception as e:
            print(f"Failed to log action: {e}")
        finally:
            conn.close()

# Shared logger instance
audit_logger = AuditLogger()
