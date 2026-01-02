# day2_sqlite_journal.py
# DAY 2: SQLite Database Implementation

import sqlite3
import json
from datetime import datetime

print("🗄️  DAY 2: SQLite Database Implementation")
print("=" * 50)


class DatabaseManager:
    """Handles all database operations for trading journal"""

    def __init__(self, db_name="trading_journal.db"):
        self.db_name = db_name
        self.connection = None
        self.cursor = None
        self.connect()
        self.create_tables()
        print(f"✅ Database '{db_name}' ready")

    def connect(self):
        """Connect to SQLite database"""
        try:
            self.connection = sqlite3.connect(self.db_name)
            self.cursor = self.connection.cursor()
        except sqlite3.Error as e:
            print(f"❌ Connection error: {e}")

    def create_tables(self):
        """Create trades table if it doesn't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            entry_price REAL NOT NULL,
            exit_price REAL NOT NULL,
            quantity REAL NOT NULL,
            pnl REAL,
            entry_time TIMESTAMP,
            notes TEXT
        )
        """
        try:
            self.cursor.execute(create_table_sql)
            self.connection.commit()
            print("✅ Trades table created/verified")
        except sqlite3.Error as e:
            print(f"❌ Table creation error: {e}")

    def add_trade(self, symbol, side, entry_price, exit_price, quantity, notes=""):
        """Add a new trade to database"""
        if side == 'buy':
            pnl = (exit_price - entry_price) * quantity
        else:
            pnl = (entry_price - exit_price) * quantity

        insert_sql = """
        INSERT INTO trades (symbol, side, entry_price, exit_price, 
                           quantity, pnl, entry_time, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            self.cursor.execute(insert_sql, (
                symbol, side, entry_price, exit_price,
                quantity, pnl, datetime.now(), notes
            ))
            self.connection.commit()
            trade_id = self.cursor.lastrowid
            print(f"✅ Trade #{trade_id} added: {symbol} {side} - P&L: ${pnl:.2f}")
            return trade_id
        except sqlite3.Error as e:
            print(f"❌ Error adding trade: {e}")
            return None

    def get_all_trades(self):
        """Get all trades from database"""
        select_sql = "SELECT * FROM trades ORDER BY entry_time DESC"
        try:
            self.cursor.execute(select_sql)
            trades = self.cursor.fetchall()
            print(f"📋 Found {len(trades)} trades in database")
            return trades
        except sqlite3.Error as e:
            print(f"❌ Error fetching trades: {e}")
            return []

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("🔌 Database connection closed")


def main():
    """Test the database system"""
    print("\n" + "=" * 50)
    print("🧪 TESTING DATABASE SYSTEM")
    print("=" * 50)

    # Create database
    db = DatabaseManager()

    # Test 1: Add new trades
    print("\n1. Adding test trades...")
    db.add_trade("BTCUSD", "buy", 50000, 51000, 0.1, "Test buy")
    db.add_trade("ETHUSD", "sell", 3000, 2900, 2, "Test sell")

    # Test 2: Get all trades
    print("\n2. Getting all trades...")
    all_trades = db.get_all_trades()
    print(f"   Found {len(all_trades)} trades")

    # Test 3: Show sample trades
    if all_trades:
        print("\n3. Sample trades:")
        for trade in all_trades[:3]:  # Show first 3 trades
            print(f"   ID {trade[0]}: {trade[1]} {trade[2]} - P&L: ${trade[6]:.2f}")

    # Close connection
    db.close()

    print("\n" + "=" * 50)
    print("✅ DAY 2 COMPLETE!")
    print("Database: trading_journal.db created successfully")
    print("Next: Day 3 - Pandas Data Analysis")
    print("=" * 50)


# THIS IS CRITICAL - makes the program run
if __name__ == "__main__":
    main()