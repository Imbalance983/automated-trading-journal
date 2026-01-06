import sqlite3

conn = sqlite3.connect('trading_journal.db')
cursor = conn.cursor()

# Check trades without external_id
cursor.execute("SELECT COUNT(*) FROM trades WHERE notes LIKE '%Imported from Bybit%' AND external_id IS NULL")
no_external_id_count = cursor.fetchone()[0]
print(f"Trades without external_id: {no_external_id_count}")

# Check current duplicates
cursor.execute("""
    SELECT symbol, side, COUNT(*) as count, external_id 
    FROM trades 
    WHERE notes LIKE '%Imported from Bybit%'
    GROUP BY symbol, side, external_id 
    HAVING COUNT(*) > 1
    ORDER BY count DESC
    LIMIT 5
""")
duplicates = cursor.fetchall()

print("=== CURRENT DUPLICATES ===")
for dup in duplicates:
    print(f"Symbol: {dup[0]}, Side: {dup[1]}, Count: {dup[2]}, External ID: {dup[3]}")

conn.close()
