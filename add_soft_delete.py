"""
Add soft delete column to trades table
"""
import sys
import io
import sqlite3
from datetime import datetime

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def add_soft_delete():
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    print("=" * 80)
    print("ADDING SOFT DELETE SUPPORT")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        # Step 1: Add is_deleted column
        print("Step 1: Adding is_deleted column...")
        cursor.execute('ALTER TABLE trades ADD COLUMN is_deleted INTEGER DEFAULT 0')
        print("  ✓ Added is_deleted column (default: 0)")
        print()

        conn.commit()

        print("=" * 80)
        print("SOFT DELETE COLUMN ADDED SUCCESSFULLY!")
        print("=" * 80)
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("  ⚠️  Column already exists - skipping")
            print()
        else:
            conn.rollback()
            print(f"\n❌ ERROR: {str(e)}")
            raise

    finally:
        conn.close()

if __name__ == '__main__':
    add_soft_delete()
