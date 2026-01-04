# day7_simple_calendar.py - ENHANCED VERSION
# Now with better sample data distribution

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import calendar
import random


def add_diverse_sample_data(cursor):
    """Add trades spread across multiple days for better calendar testing"""
    print("\n📅 Adding diverse sample data across multiple days...")

    symbols = ['BTC', 'ETH', 'SOL', 'ADA', 'XRP']

    # Clear existing sample data (optional - comment out if you want to keep real data)
    # cursor.execute("DELETE FROM trades WHERE symbol IN ('BTC', 'ETH', 'SOL', 'ADA', 'XRP')")

    # Add trades for the last 60 days
    for day_offset in range(60):
        date = (datetime.now() - timedelta(days=day_offset)).strftime('%Y-%m-%d %H:%M')

        # Some days have trades, some don't
        trades_today = random.randint(0, 3)

        for _ in range(trades_today):
            symbol = random.choice(symbols)
            pnl = random.uniform(-300, 500)
            side = random.choice(['LONG', 'SHORT'])
            entry_price = random.uniform(100, 50000)
            exit_price = entry_price + (pnl / random.uniform(0.5, 2))
            quantity = random.uniform(0.1, 5)

            cursor.execute('''
                INSERT INTO trades (date, symbol, side, entry_price, exit_price, quantity, pnl, entry_time, exit_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (date, symbol, side, entry_price, exit_price, quantity, pnl, date, date))

    print("✅ Added diverse sample data across 60 days")


def main():
    print("=" * 60)
    print("DAY 7: CALENDAR VIEW & DATABASE ENHANCEMENT")
    print("=" * 60)

    # 1. Setup database
    print("\n📊 STEP 1: Checking database structure...")

    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    # Check what columns exist in trades table
    cursor.execute("PRAGMA table_info(trades)")
    columns = cursor.fetchall()

    if not columns:
        print("No trades table found. Creating new table...")
        # Create table matching Day 6 structure
        cursor.execute('''
        CREATE TABLE trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            side TEXT,
            entry_price REAL,
            exit_price REAL,
            quantity REAL,
            pnl REAL,
            entry_time TEXT,
            exit_time TEXT,
            date TEXT
        )
        ''')
        print("Created new trades table")

    column_names = [col[1] for col in columns]
    print(f"Columns: {', '.join(column_names)}")

    # Check if we have date column
    if 'date' not in column_names:
        print("Adding 'date' column to existing table...")
        try:
            cursor.execute("ALTER TABLE trades ADD COLUMN date TEXT")
            conn.commit()
            print("Added date column")
        except Exception as e:
            print(f"Could not add date column: {e}")

    # Populate date if empty
    cursor.execute("SELECT COUNT(*) FROM trades WHERE date IS NULL OR date = ''")
    null_dates = cursor.fetchone()[0]

    if null_dates > 0:
        print(f"Found {null_dates} trades without dates. Populating...")
        cursor.execute("SELECT id, entry_time FROM trades WHERE date IS NULL OR date = ''")
        trades = cursor.fetchall()

        for trade_id, entry_time in trades:
            if entry_time:
                cursor.execute("UPDATE trades SET date = ? WHERE id = ?", (entry_time, trade_id))
            else:
                # Add random date if no entry_time
                random_date = (datetime.now() - timedelta(days=random.randint(0, 60))).strftime('%Y-%m-%d %H:%M')
                cursor.execute("UPDATE trades SET date = ? WHERE id = ?", (random_date, trade_id))

        conn.commit()
        print("Populated missing dates")

    # Ask if user wants to add diverse sample data
    print("\n📈 Do you want to add diverse sample data for better calendar testing?")
    print("   (This will add trades across multiple days)")
    response = input("   Enter 'yes' to add sample data, or press Enter to skip: ")

    if response.lower() == 'yes':
        add_diverse_sample_data(cursor)
        conn.commit()

    # 2. Load and show data
    print("\n📈 STEP 2: Loading trade data...")

    df = pd.read_sql_query("SELECT * FROM trades ORDER BY date", conn)

    if not df.empty:
        print(f"\n✅ Successfully loaded {len(df)} trades")

        # Convert date to datetime
        try:
            df['date'] = pd.to_datetime(df['date'])
        except:
            print("⚠️ Could not parse dates, using today's date")
            df['date'] = datetime.now()

        print(f"\n📊 TRADE STATS:")
        print(f"   Total trades: {len(df)}")

        if 'pnl' in df.columns:
            total_pnl = df['pnl'].sum()
            winning_trades = df[df['pnl'] > 0]
            losing_trades = df[df['pnl'] < 0]
            win_rate = len(winning_trades) / len(df) * 100 if len(df) > 0 else 0

            print(f"   Total P&L: ${total_pnl:.2f}")
            print(f"   Win rate: {win_rate:.1f}% ({len(winning_trades)} wins, {len(losing_trades)} losses)")
            print(
                f"   Avg win: ${winning_trades['pnl'].mean():.2f}" if len(winning_trades) > 0 else "   Avg win: $0.00")
            print(
                f"   Avg loss: ${losing_trades['pnl'].mean():.2f}" if len(losing_trades) > 0 else "   Avg loss: $0.00")
        else:
            print("   Note: No P&L column found")

        print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
        print(f"   Unique trading days: {df['date'].dt.date.nunique()}")

        # Show trade distribution by day
        print(f"\n📅 Trade distribution by day:")
        daily_counts = df['date'].dt.date.value_counts().sort_index()
        for date, count in daily_counts.items():
            print(f"   {date}: {count} trade{'s' if count != 1 else ''}")

        # 3. Show calendar
        print("\n📅 STEP 3: Calendar View")
        print("-" * 40)

        # Ask for month/year or use current
        current_year = datetime.now().year
        current_month = datetime.now().month

        print(f"\nSelect month for calendar view:")
        print(f"   Press Enter for current month ({calendar.month_name[current_month]} {current_year})")

        try:
            year_input = input(f"   Enter year ({current_year}): ")
            month_input = input(f"   Enter month 1-12 ({current_month}): ")

            year = int(year_input) if year_input.strip() else current_year
            month = int(month_input) if month_input.strip() else current_month

            if month < 1 or month > 12:
                print("⚠️ Invalid month, using current month")
                month = current_month
        except:
            print("⚠️ Invalid input, using current month")
            year = current_year
            month = current_month

        print(f"\nCalendar for {calendar.month_name[month]} {year}:")
        print()

        # Create text calendar
        cal = calendar.Calendar()
        month_days = cal.monthdayscalendar(year, month)

        # Print day names
        day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for day in day_names:
            print(f"{day:>6}", end="")
        print()

        # Print each week
        for week in month_days:
            for day in week:
                if day != 0:
                    day_date = datetime(year, month, day).date()

                    # Check if we have trades for this day
                    day_trades = df[df['date'].dt.date == day_date]

                    if len(day_trades) > 0:
                        if 'pnl' in df.columns:
                            daily_pnl = day_trades['pnl'].sum()
                            trade_count = len(day_trades)

                            if daily_pnl > 100:
                                print(f" {day:2d}[++]", end="")  # Big profit
                            elif daily_pnl > 0:
                                print(f" {day:2d}[+]", end="")  # Profit
                            elif daily_pnl < -100:
                                print(f" {day:2d}[--]", end="")  # Big loss
                            elif daily_pnl < 0:
                                print(f" {day:2d}[-]", end="")  # Loss
                            else:
                                print(f" {day:2d}[=]", end="")  # Break even
                        else:
                            print(f" {day:2d}[T]", end="")  # Has trades
                    else:
                        print(f" {day:2d}  ", end="")  # No trades
                else:
                    print("     ", end="")
            print()  # New line after each week

        print("\nLegend: [++] Big profit [+] Profit [=] Break even [-] Loss [--] Big loss")

        # Show month summary
        month_data = df[(df['date'].dt.year == year) & (df['date'].dt.month == month)]
        if not month_data.empty and 'pnl' in month_data.columns:
            month_pnl = month_data['pnl'].sum()
            month_trades = len(month_data)
            profitable_days = len(month_data[month_data['pnl'] > 0])
            total_days = month_data['date'].dt.date.nunique()

            print(f"\n📈 Month Summary:")
            print(f"   Month P&L: ${month_pnl:.2f}")
            print(f"   Total trades: {month_trades}")
            print(f"   Trading days: {total_days}")
            if total_days > 0:
                print(f"   Day win rate: {(profitable_days / total_days * 100):.1f}%")

        # 4. Database enhancement - Key Levels
        print("\n🗄️ STEP 4: Database Enhancement")
        print("-" * 40)

        # Create key levels table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS key_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            level_type TEXT,
            symbol TEXT,
            value REAL,
            strength INTEGER,
            notes TEXT
        )
        ''')

        # Check if we have key levels
        cursor.execute("SELECT COUNT(*) FROM key_levels")
        key_levels_count = cursor.fetchone()[0]

        if key_levels_count == 0:
            print("Adding default key levels...")

            default_levels = [
                ('BTC Major Support', 'Support', 'BTC', 40000.00, 5, 'Major psychological level'),
                ('BTC Major Resistance', 'Resistance', 'BTC', 50000.00, 5, 'Key resistance zone'),
                ('BTC 20 EMA', 'Trendline', 'BTC', 42000.00, 3, '20 EMA on 4H chart'),
                ('ETH Support Zone', 'Support', 'ETH', 2200.00, 4, 'Strong support area'),
                ('ETH Resistance', 'Resistance', 'ETH', 2800.00, 4, 'Previous highs'),
                ('SOL Support', 'Support', 'SOL', 80.00, 3, 'Key support level'),
                ('Daily Pivot', 'Pivot', 'ALL', 0.00, 2, 'Standard pivot point'),
                ('Weekly High', 'Resistance', 'ALL', 0.00, 3, 'Weekly high reference'),
            ]

            for level in default_levels:
                cursor.execute('''
                    INSERT INTO key_levels (name, level_type, symbol, value, strength, notes) 
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', level)

            conn.commit()
            print(f"✅ Added {len(default_levels)} default key levels")
        else:
            print(f"Found {key_levels_count} existing key levels")

        # Show key levels by symbol
        print("\n📋 KEY LEVELS BY SYMBOL:")
        cursor.execute("SELECT symbol, COUNT(*) as count FROM key_levels GROUP BY symbol")
        symbol_counts = cursor.fetchall()

        for symbol, count in symbol_counts:
            print(f"\n   {symbol} ({count} levels):")
            cursor.execute(
                "SELECT name, level_type, value, strength FROM key_levels WHERE symbol = ? ORDER BY level_type",
                (symbol,))
            levels = cursor.fetchall()

            for name, level_type, value, strength in levels:
                stars = "★" * strength + "☆" * (5 - strength)
                print(f"     • {name}: ${value:,.2f} ({level_type}) {stars}")

        # Show junction table
        print("\n🔗 Creating trade_key_levels junction table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trade_key_levels (
            trade_id INTEGER NOT NULL,
            key_level_id INTEGER NOT NULL,
            relationship TEXT,
            notes TEXT,
            PRIMARY KEY (trade_id, key_level_id),
            FOREIGN KEY (trade_id) REFERENCES trades (id),
            FOREIGN KEY (key_level_id) REFERENCES key_levels (id)
        )
        ''')
        print("✅ Created junction table for linking trades to key levels")

    else:
        print("No trades found in database!")

    # Show final database structure
    print("\n📁 FINAL DATABASE STRUCTURE:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        cols = cursor.fetchall()
        print(f"   {table_name}: {len(cols)} columns")

    # Cleanup
    conn.close()

    print("\n" + "=" * 60)
    print("✅ DAY 7 COMPLETE!")
    print("=" * 60)
    print("\n🎉 SUCCESS! All Day 7 objectives achieved:")
    print("1. ✅ Database structure checked and enhanced")
    print("2. ✅ Calendar view with detailed profit/loss indicators")
    print("3. ✅ Month selection and summary")
    print("4. ✅ Key levels system with default levels")
    print("5. ✅ Junction table for trade-key level relationships")
    print("\n📂 Files created/updated:")
    print("   - trading_journal.db (enhanced with key levels)")
    print("   - day7_simple_calendar.py (this script)")
    print("\n🚀 Ready for Day 8: Enhanced Trade Entry & Modal!")


if __name__ == "__main__":
    main()