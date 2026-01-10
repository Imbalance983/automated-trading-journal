"""
Migration script to refactor trades to support one-to-many relations
for key levels, confirmations, entries, models, and screenshots.
"""
import sys
import io
import sqlite3
from datetime import datetime

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def migrate_database():
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    print("=" * 80)
    print("TRADE JOURNAL DATABASE MIGRATION")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # Step 1: Create new child tables
        print("Step 1: Creating new child tables...")

        # Trade Key Levels
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trade_key_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id INTEGER NOT NULL,
            level TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trade_id) REFERENCES trades(id) ON DELETE CASCADE
        )
        ''')
        print("  ✓ Created trade_key_levels table")

        # Trade Confirmations
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trade_confirmations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id INTEGER NOT NULL,
            confirmation TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trade_id) REFERENCES trades(id) ON DELETE CASCADE
        )
        ''')
        print("  ✓ Created trade_confirmations table")

        # Trade Entries
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trade_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id INTEGER NOT NULL,
            entry TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trade_id) REFERENCES trades(id) ON DELETE CASCADE
        )
        ''')
        print("  ✓ Created trade_entries table")

        # Trade Models
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trade_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id INTEGER NOT NULL,
            model TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trade_id) REFERENCES trades(id) ON DELETE CASCADE
        )
        ''')
        print("  ✓ Created trade_models table")

        # Trade Screenshots (MULTIPLE)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trade_screenshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id INTEGER NOT NULL,
            screenshot_url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trade_id) REFERENCES trades(id) ON DELETE CASCADE
        )
        ''')
        print("  ✓ Created trade_screenshots table")
        print()

        # Step 2: Migrate existing data
        print("Step 2: Migrating existing data to new tables...")

        # Get all trades with old data
        cursor.execute('''
            SELECT id, key_level, confirmation, entry, model,
                   screenshot_url, screenshot_1, screenshot_2, screenshot_3
            FROM trades
        ''')
        trades = cursor.fetchall()

        migrated_counts = {
            'key_levels': 0,
            'confirmations': 0,
            'entries': 0,
            'models': 0,
            'screenshots': 0
        }

        for trade in trades:
            trade_id = trade[0]
            key_level = trade[1]
            confirmation = trade[2]
            entry = trade[3]
            model = trade[4]
            screenshot_url = trade[5]
            screenshot_1 = trade[6]
            screenshot_2 = trade[7]
            screenshot_3 = trade[8]

            # Migrate key_level (can be comma-separated)
            if key_level:
                levels = [l.strip() for l in key_level.split(',') if l.strip()]
                for level in levels:
                    cursor.execute('''
                        INSERT INTO trade_key_levels (trade_id, level)
                        VALUES (?, ?)
                    ''', (trade_id, level))
                    migrated_counts['key_levels'] += 1

            # Migrate confirmation (can be comma-separated)
            if confirmation:
                confirmations = [c.strip() for c in confirmation.split(',') if c.strip()]
                for conf in confirmations:
                    cursor.execute('''
                        INSERT INTO trade_confirmations (trade_id, confirmation)
                        VALUES (?, ?)
                    ''', (trade_id, conf))
                    migrated_counts['confirmations'] += 1

            # Migrate entry (can be comma-separated)
            if entry:
                entries = [e.strip() for e in entry.split(',') if e.strip()]
                for ent in entries:
                    cursor.execute('''
                        INSERT INTO trade_entries (trade_id, entry)
                        VALUES (?, ?)
                    ''', (trade_id, ent))
                    migrated_counts['entries'] += 1

            # Migrate model (can be comma-separated)
            if model:
                models = [m.strip() for m in model.split(',') if m.strip()]
                for mod in models:
                    cursor.execute('''
                        INSERT INTO trade_models (trade_id, model)
                        VALUES (?, ?)
                    ''', (trade_id, mod))
                    migrated_counts['models'] += 1

            # Migrate screenshots (multiple sources)
            screenshots = []
            if screenshot_url:
                screenshots.append(screenshot_url)
            if screenshot_1:
                screenshots.append(screenshot_1)
            if screenshot_2:
                screenshots.append(screenshot_2)
            if screenshot_3:
                screenshots.append(screenshot_3)

            for screenshot in screenshots:
                if screenshot.strip():
                    cursor.execute('''
                        INSERT INTO trade_screenshots (trade_id, screenshot_url)
                        VALUES (?, ?)
                    ''', (trade_id, screenshot.strip()))
                    migrated_counts['screenshots'] += 1

        print(f"  ✓ Migrated {migrated_counts['key_levels']} key levels")
        print(f"  ✓ Migrated {migrated_counts['confirmations']} confirmations")
        print(f"  ✓ Migrated {migrated_counts['entries']} entries")
        print(f"  ✓ Migrated {migrated_counts['models']} models")
        print(f"  ✓ Migrated {migrated_counts['screenshots']} screenshots")
        print()

        # Step 3: Update trades table - remove old columns
        print("Step 3: Cleaning up trades table...")
        print("  NOTE: We'll keep old columns for now to prevent data loss")
        print("  They will be marked as deprecated in the app code")
        print()

        # Commit all changes
        conn.commit()

        print("=" * 80)
        print("MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("Summary:")
        print(f"  - {len(trades)} trades processed")
        print(f"  - {sum(migrated_counts.values())} total records migrated")
        print()
        print("Next steps:")
        print("  1. Run the application and test the new Edit Trade popup")
        print("  2. Verify all data is correctly displayed")
        print("  3. Old columns will remain for backward compatibility")
        print()

    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERROR: Migration failed!")
        print(f"   {str(e)}")
        print("\n   Rolling back changes...")
        raise

    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
