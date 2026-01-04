import sqlite3
import pandas as pd
from datetime import datetime
import os


class TradeDatabase:
    """Simple database for trades"""

    def __init__(self):
        # Create data folder if it doesn't exist
        os.makedirs('data', exist_ok=True)
        self.db_path = 'data/trading_journal.db'
        self._create_tables()

    def _create_tables(self):
        """Create just ONE simple table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # ONLY trades table (keep it simple)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    trade_id TEXT PRIMARY KEY,
                    symbol TEXT,
                    side TEXT,
                    qty REAL,
                    price REAL,
                    pnl REAL,
                    timestamp DATETIME,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            print("✅ Database ready!")

    def save_trade(self, trade):
        """Save ONE trade"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT OR REPLACE INTO trades 
                    (trade_id, symbol, side, qty, price, pnl, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade.get('id'),
                    trade.get('symbol'),
                    trade.get('side'),
                    trade.get('qty'),
                    trade.get('price'),
                    trade.get('pnl'),
                    trade.get('timestamp')
                ))
                conn.commit()
                print(f"✅ Saved trade: {trade.get('symbol')}")
                return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def get_trades(self):
        """Get all trades"""
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query('SELECT * FROM trades ORDER BY timestamp DESC', conn)
            return df

    def get_stats(self):
        """Get basic stats"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total trades
            cursor.execute('SELECT COUNT(*) FROM trades')
            total = cursor.fetchone()[0]

            if total == 0:
                return {'total_trades': 0, 'total_pnl': 0, 'win_rate': 0}

            # Total P&L
            cursor.execute('SELECT SUM(pnl) FROM trades')
            total_pnl = cursor.fetchone()[0] or 0

            # Win rate
            cursor.execute('SELECT COUNT(*) FROM trades WHERE pnl > 0')
            wins = cursor.fetchone()[0]
            win_rate = (wins / total) * 100

            return {
                'total_trades': total,
                'total_pnl': round(total_pnl, 2),
                'win_rate': round(win_rate, 2)
            }