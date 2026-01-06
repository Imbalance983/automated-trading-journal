import sqlite3

conn = sqlite3.connect('trading_journal.db')
cursor = conn.cursor()

print("Adding UNIQUE constraint to external_id column...")

# Step 1: Create a new table with unique constraint
cursor.execute('''
    CREATE TABLE trades_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        asset TEXT NOT NULL,
        side TEXT NOT NULL,
        entry_price REAL NOT NULL,
        exit_price REAL NOT NULL,
        quantity REAL NOT NULL,
        entry_time TEXT NOT NULL,
        exit_time TEXT NOT NULL,
        pnl REAL NOT NULL,
        pnl_percentage REAL NOT NULL,
        status TEXT NOT NULL,
        key_level TEXT,
        key_level_type TEXT,
        confirmation TEXT,
        model TEXT,
        notes TEXT,
        screenshot_1 TEXT,
        screenshot_2 TEXT,
        screenshot_3 TEXT,
        created_at TEXT NOT NULL,
        weekly_bias TEXT NOT NULL,
        daily_bias TEXT NOT NULL,
        screenshot_url TEXT,
        external_id TEXT UNIQUE
    )
''')

# Step 2: Copy data from old table to new table
cursor.execute('''
    INSERT INTO trades_new (
        symbol, asset, side, entry_price, exit_price, quantity,
        entry_time, exit_time, pnl, pnl_percentage, status,
        key_level, key_level_type, confirmation, model, notes,
        screenshot_1, screenshot_2, screenshot_3, created_at,
        weekly_bias, daily_bias, screenshot_url, external_id
    )
    SELECT symbol, asset, side, entry_price, exit_price, quantity,
           entry_time, exit_time, pnl, pnl_percentage, status,
           key_level, key_level_type, confirmation, model, notes,
           screenshot_1, screenshot_2, screenshot_3, created_at,
           weekly_bias, daily_bias, screenshot_url, external_id
    FROM trades
''')

# Step 3: Drop old table
cursor.execute('DROP TABLE trades')

# Step 4: Rename new table to original name
cursor.execute('ALTER TABLE trades_new RENAME TO trades')

conn.commit()
conn.close()

print("UNIQUE constraint added to external_id column!")
print("Duplicate prevention will now work properly!")
