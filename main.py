# main.py - SIMPLIFIED VERSION
import os
import sqlite3


def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def show_menu():
    """Display the main menu"""
    clear_screen()
    print("=" * 50)
    print("🚀 AUTOMATED TRADING JOURNAL")
    print("=" * 50)
    print("\nMAIN MENU:")
    print("1. 📝 View Trades")
    print("2. ➕ Add Trade")
    print("3. 📊 View Dashboard")
    print("4. 🎯 View Key Levels")
    print("5. 📈 Advanced Analytics")
    print("6. 🚪 Exit")
    print("=" * 50)


def view_trades():
    """Show all trades from database"""
    clear_screen()
    print("📝 YOUR TRADES")
    print("=" * 50)

    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, symbol, entry_price, exit_price, quantity, pnl, side FROM trades ORDER BY entry_time DESC")
    trades = cursor.fetchall()

    if not trades:
        print("\nNo trades found!")
        print("Add your first trade using option 2")
    else:
        print(f"\nFound {len(trades)} trades:\n")
        print(f"{'ID':<3} {'Symbol':<10} {'Side':<6} {'Entry':<10} {'Exit':<10} {'Qty':<8} {'P&L':<10}")
        print("-" * 65)
        for trade in trades:
            id, symbol, entry, exit, qty, pnl, side = trade
            pnl_color = "🟢" if pnl > 0 else "🔴"
            print(f"{id:<3} {symbol:<10} {side:<6} ${entry:<9.2f} ${exit:<9.2f} {qty:<8.2f} {pnl_color} ${pnl:<8.2f}")

    conn.close()
    input("\nPress Enter to continue...")


def add_trade():
    """Add a new trade"""
    clear_screen()
    print("➕ ADD NEW TRADE")
    print("=" * 50)

    try:
        symbol = input("\nSymbol (e.g., BTC-USD): ").strip()
        entry_price = float(input("Entry Price: "))
        exit_price = float(input("Exit Price: "))
        quantity = float(input("Quantity: "))

        pnl = (exit_price - entry_price) * quantity
        side = "buy" if exit_price > entry_price else "sell"

        conn = sqlite3.connect('trading_journal.db')
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO trades (symbol, side, entry_price, exit_price, quantity, pnl, entry_time)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (symbol, side, entry_price, exit_price, quantity, pnl))

        conn.commit()
        conn.close()

        print(f"\n✅ Trade added successfully!")
        print(f"   Symbol: {symbol}")
        print(f"   Side: {side}")
        print(f"   P&L: ${pnl:.2f}")

    except ValueError:
        print("\n❌ Error: Please enter valid numbers!")
    except Exception as e:
        print(f"\n❌ Error: {e}")

    input("\nPress Enter to continue...")


def view_dashboard():
    """Show simple dashboard"""
    clear_screen()
    print("📊 DASHBOARD")
    print("=" * 50)

    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    # Basic stats
    cursor.execute("SELECT COUNT(*) FROM trades")
    total_trades = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM trades WHERE pnl > 0")
    winning_trades = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(pnl) FROM trades")
    total_pnl = cursor.fetchone()[0] or 0

    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

    print(f"\n📈 PERFORMANCE SUMMARY:")
    print(f"   Total Trades: {total_trades}")
    print(f"   Winning Trades: {winning_trades} ({win_rate:.1f}%)")
    print(f"   Total P&L: ${total_pnl:.2f}")

    # Recent trades
    print(f"\n📋 RECENT TRADES:")
    cursor.execute("SELECT symbol, pnl FROM trades ORDER BY entry_time DESC LIMIT 5")
    recent = cursor.fetchall()
    for symbol, pnl in recent:
        print(f"   {symbol}: ${pnl:+.2f}")

    conn.close()
    input("\nPress Enter to continue...")


def view_key_levels():
    """Show and manage key levels"""
    clear_screen()
    print("🎯 KEY LEVELS")
    print("=" * 50)

    while True:
        print("\nOptions:")
        print("1. View all key levels")
        print("2. Add new key level")
        print("3. Back to main menu")

        choice = input("\nEnter choice (1-3): ").strip()

        if choice == "1":
            show_key_levels_list()
        elif choice == "2":
            add_key_level_simple()
        elif choice == "3":
            break
        else:
            print("❌ Invalid choice!")


