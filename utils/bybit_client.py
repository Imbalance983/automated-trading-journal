# utils/bybit_client.py
from pybit.unified_trading import HTTP
import pandas as pd
from datetime import datetime
import time
import json
from config.api_config import BybitConfig


class BybitTestnetClient:
    def __init__(self):
        config = BybitConfig()

        self.session = HTTP(
            testnet=True,
            api_key=config.key,
            api_secret=config.secret
        )
        print("✅ Bybit Testnet client initialized")

    def get_account_info(self):
        """Get account balance and info"""
        try:
            response = self.session.get_wallet_balance(accountType="UNIFIED")

            if response['retCode'] == 0:
                total_balance = float(response['result']['list'][0]['totalWalletBalance'])
                available_balance = float(response['result']['list'][0]['totalAvailableBalance'])
                total_pnl = float(response['result']['list'][0]['totalPerpUPL'])

                print(f"💰 Account Balance: ${total_balance:.2f}")
                return {
                    'total_balance': total_balance,
                    'available_balance': available_balance,
                    'total_pnl': total_pnl
                }
            else:
                print(f"❌ API Error: {response}")
                return None

        except Exception as e:
            print(f"❌ Error getting account info: {e}")
            return None

    def fetch_trades(self):
        """Fetch trade history from last 7 days"""
        try:
            # Calculate timestamps for last 7 days
            end_time = int(time.time() * 1000)
            start_time = end_time - (7 * 24 * 60 * 60 * 1000)  # 7 days ago

            print(
                f"📊 Fetching trades from {datetime.fromtimestamp(start_time / 1000)} to {datetime.fromtimestamp(end_time / 1000)}")

            # Fetch closed P&L
            response = self.session.get_closed_pnl(
                category="linear",
                startTime=start_time,
                endTime=end_time,
                limit=100
            )

            trades = []

            if response['retCode'] == 0:
                if response['result']['list']:
                    for trade_data in response['result']['list']:
                        trade = self._parse_trade(trade_data)
                        if trade:
                            trades.append(trade)
                    print(f"✅ Found {len(trades)} closed trades")
                else:
                    print("⚠️ No closed trades found")
            else:
                print(f"❌ API Error fetching trades: {response}")

            return trades

        except Exception as e:
            print(f"❌ Error fetching trades: {e}")
            return []

    def _parse_trade(self, trade_data):
        """Parse raw trade data from Bybit"""
        try:
            pnl = float(trade_data['closedPnl'])
            order_value = float(trade_data.get('orderValue', 0))

            # Calculate P&L percentage
            pnl_percentage = 0
            if order_value > 0:
                pnl_percentage = (pnl / order_value) * 100

            # Determine status
            status = 'win' if pnl > 0 else 'loss' if pnl < 0 else 'breakeven'

            # Parse timestamps
            entry_time = pd.to_datetime(trade_data['createdTime'], unit='ms').isoformat() if trade_data.get(
                'createdTime') else None
            exit_time = pd.to_datetime(trade_data['updatedTime'], unit='ms').isoformat() if trade_data.get(
                'updatedTime') else None

            return {
                'order_id': str(trade_data.get('orderId', '')),
                'symbol': trade_data.get('symbol', ''),
                'side': 'buy' if trade_data.get('side') == 'Buy' else 'sell',
                'position_value': order_value,
                'entry_price': float(trade_data.get('avgEntryPrice', 0)),
                'exit_price': float(trade_data.get('avgExitPrice', 0)),
                'stop_loss': None,
                'take_profit': None,
                'pnl': pnl,
                'pnl_percentage': pnl_percentage,
                'fee': float(trade_data.get('cumExecFee', 0)),
                'status': status,
                'entry_time': entry_time,
                'exit_time': exit_time,
                'risk_percentage': 1.0,
                'strategy': 'Bybit Trade',
                'notes': ''
            }
        except Exception as e:
            print(f"⚠️ Error parsing trade: {e}")
            return None