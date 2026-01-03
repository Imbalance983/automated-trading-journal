# day2_sqlite_journal.py
# DAY 2: SQLite Database Implementation

import sqlite3

print("\n🗄️  DAY 2: SQLite Database Implementation")
print("=" * 50)


class DatabaseManager:
    def __init__(self, db_name="trading_journal.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            return True
        except sqlite3.Error as e:
            print(f"❌ Database connection error: {e}")
            return False

    def create_table(self):
        try:
            # Delete old table first
            self.cursor.execute("DROP TABLE IF EXISTS trades")

            # Create fresh table
            create_table_sql = """
            CREATE TABLE trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                quantity REAL NOT NULL,
                pnl REAL NOT NULL,
                entry_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                exit_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            self.cursor.execute(create_table_sql)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"❌ Table creation error: {e}")
            return False

    def add_trade(self, symbol, side, entry_price, exit_price, quantity):
        try:
            # Calculate P&L
            if side.lower() == 'buy':
                pnl = (exit_price - entry_price) * quantity
            else:
                pnl = (entry_price - exit_price) * quantity

            # Insert trade
            insert_sql = """
            INSERT INTO trades (symbol, side, entry_price, exit_price, quantity, pnl)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(insert_sql, (
                symbol.upper(),
                side.lower(),
                entry_price,
                exit_price,
                quantity,
                pnl
            ))
            self.conn.commit()

            trade_id = self.cursor.lastrowid
            print(f"✅ Trade #{trade_id} added: {symbol} {side} - P&L: ${pnl:,.2f}")
            return trade_id
        except sqlite3.Error as e:
            print(f"❌ Error adding trade: {e}")
            return None

    def get_all_trades(self):
        try:
            select_sql = "SELECT * FROM trades ORDER BY entry_time"
            self.cursor.execute(select_sql)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"❌ Error fetching trades: {e}")
            return []

    def close(self):
        if self.conn:
            self.conn.close()


def test_database_system():
    print("\n" + "=" * 50)
    print("🧪 TESTING DATABASE SYSTEM")
    print("=" * 50)

    db = DatabaseManager()
    if not db.connect():
        return

    if not db.create_table():
        db.close()
        return

    print("✅ Trades table created/verified")
    print("✅ Database 'trading_journal.db' ready")

    print("\n1. Adding test trades...")
    print("-" * 40)

    # ADD ALL 10 TRADES HERE (not just 2)
    db.add_trade("BTCUSD", "buy", 45000, 45500, 0.5)
    db.add_trade("BTCUSD", "sell", 45500, 45300, 0.3)
    db.add_trade("ETHUSD", "buy", 2500, 2600, 2.0)
    db.add_trade("ETHUSD", "sell", 2600, 2580, 1.5)
    db.add_trade("BTCUSD", "buy", 45300, 46000, 0.2)
    db.add_trade("ETHUSD", "buy", 2580, 2650, 3.0)
    db.add_trade("BTCUSD", "sell", 46000, 45800, 0.4)
    db.add_trade("ETHUSD", "sell", 2650, 2700, 2.5)
    db.add_trade("BTCUSD", "buy", 45800, 46500, 0.6)
    db.add_trade("ETHUSD", "buy", 2700, 2750, 1.8)

    print("\n2. Getting all trades...")
    print("-" * 40)

    all_trades = db.get_all_trades()
    print(f"📋 Found {len(all_trades)} trades in database")

    if all_trades:
        print("\n3. Sample trades:")
        print("-" * 40)
        for trade in all_trades[:3]:
            trade_id, symbol, side, entry, exit, qty, pnl, entry_time, exit_time = trade
            print(f"   ID {trade_id}: {symbol} {side} - P&L: ${pnl:,.2f}")

    db.close()
    print("🔌 Database connection closed")


def main():
    test_database_system()
    print("\n" + "=" * 50)
    print("✅ DAY 2 COMPLETE!")
    print("Database: trading_journal.db created successfully")
    print("Next: Day 3 - Pandas Data Analysis")
    print("=" * 50)


if __name__ == "__main__":
    main()