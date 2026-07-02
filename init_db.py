import sqlite3

SCHEMA_FILE = "schema.sql"
DB_FILE = "database.db"

with open(SCHEMA_FILE, "r") as f:
    schema_sql = f.read()

conn = sqlite3.connect(DB_FILE)
conn.executescript(schema_sql)
conn.commit()
conn.close()

print(f"✅ {DB_FILE} created successfully from {SCHEMA_FILE}.")
print("   Admin login -> username: admin | password: admin123")
print("   Voter login -> ID: V001 or V002 | password: pass123")
