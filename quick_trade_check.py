# quick_check.py
import sqlite3

conn = sqlite3.connect("trading_journal.db")
cursor = conn.cursor()

print("🔍 DAY 8 VERIFICATION")
print("=" * 50)

# Check trade count
cursor.execute("SELECT COUNT(*) FROM trades")
print(f"Total trades: {cursor.fetchone()[0]}")

# Check trade_key_levels links
cursor.execute("SELECT COUNT(*) FROM trade_key_levels")
print(f"Trade-KeyLevel links: {cursor.fetchone()[0]}")

# Check notes in trades
cursor.execute("SELECT id, notes FROM trades WHERE notes != '' LIMIT 3")
print("\nTrades with notes (first 3):")
for trade in cursor.fetchall():
    print(f"  Trade #{trade[0]}: {len(trade[1])} chars in notes")

conn.close()
print("=" * 50)