def show_key_levels_list():
    """Show all key levels"""
    clear_screen()
    print("🔑 KEY LEVELS LIST")
    print("=" * 50)

    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='key_levels'")
    if not cursor.fetchone():
        print("\nNo key levels table found!")
        print("Add your first key level to create the table.")
        conn.close()
        input("\nPress Enter to continue...")
        return

    cursor.execute("SELECT COUNT(*) FROM key_levels")
    level_count = cursor.fetchone()[0]

    if level_count == 0:
        print("\nNo key levels found!")
        print("Add your first key level using option 2.")
    else:
        print(f"\nFound {level_count} key levels:\n")

        # Try to get whatever columns exist
        cursor.execute("SELECT * FROM key_levels")
        levels = cursor.fetchall()

        # Get column names
        cursor.execute("PRAGMA table_info(key_levels)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        # Display levels based on what we have
        for level in levels:
            if len(level) >= 3:
                id = level[0]
                symbol = level[1] if len(level) > 1 and level[1] else "Unknown"
                level_type = level[2] if len(level) > 2 and level[2] else "Unknown"

                # Try to find strength
                strength = 3
                for i, col_name in enumerate(column_names):
                    if i < len(level) and 'strength' in col_name.lower():
                        strength = level[i] or 3
                        break

                stars = "★" * (strength if strength else 3)
                print(f"   {symbol} {level_type} {stars}")

    conn.close()
    input("\nPress Enter to continue...")


def add_key_level_simple():
    """Add a new key level - SIMPLE VERSION"""
    clear_screen()
    print("➕ ADD NEW KEY LEVEL")
    print("=" * 50)

    try:
        # Ask for just the name (like "Daily Pivot", ".618", "VWAP", etc.)
        level_name = input("\nKey Level Name (e.g., 'Daily Pivot', '.618', 'VWAP'): ").strip()

        # Optional: Ask for symbol if you want to link it to a specific symbol
        symbol = input("Symbol (optional, press Enter to skip): ").strip()
        if not symbol:
            symbol = "General"

        strength = input("Strength (1-5 stars, default 3): ").strip()

        # Set default strength
        if strength and strength.isdigit():
            strength = int(strength)
            strength = max(1, min(5, strength))
        else:
            strength = 3

        # Use with statement to properly handle database connection
        conn = None
        try:
            conn = sqlite3.connect('trading_journal.db', timeout=10)
            cursor = conn.cursor()

            # Create table if it doesn't exist - with CORRECT columns
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS key_levels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    symbol TEXT,
                    strength INTEGER DEFAULT 3,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Add the key level with NAME column
            cursor.execute("""
                INSERT INTO key_levels (name, symbol, strength)
                VALUES (?, ?, ?)
            """, (level_name, symbol, strength))

            conn.commit()

            print(f"\n✅ Key level added successfully!")
            print(f"   Name: {level_name}")
            if symbol != "General":
                print(f"   Symbol: {symbol}")
            print(f"   Strength: {'★' * strength}")

        except sqlite3.OperationalError as e:
            if "locked" in str(e):
                print(f"\n❌ Database is locked!")
                print("   Please close any other programs using the database.")
            else:
                print(f"\n❌ Database error: {e}")
        finally:
            if conn:
                conn.close()

    except Exception as e:
        print(f"\n❌ Error: {e}")

    input("\nPress Enter to continue...")


def view_analytics():
    """Show simple analytics"""
    clear_screen()
    print("📈 ANALYTICS")
    print("=" * 50)

    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    # Basic stats
    cursor.execute("SELECT COUNT(*) FROM trades")
    total_trades = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM trades WHERE pnl > 0")
    winning_trades = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(pnl) FROM trades")
    total_pnl = cursor.fetchone()[0] or 0

    cursor.execute("SELECT AVG(pnl) FROM trades WHERE pnl > 0")
    avg_win = cursor.fetchone()[0] or 0

    cursor.execute("SELECT AVG(pnl) FROM trades WHERE pnl < 0")
    avg_loss = cursor.fetchone()[0] or 0

    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

    print(f"\n📊 PERFORMANCE:")
    print(f"   Total Trades: {total_trades}")
    print(f"   Win Rate: {win_rate:.1f}%")
    print(f"   Total P&L: ${total_pnl:.2f}")
    print(f"   Average Win: ${avg_win:.2f}")
    print(f"   Average Loss: ${avg_loss:.2f}")

    # Best and worst trades
    print(f"\n🏆 BEST & WORST TRADES:")
    cursor.execute("SELECT symbol, pnl FROM trades ORDER BY pnl DESC LIMIT 3")
    best = cursor.fetchall()
    print(f"   Best:")
    for symbol, pnl in best:
        print(f"     {symbol}: ${pnl:+.2f}")

    cursor.execute("SELECT symbol, pnl FROM trades ORDER BY pnl ASC LIMIT 3")
    worst = cursor.fetchall()
    print(f"   Worst:")
    for symbol, pnl in worst:
        print(f"     {symbol}: ${pnl:+.2f}")

    conn.close()
    input("\nPress Enter to continue...")


def main():
    """Main program loop"""
    while True:
        show_menu()
        choice = input("\nEnter choice (1-6): ").strip()

        if choice == "1":
            view_trades()
        elif choice == "2":
            add_trade()
        elif choice == "3":
            view_dashboard()
        elif choice == "4":
            view_key_levels()
        elif choice == "5":
            view_analytics()
        elif choice == "6":
            print("\n👋 Goodbye! Happy trading!")
            break
        else:
            print("❌ Invalid choice!")


if __name__ == "__main__":
    main()