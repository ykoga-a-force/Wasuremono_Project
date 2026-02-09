import sqlite3
conn = sqlite3.connect('wasuremono.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute('SELECT * FROM history ORDER BY date DESC LIMIT 5')
for row in cursor.fetchall():
    print(dict(row))
conn.close()
