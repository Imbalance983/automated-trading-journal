# fix_nulls.py
import sqlite3

print("🔧 FIXING NULL VALUES IN DATABASE")
print("=" * 50)

conn = sqlite3.connect("trading_journal.db")
cursor = conn.cursor()

# Fix 1: Update pnl_percent for all trades
print("\n1️⃣ Calculating pnl_percent for all trades...")

# First, let's see what we have
cursor.execute("SELECT id, entry_price, quantity, pnl FROM trades")
trades = cursor.fetchall()

for trade in trades:
    trade_id, entry_price, quantity, pnl = trade

    # Calculate pnl_percent
    if entry_price > 0 and quantity > 0:
        pnl_percent = (pnl / (entry_price * quantity)) * 100
    else:
        pnl_percent = 0

    # Update the database
    cursor.execute("UPDATE trades SET pnl_percent = ? WHERE id = ?",
                   (pnl_percent, trade_id))

    print(f"  Trade #{trade_id}: ${pnl:.2f} → {pnl_percent:.2f}%")

# Fix 2: Set empty notes for NULL values
print("\n2️⃣ Setting empty notes for NULL values...")
cursor.execute("UPDATE trades SET notes = '' WHERE notes IS NULL")

# Count how many were fixed
cursor.execute("SELECT COUNT(*) FROM trades WHERE notes IS NULL")
null_notes = cursor.fetchone()[0]
print(f"  Fixed {null_notes} NULL note values")

# Commit changes
conn.commit()

# Verify the fix
print("\n3️⃣ VERIFYING FIX...")
cursor.execute("SELECT id, pnl, pnl_percent FROM trades LIMIT 3")
fixed_trades = cursor.fetchall()
print("First 3 trades after fix:")
for trade in fixed_trades:
    print(f"  Trade #{trade[0]}: ${trade[1]:.2f} ({trade[2]:.2f}%)")

conn.close()
print("\n✅ NULL values fixed successfully!")
print("=" * 50)


