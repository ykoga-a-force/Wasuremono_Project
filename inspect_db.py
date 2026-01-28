import sqlite3
import os

db_path = os.path.join("DB", "wasuremono.db")
if not os.path.exists(db_path):
    print(f"Error: {db_path} not found")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get list of tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", tables)

for table in tables:
    table_name = table[0]
    print(f"\nSchema for {table_name}:")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        print(col)

conn.close()
