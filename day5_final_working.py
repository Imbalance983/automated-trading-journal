
import os

print("🔧 DAY 5: ")
print("=" * 40)

# MANUALLY set your API keys (no .env reading issues)
API_KEY = "wRn8B3OyROiaqRFqR0"
API_SECRET = "gGG6ZkQelxCMaH2UYwBN960MRNlM7agp8Wkh"

print(f"🔑 Using API Key: {API_KEY[:8]}...")
print(f"🔑 Using API Secret: {API_SECRET[:8]}...")

# 1. Connect to Bybit
print("\n1. Connecting to Bybit Testnet...")
try:
    from pybit.unified_trading import HTTP

    client = HTTP(testnet=True, api_key=API_KEY, api_secret=API_SECRET)
    print("✅ Connected to Bybit Testnet!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit()

# 2. Get trades
print("\n2. Fetching your trades...")
try:
    response = client.get_executions(category="linear", limit=10)

    if response['retCode'] != 0:
        print(f"❌ API Error: {response['retMsg']}")
        exit()

    trades = response['result']['list']
    print(f"✅ Got {len(trades)} trade executions")

    if not trades:
        print("⚠️  No trades found")
        exit()

except Exception as e:
    print(f"❌ Error: {e}")
    exit()

# 3. Create database
print("\n3. Creating database...")
import sqlite3
import pandas as pd
from datetime import datetime

# Create data folder
os.makedirs('data', exist_ok=True)

# Create database
db_path = 'data/day5_success.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Simple table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id TEXT PRIMARY KEY,
        symbol TEXT,
        action TEXT,
        amount REAL,
        price REAL,
        fee REAL,
        time TEXT
    )
''')
conn.commit()
print(f"✅ Database created: {db_path}")

# 4. Save trades
print("\n4. Saving trades...")
saved = 0

for i, trade in enumerate(trades):
    try:
        # Get data
        trade_id = trade.get('execId', f'trade_{i}')
        symbol = trade.get('symbol', 'BTCUSDT')
        action = trade.get('side', 'Buy')
        amount = float(trade.get('execQty', 0))
        price = float(trade.get('execPrice', 0))
        fee = float(trade.get('execFee', 0))

        # Get time
        exec_time = trade.get('execTime', '0')
        if exec_time != '0':
            trade_time = datetime.fromtimestamp(int(exec_time) / 1000)
            time_str = trade_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Save to database
        cursor.execute('''
            INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (trade_id, symbol, action, amount, price, fee, time_str))

        saved += 1
        print(f"   ✓ {symbol} {action}: {amount} @ ${price:,.2f}")

    except Exception as e:
        print(f"   ✗ Error: {e}")

conn.commit()
print(f"\n✅ Saved {saved} trades")

# 5. Show results
print("\n5. Your trading history:")
try:
    df = pd.read_sql_query('SELECT * FROM trades ORDER BY time DESC', conn)

    if not df.empty:
        print(f"\n📋 Found {len(df)} trades:")
        print("=" * 70)

        # Format for display
        display_df = df.copy()
        display_df['value'] = display_df['amount'] * display_df['price']

        print(display_df[['symbol', 'action', 'amount', 'price', 'value', 'time']].to_string(index=False))

        # Statistics
        print("\n📊 SUMMARY:")
        print(f"Total trades: {len(df)}")
        print(f"Total volume: ${display_df['value'].sum():,.2f}")
        print(f"Total fees: ${display_df['fee'].sum():.4f}")

        # By symbol
        print("\nBy Symbol:")
        for symbol in df['symbol'].unique():
            symbol_trades = df[df['symbol'] == symbol]
            print(f"  {symbol}: {len(symbol_trades)} trades")

    else:
        print("📭 No trades in database")

except Exception as e:
    print(f"❌ Error reading database: {e}")

# 6. Close connection
conn.close()

print("\n" + "=" * 70)
print("🎉 DAY 5: COMPLETE!")
print(f"📁 Database: {os.path.abspath(db_path)}")
print(f"📊 Trades saved: {saved}")
print("✅ Ready for Day 6: Dashboard!")
print("=" * 70)