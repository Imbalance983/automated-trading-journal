# day8_db_migration.py
import sqlite3


def migrate_database():
    """Add missing columns to the database"""
    print("🔧 DATABASE MIGRATION - DAY 8")
    print("=" * 50)

    try:
        conn = sqlite3.connect("trading_journal.db")
        cursor = conn.cursor()

        # Check if pnl_percent column exists
        cursor.execute("PRAGMA table_info(trades)")
        columns = [col[1] for col in cursor.fetchall()]

        print("Current columns in trades table:", columns)

        # Add pnl_percent column if it doesn't exist
        if 'pnl_percent' not in columns:
            print("Adding pnl_percent column...")
            cursor.execute("ALTER TABLE trades ADD COLUMN pnl_percent REAL")
            print("✅ Added pnl_percent column")

        # Also check for other columns we might need
        if 'notes' not in columns:
            print("Adding notes column...")
            cursor.execute("ALTER TABLE trades ADD COLUMN notes TEXT")
            print("✅ Added notes column")

        conn.commit()
        conn.close()

        print("\n✅ Database migration complete!")

    except Exception as e:
        print(f"❌ Migration error: {e}")


if __name__ == "__main__":
    migrate_database()