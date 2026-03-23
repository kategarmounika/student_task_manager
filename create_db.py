import sqlite3

conn = sqlite3.connect("database.db")

conn.execute("""
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    status TEXT
)
""")

conn.commit()
conn.close()

print("Database created successfully!")