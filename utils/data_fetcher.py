# utils/data_fetcher.py - UPDATED
from datetime import datetime

def get_trades(bybit_client, count=10):
    """Get trades from Bybit"""
    print(f"📡 Getting {limit} trades from Bybit...")

    try:
        response = bybit_client.client.get_executions(
            category="linear",
            limit=limit
        )

        if response['retCode'] == 0:
            trades = response['result']['list']
            print(f"✅ Got {len(trades)} trades")
            return trades
        else:
            print(f"❌ Error: {response['retMsg']}")
            return []

    except Exception as e:
        print(f"❌ Failed: {e}")
        return []

def make_simple_trade(trade):
    """Convert Bybit trade to simple format - FIXED"""
    try:
        # Use execId as trade_id (NOT tradeId - it doesn't exist!)
        trade_id = trade.get('execId', '')

        if not trade_id:
            print("⚠️  WARNING: execId is empty!")
            # Create a fallback ID
            import time
            trade_id = f"trade_{int(time.time() * 1000)}"

        symbol = trade.get('symbol', 'UNKNOWN')
        side = trade.get('side', 'UNKNOWN')
        qty = float(trade.get('execQty', 0))
        price = float(trade.get('execPrice', 0))

        # Calculate approximate P&L if not provided
        # For now, set to 0 since we don't have closedPnl
        pnl = 0.0

        # Get timestamp
        exec_time = trade.get('execTime', '0')
        if exec_time and exec_time != '0':
            timestamp = datetime.fromtimestamp(int(exec_time) / 1000)
            time_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        else:
            time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        result = {
            'id': trade_id,
            'symbol': symbol,
            'side': side,
            'qty': qty,
            'price': price,
            'pnl': pnl,
            'timestamp': time_str
        }

        print(f"✅ Converted: {symbol} {side} ${price:.2f} (ID: {trade_id[:10]}...)")
        return result

    except Exception as e:
        print(f"❌ Conversion error: {e}")
        return None