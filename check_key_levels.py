# check_key_levels.py
import sqlite3

print("🔍 CHECKING KEY_LEVELS TABLE")
print("=" * 50)

conn = sqlite3.connect("trading_journal.db")
cursor = conn.cursor()

# Check key_levels table structure
cursor.execute("PRAGMA table_info(key_levels)")
columns = cursor.fetchall()
print("key_levels table columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Check what data is in the table
print("\n📊 Data in key_levels table:")
cursor.execute("SELECT * FROM key_levels")
rows = cursor.fetchall()
for row in rows:
    print(f"  {row}")

conn.close()
print("=" * 50)