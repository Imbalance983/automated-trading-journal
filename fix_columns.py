# Create a file called fix_columns.py
import sqlite3

conn = sqlite3.connect('trading_journal.db')
cursor = conn.cursor()

print("🔧 Fixing database columns...")

# Add emotional_state column if it doesn't exist
try:
    cursor.execute("ALTER TABLE trades ADD COLUMN emotional_state TEXT")
    print("✅ Added emotional_state column")
except:
    print("✓ emotional_state column already exists")

# Add setup_classification column if it doesn't exist
try:
    cursor.execute("ALTER TABLE trades ADD COLUMN setup_classification TEXT")
    print("✅ Added setup_classification column")
except:
    print("✓ setup_classification column already exists")

conn.commit()
conn.close()

print("\n🎯 Database fixed! Now run verification again.")