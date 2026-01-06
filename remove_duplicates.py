import sqlite3

conn = sqlite3.connect('trading_journal.db')
cursor = conn.cursor()

# Remove the older duplicates (IDs 26-33 from the first failed import)
duplicate_ids = [26, 27, 28, 29, 30, 31, 32, 33]

print(f"Removing {len(duplicate_ids)} duplicate trades...")
for trade_id in duplicate_ids:
    cursor.execute('DELETE FROM trades WHERE id = ?', (trade_id,))
    print(f"  Deleted trade ID {trade_id}")

# Also clean up the bybit_imports table to match
cursor.execute('DELETE FROM bybit_imports')
print("Cleared bybit_imports table")

# Re-add the current imports
current_ids = [34, 35, 36, 37, 38, 39, 40, 41]
for trade_id in current_ids:
    # Get the external_id from the debug log or recreate it
    cursor.execute('SELECT symbol, side, entry_time FROM trades WHERE id = ?', (trade_id,))
    result = cursor.fetchone()
    if result:
        symbol, side, entry_time = result
        # Recreate external_id (this is a simplified approach)
        external_id = f"{symbol}_{side}_{entry_time.replace(' ', '_').replace(':', '')}"
        cursor.execute('INSERT INTO bybit_imports (external_id, network) VALUES (?, ?)', 
                      (external_id, 'testnet'))
        print(f"  Added import record for {symbol} {side}")

conn.commit()
print("\nCleanup complete!")

# Verify no more duplicates
cursor.execute('''
    SELECT symbol, side, entry_time, COUNT(*) as count 
    FROM trades 
    WHERE notes LIKE '%Imported from Bybit%'
    GROUP BY symbol, side, entry_time 
    HAVING count > 1
''')
duplicates = cursor.fetchall()

if duplicates:
    print(f"\nStill found {len(duplicates)} duplicate groups:")
    for d in duplicates:
        print(f'  {d[0]} {d[1]} at {d[2]}: {d[3]} copies')
else:
    print("\nNo duplicates found!")

conn.close()
