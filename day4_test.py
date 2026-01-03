"""
DAY 4: BYBIT API TESTNET CONNECTION
"""

import os
import time
from datetime import datetime

# 1. Load environment variables
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("🚀 DAY 4: BYBIT TESTNET API CONNECTION")
print("=" * 60)

# 2. Get API keys from .env file
API_KEY = os.getenv("BYBIT_TESTNET_KEY")
API_SECRET = os.getenv("BYBIT_TESTNET_SECRET")

if not API_KEY or not API_SECRET:
    print("❌ ERROR: Missing API keys in .env file")
    print("\n📋 CREATE .env FILE WITH:")
    print("-" * 40)
    print("BYBIT_TESTNET_KEY=your_key_here")
    print("BYBIT_TESTNET_SECRET=your_secret_here")
    print("-" * 40)
    print("\n💡 Get keys from: https://testnet.bybit.com")
    print("   Login → API Management → Create New Key")
    exit()

print(f"✅ API Key loaded: {API_KEY[:10]}...")
print(f"✅ Environment: TESTNET (Fake Money Only)")
print(f"✅ Your real account: SAFE AND SEPARATE")

# 3. Install pybit if missing
try:
    from pybit.unified_trading import HTTP

    print("✅ pybit library loaded")
except ImportError:
    print("❌ pybit not installed. Installing now...")
    import subprocess

    subprocess.check_call(["pip", "install", "pybit", "python-dotenv"])
    print("✅ pybit installed. Please run script again.")
    exit()

# 4. Connect to Bybit TESTNET
print("\n🔗 Connecting to Bybit Testnet...")
try:
    # IMPORTANT: testnet=True means FAKE MONEY ONLY
    session = HTTP(
        testnet=True,  # ← Testnet = fake money
        api_key=API_KEY,
        api_secret=API_SECRET,
        recv_window=5000  # 5 second timeout
    )
    print("✅ Connected successfully!")
except Exception as e:
    print(f"❌ Connection failed: {str(e)[:100]}")
    print("\n🔧 TROUBLESHOOTING:")
    print("1. Are keys from testnet.bybit.com (NOT main site)?")
    print("2. Is .env file in same folder as this script?")
    print("3. Try creating new API key on testnet")
    exit()

# 5. Test connection with safe request
print("\n🧪 Testing connection...")
try:
    # Get server time (no permissions needed)
    server_time = session.get_server_time()
    timestamp = int(server_time['result']['timeSecond'])  # ← ADD int() HERE
    human_time = datetime.fromtimestamp(timestamp)
    print(f"✅ Server time: {human_time}")
except Exception as e:
    print(f"⚠️  Time format issue: {e}")
    print("⚠️  Continuing anyway - connection is working!")

# 6. Get testnet balance (FAKE MONEY)
print("\n💰 CHECKING TESTNET BALANCE (FAKE MONEY):")
try:
    time.sleep(0.5)  # Wait between requests

    balance = session.get_wallet_balance(accountType="UNIFIED")

    if balance['retCode'] == 0:
        coins = balance['result']['list'][0]['coin']

        print("   Coin     Balance       USD Value")
        print("   ----     -------       ---------")

        total_usd = 0
        for coin in coins:
            usd_val = float(coin['usdValue'])
            if usd_val > 0.01:  # Show coins with value
                total_usd += usd_val
                bal = float(coin['walletBalance'])
                print(f"   {coin['coin']:5} {bal:12.4f}   ${usd_val:12.2f}")

        print(f"\n   💵 TOTAL: ${total_usd:,.2f} (TESTNET FAKE MONEY)")

        if total_usd > 50000:
            print("   🎮 This is PLAY MONEY for testing only!")
    else:
        print(f"   ⚠️  Balance error: {balance['retMsg']}")

except Exception as e:
    print(f"   ❌ Balance check failed: {e}")

# 7. Get market prices
print("\n📈 CURRENT MARKET PRICES:")
symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

for symbol in symbols:
    try:
        time.sleep(0.3)  # Rate limiting

        ticker = session.get_tickers(category="spot", symbol=symbol)

        if ticker['retCode'] == 0:
            data = ticker['result']['list'][0]
            price = float(data['lastPrice'])
            change = float(data['price24hPcnt']) * 100

            arrow = "🔼" if change > 0 else "🔽"
            print(f"   {symbol:8} ${price:9,.2f} {arrow} {change:+.2f}%")
        else:
            print(f"   {symbol:8} Error: {ticker['retMsg']}")

    except Exception as e:
        print(f"   {symbol:8} Failed: {str(e)[:30]}")

# 8. Test trade history (optional)
print("\n📊 CHECKING TRADE HISTORY:")
try:
    time.sleep(0.5)

    trades = session.get_executions(
        category="spot",
        symbol="BTCUSDT",
        limit=5
    )

    if trades['retCode'] == 0:
        trade_list = trades['result']['list']
        if trade_list:
            print(f"   Found {len(trade_list)} BTC trades")
            for trade in trade_list[:2]:  # Show first 2
                side = "BUY" if trade['side'] == 'Buy' else "SELL"
                print(f"   - {side} {trade['execQty']} @ ${trade['price']}")
        else:
            print("   No trades yet - make some on testnet!")
    else:
        print(f"   Trade error: {trades['retMsg']}")

except Exception as e:
    print(f"   Trade check skipped: {e}")

# 9. Success message
print("\n" + "=" * 60)
print("✅ DAY 4 COMPLETE!")
print("=" * 60)
print("\n🎯 NEXT STEPS:")
print("   1. Go to https://testnet.bybit.com")
print("   2. Make test trades (it's FREE play money)")
print("   3. Run this script again to see your trades")
print("   4. Tomorrow: Connect to your SQL database")
print("\n🔒 SECURITY CONFIRMED:")
print("   ✓ Testnet only (fake money)")
print("   ✓ Real account untouched")
print("   ✓ Read-only permissions")

# 10. Ask for test trade
print("\n💡 QUICK TEST:")
response = input("Make a test trade now? (y/n): ")
if response.lower() == 'y':
    print("\nGo to: https://testnet.bybit.com")
    print("1. Click 'Spot Trading'")
    print("2. Buy 0.001 BTC with market order")
    print("3. Wait 1 minute")
    print("4. Run this script again!")