import sqlite3

conn = sqlite3.connect('trading_journal.db')
cursor = conn.cursor()

# Check for duplicates
cursor.execute('''
    SELECT symbol, side, entry_time, COUNT(*) as count 
    FROM trades 
    WHERE notes LIKE '%Imported from Bybit%'
    GROUP BY symbol, side, entry_time 
    HAVING count > 1
''')
duplicates = cursor.fetchall()

print(f'Found {len(duplicates)} duplicate groups:')
for d in duplicates:
    print(f'  {d[0]} {d[1]} at {d[2]}: {d[3]} copies')

# Get all imported trades with their IDs
cursor.execute('''
    SELECT id, symbol, side, entry_time, notes 
    FROM trades 
    WHERE notes LIKE '%Imported from Bybit%'
    ORDER BY entry_time, id
''')
all_imported = cursor.fetchall()

print(f'\nTotal imported trades: {len(all_imported)}')

# Show duplicates with IDs
for d in duplicates:
    symbol, side, entry_time, count = d
    print(f'\nDuplicates for {symbol} {side} at {entry_time}:')
    cursor.execute('''
        SELECT id, created_at 
        FROM trades 
        WHERE symbol = ? AND side = ? AND entry_time = ? AND notes LIKE '%Imported from Bybit%'
        ORDER BY id
    ''', (symbol, side, entry_time))
    dup_ids = cursor.fetchall()
    for trade_id, created_at in dup_ids:
        print(f'  ID: {trade_id}, Created: {created_at}')

conn.close()
