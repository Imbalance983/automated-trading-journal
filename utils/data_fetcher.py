# utils/data_fetcher.py
import sqlite3
from datetime import datetime, timedelta
import time


def fetch_and_store_trades():
    """Fetch trades from Bybit and store them"""
    print("\n" + "=" * 50)
    print("🔄 STARTING DATA FETCH")
    print("=" * 50)

    try:
        # First check if we can import Bybit client
        try:
            from utils.bybit_client import BybitTestnetClient
            client = BybitTestnetClient()

            # Try to get account info first
            print("🔍 Testing API connection...")
            account_info = client.get_account_info()

            if account_info:
                print(f"✅ API Connected! Balance: ${account_info['total_balance']:.2f}")

                # Fetch trades
                print("📥 Fetching trades...")
                trades = client.fetch_trades()

                if trades:
                    store_trades(trades)
                    update_daily_summary()
                    update_account_balance(account_info)
                    print(f"✅ Successfully processed {len(trades)} trades")
                else:
                    print("⚠️ No trades fetched, using existing data")
                    update_daily_summary()  # Still update from existing data

            else:
                print("❌ Could not get account info, using simulated data")
                use_simulated_data()

        except ImportError as e:
            print(f"⚠️ Could not import Bybit client: {e}")
            print("📋 Using simulated data instead")
            use_simulated_data()

    except Exception as e:
        print(f"❌ Unexpected error in fetch_and_store_trades: {e}")
        use_simulated_data()


def store_trades(trades):
    """Store trades in database"""
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    # Ensure trades table exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE,
            symbol TEXT,
            side TEXT,
            position_value REAL,
            entry_price REAL,
            exit_price REAL,
            pnl REAL,
            status TEXT,
            entry_time TEXT,
            exit_time TEXT
        )
    ''')

    added_count = 0
    for trade in trades:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO trades 
                (order_id, symbol, side, position_value, entry_price, exit_price, pnl, status, entry_time, exit_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade['order_id'],
                trade['symbol'],
                trade['side'],
                trade['position_value'],
                trade['entry_price'],
                trade['exit_price'],
                trade['pnl'],
                trade['status'],
                trade['entry_time'],
                trade['exit_time']
            ))

            if cursor.rowcount > 0:
                added_count += 1

        except Exception as e:
            print(f"⚠️ Error storing trade {trade.get('order_id')}: {e}")
            continue

    conn.commit()
    conn.close()

    if added_count > 0:
        print(f"💾 Stored {added_count} new trades in database")


def update_daily_summary():
    """Update daily summary table"""
    try:
        conn = sqlite3.connect('trading_journal.db')
        cursor = conn.cursor()

        # Create daily_summary table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE,
                total_trades INTEGER,
                profitable_trades INTEGER,
                total_pnl REAL,
                win_rate REAL
            )
        ''')

        # Get all trades grouped by date
        cursor.execute('''
            SELECT 
                DATE(exit_time) as trade_date,
                COUNT(*) as total_trades,
                SUM(CASE WHEN status = 'win' THEN 1 ELSE 0 END) as profitable_trades,
                SUM(pnl) as total_pnl
            FROM trades 
            WHERE exit_time IS NOT NULL AND status IN ('win', 'loss')
            GROUP BY DATE(exit_time)
            ORDER BY trade_date
        ''')

        daily_data = cursor.fetchall()

        # Clear and update daily summary
        cursor.execute('DELETE FROM daily_summary')

        for date_str, total, profitable, pnl in daily_data:
            if date_str and total > 0:
                win_rate = (profitable / total) * 100
                cursor.execute('''
                    INSERT INTO daily_summary (date, total_trades, profitable_trades, total_pnl, win_rate)
                    VALUES (?, ?, ?, ?, ?)
                ''', (date_str, total, profitable, pnl, win_rate))

        conn.commit()
        conn.close()

        print(f"📈 Updated daily summary for {len(daily_data)} days")

    except Exception as e:
        print(f"⚠️ Error updating daily summary: {e}")


def update_account_balance(account_info):
    """Update account balance in database"""
    try:
        conn = sqlite3.connect('trading_journal.db')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS account (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                balance REAL,
                available_balance REAL,
                total_pnl REAL
            )
        ''')

        cursor.execute('''
            INSERT INTO account (balance, available_balance, total_pnl)
            VALUES (?, ?, ?)
        ''', (
            account_info['total_balance'],
            account_info['available_balance'],
            account_info['total_pnl']
        ))

        # Keep only last 100 records
        cursor.execute('''
            DELETE FROM account 
            WHERE id NOT IN (
                SELECT id FROM account 
                ORDER BY timestamp DESC 
                LIMIT 100
            )
        ''')

        conn.commit()
        conn.close()
        print("💰 Updated account balance")

    except Exception as e:
        print(f"⚠️ Error updating account balance: {e}")


def use_simulated_data():
    """Use simulated data when API fails"""
    print("🎮 Using simulated trading data...")

    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE,
            symbol TEXT,
            side TEXT,
            position_value REAL,
            entry_price REAL,
            exit_price REAL,
            pnl REAL,
            status TEXT,
            entry_time TEXT,
            exit_time TEXT
        )
    ''')

    # Check if we have any trades
    cursor.execute('SELECT COUNT(*) FROM trades')
    count = cursor.fetchone()[0]

    if count == 0:
        print("📝 Generating sample trades...")

        # Generate sample trades for last 30 days
        sample_trades = []
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
        sides = ['buy', 'sell']
        statuses = ['win', 'loss']

        for i in range(50):
            symbol = symbols[i % len(symbols)]
            side = sides[i % len(sides)]
            status = statuses[i % len(statuses)]

            # Generate random but realistic data
            entry_price = 50000 + (i * 100) if symbol == 'BTCUSDT' else 3000 + (i * 10)
            exit_price = entry_price * (1.02 if status == 'win' else 0.98)
            pnl = (exit_price - entry_price) * 0.1 if side == 'buy' else (entry_price - exit_price) * 0.1

            # Generate dates in the past
            days_ago = 30 - (i % 30)
            trade_time = datetime.now() - timedelta(days=days_ago)

            sample_trades.append((
                f'ORDER_{i:04d}',
                symbol,
                side,
                10000 + (i * 1000),
                entry_price,
                exit_price,
                pnl,
                status,
                trade_time.isoformat(),
                (trade_time + timedelta(hours=2)).isoformat()
            ))

        cursor.executemany('''
            INSERT OR IGNORE INTO trades 
            (order_id, symbol, side, position_value, entry_price, exit_price, pnl, status, entry_time, exit_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_trades)

        print(f"✅ Generated {len(sample_trades)} sample trades")

    # Update daily summary
    update_daily_summary()

    # Add account balance if missing
    cursor.execute('SELECT COUNT(*) FROM account')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO account (balance, available_balance, total_pnl)
            VALUES (12900.16, 12000.00, 900.16)
        ''')
        print("💰 Added sample account balance")

    conn.commit()
    conn.close()
    print("✅ Simulation complete")