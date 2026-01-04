# database/key_levels_db.py
# Database migration and key levels management

import sqlite3
from datetime import datetime


def migrate_database():
    """Migrate database to include key levels system"""
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    print("🔧 Running database migration...")

    # 1. Ensure trades table has date column
    cursor.execute("PRAGMA table_info(trades)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'date' not in columns:
        print("  Adding 'date' column to trades table...")
        try:
            cursor.execute("ALTER TABLE trades ADD COLUMN date TEXT")
            # Populate from entry_time if available
            cursor.execute("UPDATE trades SET date = entry_time WHERE date IS NULL")
            print("  ✅ Added date column")
        except Exception as e:
            print(f"  ⚠️ Could not add date column: {e}")

    # 2. Create key_levels table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_key_levels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        level_type TEXT CHECK(level_type IN ('Support', 'Resistance', 'Trendline', 'Fibonacci', 'Pivot')),
        symbol TEXT,
        value REAL NOT NULL,
        strength INTEGER CHECK(strength BETWEEN 1 AND 5),
        timeframe TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 3. Create junction table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trade_key_levels (
        trade_id INTEGER NOT NULL,
        key_level_id INTEGER NOT NULL,
        relationship TEXT CHECK(relationship IN ('Bounce', 'Break', 'Test', 'Respect', 'Ignore')),
        notes TEXT,
        PRIMARY KEY (trade_id, key_level_id),
        FOREIGN KEY (trade_id) REFERENCES trades (id),
        FOREIGN KEY (key_level_id) REFERENCES user_key_levels (id)
    )
    ''')

    # 4. Add default key levels if none exist
    cursor.execute("SELECT COUNT(*) FROM user_key_levels")
    if cursor.fetchone()[0] == 0:
        default_levels = [
            ('BTC Major Support', 'Support', 'BTCUSDT', 40000.00, 5, '1D', 'Major psychological level'),
            ('BTC Major Resistance', 'Resistance', 'BTCUSDT', 50000.00, 5, '1D', 'Key resistance zone'),
            ('BTC 20 EMA', 'Trendline', 'BTCUSDT', 42000.00, 3, '4H', '20 EMA on 4H chart'),
            ('ETH Support Zone', 'Support', 'ETHUSDT', 2200.00, 4, '1D', 'Strong support area'),
            ('ETH Resistance', 'Resistance', 'ETHUSDT', 2800.00, 4, '1D', 'Previous highs'),
            ('SOL Support', 'Support', 'SOLUSDT', 80.00, 3, '1D', 'Key support level'),
            ('Daily Pivot', 'Pivot', 'ALL', 0.00, 2, '1D', 'Standard pivot point'),
        ]

        cursor.executemany('''
            INSERT INTO user_key_levels (name, level_type, symbol, value, strength, timeframe, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', default_levels)

        print(f"  ✅ Added {len(default_levels)} default key levels")

    conn.commit()

    # Show final structure
    print("\n📁 Database Structure:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        cols = cursor.fetchall()
        print(f"  {table_name}: {len(cols)} columns")

    conn.close()
    print("\n✅ Migration complete!")
    return True


if __name__ == "__main__":
    migrate_database()