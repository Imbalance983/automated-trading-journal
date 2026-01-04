# day11_main.py
"""
DAY 11 - PROFESSIONAL TRADER'S JOURNAL
Main execution file
"""
from database.trade_db import TradeDatabase

print("🚀 DAY 11 - PROFESSIONAL TRADER'S JOURNAL")
print("=" * 60)


def main():
    # Initialize database
    db = TradeDatabase()

    # Check existing data
    trades = db.get_trades()
    stats = db.get_stats()

    print(f"📊 Existing: {len(trades)} trades")
    print(f"📈 Stats: {stats}")

    # Show key levels
    levels = db.get_key_levels()
    print(f"🎯 Key Levels: {len(levels)} defined")

    # Menu system
    while True:
        print("\n" + "=" * 60)
        print("PROFESSIONAL TRADING JOURNAL")
        print("=" * 60)
        print("1. Import trades from Bybit")
        print("2. View trades & statistics")
        print("3. Manage key levels")
        print("4. Advanced analytics")
        print("5. Export data")
        print("6. Start auto-scheduler")
        print("0. Exit")

        choice = input("\nSelect option: ").strip()

        if choice == '1':
            hours = input("Hours to look back (default 24): ").strip()
            hours = int(hours) if hours else 24
            db.import_from_bybit(hours_back=hours)

        elif choice == '2':
            print(f"\n📊 STATISTICS:")
            print(stats)

            print(f"\n📈 RECENT TRADES:")
            recent = db.get_trades(limit=10)
            print(recent.to_string() if not recent.empty else "No trades")

        elif choice == '3':
            print("\n🎯 KEY LEVELS:")
            print(levels.to_string() if not levels.empty else "No key levels")

            add_new = input("\nAdd new key level? (y/n): ").lower()
            if add_new == 'y':
                name = input("Level name: ").strip()
                value = float(input("Price value: ").strip())
                category = input("Category: ").strip() or "Custom"
                instrument = input("Instrument (or 'ALL'): ").strip() or "ALL"
                db.add_key_level(name, value, category, instrument)

        elif choice == '6':
            interval = input("Import interval (minutes, default 15): ").strip()
            interval = int(interval) if interval else 15
            db.start_auto_import_scheduler(interval_minutes=interval)
            print(f"✅ Auto-scheduler started (every {interval} minutes)")

        elif choice == '0':
            print("\n✅ Goodbye! Happy trading! 📈")
            break


if __name__ == "__main__":
    main()