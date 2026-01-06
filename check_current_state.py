import sqlite3

conn = sqlite3.connect('trading_journal.db')
cursor = conn.cursor()

# Check total Bybit trades
cursor.execute('SELECT COUNT(*) FROM trades WHERE notes LIKE ?', ('%Imported from Bybit%',))
total_bybit = cursor.fetchone()[0]
print(f'Total Bybit trades: {total_bybit}')

# Check trades without external_id
cursor.execute('SELECT COUNT(*) FROM trades WHERE notes LIKE ? AND external_id IS NULL', ('%Imported from Bybit%',))
no_external_id = cursor.fetchone()[0]
print(f'Bybit trades without external_id: {no_external_id}')

# Check recent trades with external_id
cursor.execute('SELECT COUNT(*) FROM trades WHERE notes LIKE ? AND external_id IS NOT NULL', ('%Imported from Bybit%',))
with_external_id = cursor.fetchone()[0]
print(f'Bybit trades with external_id: {with_external_id}')

conn.close()
