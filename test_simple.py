# test_simple.py
import os
import sqlite3

print("=" * 50)
print("DATABASE CONNECTION TEST")
print("=" * 50)

# Show current folder
print(f"\n📁 Current folder: {os.getcwd()}")
print(f"📊 Database file: trading_journal.db")
print(f"✅ File exists: {os.path.exists('trading_journal.db')}")
print(f"📏 File size: {os.path.getsize('trading_journal.db')} bytes")

try:
    print("\n" + "-" * 50)
    print("🔗 Attempting to connect to database...")

    # Try to connect
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    print("✅ Connected successfully!")

    # List tables
    print("\n📋 Checking tables...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print(f"Found {len(tables)} table(s):")
    for table in tables:
        print(f"  - {table[0]}")

    # Check trades table
    if any('trades' in t[0] for t in tables):
        print("\n📈 Checking trades table...")

        # Count trades
        cursor.execute("SELECT COUNT(*) FROM trades;")
        count = cursor.fetchone()[0]
        print(f"Total trades: {count}")

        # Get sample data
        cursor.execute("SELECT symbol, entry_price, pnl FROM trades LIMIT 5;")
        trades = cursor.fetchall()

        print("\nSample trades (first 5):")
        for trade in trades:
            symbol, entry, pnl = trade
            print(f"  {symbol}: ${entry:.2f}, P&L: ${pnl:.2f}" if pnl else f"  {symbol}: ${entry:.2f}, P&L: None")

    conn.close()
    print("\n" + "=" * 50)
    print("🎉 TEST COMPLETE - DATABASE IS READABLE!")
    print("=" * 50)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print(f"\n💡 Possible fixes:")
    print("1. Close any other programs using the database")
    print("2. Check file permissions")
    print("3. Make sure SQLite is installed")