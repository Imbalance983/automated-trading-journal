import sqlite3

conn = sqlite3.connect('trading_journal.db')
cursor = conn.cursor()

# Update existing trades without external_id with generated external_ids
cursor.execute("""
    UPDATE trades 
    SET external_id = 
        CASE 
            WHEN symbol = 'BTCUSDT' AND side = 'short' THEN 'BTCUSDT_short_1'
            WHEN symbol = 'BTCUSDT' AND side = 'long' THEN 'BTCUSDT_long_1'
            WHEN symbol = 'BTCUSDT' AND side = 'short' THEN 'BTCUSDT_short_2'
            WHEN symbol = 'BTCUSDT' AND side = 'long' THEN 'BTCUSDT_long_2'
            WHEN symbol = '1000PEPEUSDT' AND side = 'short' THEN '1000PEPEUSDT_short_1'
            WHEN symbol = 'SHIB1000USDT' AND side = 'long' THEN 'SHIB1000USDT_long_1'
            WHEN symbol = 'SHIB1000USDT' AND side = 'long' THEN 'SHIB1000USDT_long_2'
            WHEN symbol = 'XRPUSDT' AND side = 'short' THEN 'XRPUSDT_short_1'
            WHEN symbol = 'XRPUSDT' AND side = 'short' THEN 'XRPUSDT_short_2'
        END
    WHERE notes LIKE '%Imported from Bybit%' AND external_id IS NULL
""")

updated_count = cursor.rowcount
print(f"Updated {updated_count} trades with external_id values")

conn.commit()
conn.close()

print("✅ Updated existing trades with external_id values for proper duplicate tracking")
print("🎯 Now you can:")
print("   1. Sync new trades - they will be properly tracked")
print("   2. Use clear duplicates API if needed")
