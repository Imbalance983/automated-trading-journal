# debug_db.py
import sqlite3

# Check current database structure
print("🔍 DEBUGGING DATABASE STRUCTURE")
print("=" * 50)

conn = sqlite3.connect("trading_journal.db")
cursor = conn.cursor()

# 1. Check all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in database:")
for table in tables:
    print(f"  - {table[0]}")

# 2. Check trades table structure
print("\n📊 trades table structure:")
cursor.execute("PRAGMA table_info(trades)")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# 3. Show existing data
print("\n📈 Sample data (first 3 rows):")
cursor.execute("SELECT * FROM trades LIMIT 3")
rows = cursor.fetchall()
for row in rows:
    print(f"  {row}")

conn.close()
print("=" * 50)
