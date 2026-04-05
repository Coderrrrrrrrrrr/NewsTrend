import sqlite3
import os

db_path = "data/news_trend.db"

def repair():
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    print(f"Attempting to repair {db_path}...")
    try:
        # Use bytes to fetch corrupted names
        conn = sqlite3.connect(db_path, timeout=10)
        conn.text_factory = bytes
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name FROM sources")
        rows = cursor.fetchall()
        
        for row_id, raw_name in rows:
            try:
                # Try to decode as UTF-8 (the correct ones)
                raw_name.decode('utf-8')
            except UnicodeDecodeError:
                # If it fails, it's likely the GBK corrupted one
                try:
                    correct_name = raw_name.decode('gbk')
                    print(f"Repairing ID {row_id}: {correct_name}")
                    
                    # Update with correct UTF-8 string
                    # We need a new cursor or connection that handles text normally
                    conn_fix = sqlite3.connect(db_path, timeout=10)
                    conn_fix.execute("UPDATE sources SET name = ? WHERE id = ?", (correct_name, row_id))
                    conn_fix.commit()
                    conn_fix.close()
                except Exception as e:
                    print(f"Failed to fix ID {row_id}: {e}")
        
        conn.close()
        print("Repair complete. Please restart your application.")
    except sqlite3.OperationalError as e:
        if "locked" in str(e).lower():
            print("\n!!! DATABASE IS LOCKED !!!")
            print("Please CLOSE your Streamlit application or any other process using the database and try again.")
        else:
            print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    repair()
