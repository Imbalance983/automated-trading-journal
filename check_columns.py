# check_columns.py - Check what columns your database actually has
import sqlite3

print("🔍 Checking database structure...")
print("=" * 60)

try:
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    # Check trades table columns
    cursor.execute("PRAGMA table_info(trades);")
    columns = cursor.fetchall()

    print("📋 COLUMNS IN 'trades' TABLE:")
    print("-" * 40)
    for col in columns:
        print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULLABLE'}")

    print("\n📊 SAMPLE DATA FROM 'trades' TABLE:")
    print("-" * 40)

    # Get a sample row
    cursor.execute("SELECT * FROM trades LIMIT 1;")
    sample = cursor.fetchone()

    if sample:
        # Get column names
        cursor.execute("SELECT * FROM trades LIMIT 0;")
        col_names = [description[0] for description in cursor.description]

        for i, (name, value) in enumerate(zip(col_names, sample)):
            print(f"  {name}: {value}")

    # Check key_levels table too
    print("\n📋 COLUMNS IN 'key_levels' TABLE:")
    print("-" * 40)
    cursor.execute("PRAGMA table_info(key_levels);")
    key_columns = cursor.fetchall()

    for col in key_columns:
        print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULLABLE'}")

    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)