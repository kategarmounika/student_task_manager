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
ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'Medium';

conn.commit()
conn.close()

print("Database created successfully!")