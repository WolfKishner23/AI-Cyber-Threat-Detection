import sqlite3
import os

db_path = "cyber_threat_platform.db"
if not os.path.exists(db_path):
    print(f"Database {db_path} not found.")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customer';")
    result = cursor.fetchone()
    print(f"Table customer exists: {bool(result)}")
