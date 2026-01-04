import sys

sys.path.append('.')
from utils.bybit_client import BybitClient

print("🔍 Debugging Bybit trade data...")
client = BybitClient()

response = client.client.get_executions(category="linear", limit=3)

if response['retCode'] == 0:
    trades = response['result']['list']
    print(f"API returned {len(trades)} trades")

    for i, trade in enumerate(trades):
        print(f"\n📊 Trade {i + 1} keys:")
        for key in trade.keys():
            value = trade[key]
            print(f"  {key}: {value} (type: {type(value).__name__})")
else:
    print(f"❌ API Error: {response['retMsg']}")