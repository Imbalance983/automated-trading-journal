# utils/bybit_client.py
from pybit.unified_trading import HTTP
import time
from datetime import datetime


class BybitClient:
    def __init__(self, api_key, api_secret):
        print("🔗 Connecting to Bybit Testnet...")

        try:
            # Connect to TESTNET (fake money only)
            self.session = HTTP(
                testnet=True,  # ← IMPORTANT: Testnet only!
                api_key=api_key,
                api_secret=api_secret
            )
            print("✅ Connected successfully!")

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.session = None

    def get_testnet_balance(self):
        """Get fake money balance from testnet"""
        if not self.session:
            return None

        try:
            # Wait between requests to avoid rate limits
            time.sleep(0.3)

            response = self.session.get_wallet_balance(
                accountType="UNIFIED"
            )

            if response['retCode'] == 0:
                coins = response['result']['list'][0]['coin']
                print(f"💰 Testnet Balance Retrieved")
                return coins
            else:
                print(f"Error: {response['retMsg']}")
                return None

        except Exception as e:
            print(f"Error getting balance: {e}")
            return None

    def get_market_price(self, symbol="BTCUSDT"):
        """Get current market price"""
        if not self.session:
            return None

        try:
            time.sleep(0.3)

            response = self.session.get_tickers(
                category="spot",
                symbol=symbol
            )

            if response['retCode'] == 0:
                ticker = response['result']['list'][0]
                return {
                    'symbol': symbol,
                    'price': float(ticker['lastPrice']),
                    'change': float(ticker['price24hPcnt']) * 100
                }
            return None

        except Exception as e:
            print(f"Price error: {e}")
            return None