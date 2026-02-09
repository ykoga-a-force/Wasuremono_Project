import sqlite3
import os

db_path = 'wasuremono.db'
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("--- history (Last 10) ---")
try:
    cursor.execute('SELECT * FROM history ORDER BY date DESC LIMIT 10')
    for row in cursor.fetchall():
        print(dict(row))
except Exception as e:
    print(f"Error fetching history: {e}")

print("\n--- daily_schedules (Last 10) ---")
try:
    cursor.execute('SELECT * FROM daily_schedules ORDER BY date DESC LIMIT 10')
    for row in cursor.fetchall():
        print(dict(row))
except Exception as e:
    print(f"Error fetching schedules: {e}")

conn.close()
