# day11_pro_ui.py
"""
STEP 5: Professional Trading Journal UI
"""
from database.trade_db import TradeDatabase
import pandas as pd
from datetime import datetime
import os


class ProfessionalJournal:
    def __init__(self):
        self.db = TradeDatabase()
        self.running = True

    def clear_screen(self):
        """Clear console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_header(self):
        """Display application header"""
        self.clear_screen()
        print("=" * 80)
        print("📊 PROFESSIONAL TRADER'S JOURNAL".center(80))
        print("=" * 80)
        print(f"{'Auto-import':<20} | {'Smart Key Levels':<20} | {'Advanced Analytics':<20} | {'Professional UI':<20}")
        print("=" * 80)

    def display_dashboard(self):
        """Show main dashboard"""
        self.display_header()

        # Get statistics
        stats = self.db.get_stats()
        btc_stats = self.db.get_stats(symbol='BTCUSDT')
        eth_stats = self.db.get_stats(symbol='ETHUSDT')

        print("\n📈 PERFORMANCE DASHBOARD")
        print("-" * 80)

        # Overall stats
        print(f"{'Total Trades:':<20} {stats['total_trades']}")
        print(f"{'Total PnL:':<20} ${stats['total_pnl']:,.2f}")
        print(f"{'Win Rate:':<20} {stats['win_rate']}%")
        print(f"{'Avg PnL/Trade:':<20} ${stats['avg_pnl']:,.2f}")
        print(f"{'Best Trade:':<20} ${stats['best_trade']:,.2f}")
        print(f"{'Worst Trade:':<20} ${stats['worst_trade']:,.2f}")

        # Recent trades
        print("\n🔄 RECENT TRADES")
        print("-" * 80)
        trades = self.db.get_trades(limit=5)
        if not trades.empty:
            display_cols = ['symbol', 'side', 'entry_price', 'exit_price', 'pnl', 'entry_time']
            for _, trade in trades.iterrows():
                pnl_color = "🟢" if trade['pnl'] > 0 else "🔴" if trade['pnl'] < 0 else "⚪"
                print(f"{pnl_color} {trade['symbol']:8} {trade['side']:6} "
                      f"${trade['entry_price']:,.0f} → ${trade['exit_price']:,.0f} "
                      f"(PnL: ${trade['pnl']:,.2f})")
        else:
            print("No trades yet")

        # Key levels
        print("\n🎯 KEY LEVELS SUMMARY")
        print("-" * 80)
        levels = self.db.get_key_levels()
        if not levels.empty:
            # Group by instrument
            grouped = levels.groupby('instrument')
            for instrument, group in grouped:
                print(f"\n{instrument}:")
                for _, level in group.iterrows():
                    print(f"  • {level['level_name']:15} at ${level['value']:,.0f} ({level['category']})")

        print("\n" + "=" * 80)

    def import_menu(self):
        """Import trades menu"""
        self.display_header()
        print("\n📥 TRADE IMPORT SYSTEM")
        print("=" * 60)
        print("1. Auto-import from Bybit (last 24 hours)")
        print("2. Manual import (custom timeframe)")
        print("3. Start auto-scheduler (every 15 minutes)")
        print("4. View import history")
        print("5. Back to main menu")

        choice = input("\nSelect: ").strip()

        if choice == '1':
            hours = input("Hours to look back (default 24): ").strip()
            hours = int(hours) if hours else 24

            print(f"\nImporting trades from last {hours} hours...")
            count = self.db.import_from_bybit(hours_back=hours)

            if count > 0:
                print(f"\n✅ Successfully imported {count} trades!")
            else:
                print("\n⚠️ No new trades imported")

            input("\nPress Enter to continue...")

    def key_levels_menu(self):
        """Smart key levels management"""
        while True:
            self.display_header()
            print("\n🎯 SMART KEY LEVELS MANAGER")
            print("=" * 60)

            # Show current levels
            levels = self.db.get_key_levels()
            if not levels.empty:
                print("\nCurrent Key Levels:")
                print("-" * 60)
                df_display = levels[['level_name', 'value', 'category', 'instrument']]
                print(df_display.to_string(index=False))

            print("\nOptions:")
            print("1. Add new key level")
            print("2. Search/filter key levels")
            print("3. View level statistics")
            print("4. Delete key level")
            print("5. Back to main menu")

            choice = input("\nSelect: ").strip()

            if choice == '1':
                self.add_key_level_ui()

            elif choice == '2':
                self.search_key_levels_ui()

            elif choice == '3':
                self.view_level_statistics_ui()

            elif choice == '4':
                self.delete_key_level_ui()

            elif choice == '5':
                break
            else:
                print("\n❌ Invalid option!")
                input("Press Enter to continue...")

    
    def add_key_level_ui(self):
        """UI for adding key level"""
        self.display_header()
        print("\n➕ ADD NEW KEY LEVEL")
        print("="*60)

        name = input("Level name (e.g., '.618', 'Daily Pivot'): ").strip()
        if not name:
            print("❌ Level name required!")
            input("Press Enter to continue...")
            return

        try:
            value = float(input("Price value: ").strip())
        except:
            print("❌ Invalid price!")
            input("Press Enter to continue...")
            return

        category = input("Category (Fibonacci/Pivot/VWAP/etc): ").strip() or "Custom"
        instrument = input("Instrument (e.g., BTCUSDT, or 'ALL'): ").strip() or "ALL"
        strength = input("Strength (1-5 stars, default 3): ").strip()
        strength = int(strength) if strength else 3
        notes = input("Notes (optional): ").strip()

        level_id = self.db.add_key_level(name, value, category, instrument, strength, notes)
        if level_id:
            print(f"\n✅ Key level '{{name}}' added successfully!")

        input("\nPress Enter to continue...")

    def search_key_levels_ui(self):
        """UI for searching key levels"""
        self.display_header()
        print("\n🔍 SEARCH KEY LEVELS")
        print("="*60)

        search_term = input("Search term (level name, leave empty for all): ").strip()
        category_filter = input("Category filter (leave empty for all): ").strip()
        instrument_filter = input("Instrument filter (leave empty for all): ").strip()

        # Get all levels first
        levels = self.db.get_key_levels()

        # Apply filters
        if not levels.empty:
            filtered = levels.copy()

            if search_term:
                search_lower = search_term.lower()
                filtered = filtered[filtered['level_name'].str.lower().str.contains(search_lower, na=False)]

            if category_filter:
                filtered = filtered[filtered['category'] == category_filter]

            if instrument_filter:
                filtered = filtered[filtered['instrument'] == instrument_filter]

            print(f"\nFound {{len(filtered)}} key levels:")
            print("-"*60)

            if not filtered.empty:
                display_cols = ['level_name', 'value', 'category', 'instrument', 'strength']
                print(filtered[display_cols].to_string(index=False))
            else:
                print("No key levels match your filters")
        else:
            print("No key levels defined yet")

        input("\nPress Enter to continue...")

    def view_level_statistics_ui(self):
        """UI for viewing level statistics"""
        self.display_header()
        print("\n📊 KEY LEVEL STATISTICS")
        print("="*60)

        stats = self.db.get_level_statistics()
        if stats:
            print("\nLevel Performance:")
            print("-"*60)
            for stat in stats:
                win_emoji = "🟢" if stat['win_rate'] > 50 else "🔴" if stat['win_rate'] < 50 else "⚪"
                print(f"{{win_emoji}} {{stat['level']:15}} | "
                      f"Trades: {{stat['trade_count']:3}} | "
                      f"Win Rate: {{stat['win_rate']:6.1f}}% | "
                      f"Avg PnL: ${{stat['avg_pnl']:7.2f}}")
        else:
            print("\nNo statistics available (need trades matched to levels)")

        input("\nPress Enter to continue...")

    def delete_key_level_ui(self):
        """UI for deleting key levels"""
        self.display_header()
        print("\n🗑️ DELETE KEY LEVEL")
        print("="*60)

        # Show current levels
        levels = self.db.get_key_levels()
        if levels.empty:
            print("No key levels to delete")
            input("Press Enter to continue...")
            return

        print("\nCurrent Key Levels:")
        print("-"*60)
        for i, (_, level) in enumerate(levels.iterrows(), 1):
            print(f"{{i}}. {{level['level_name']:15}} at ${{level['value']:,.0f}} ({{level['category']}}, {{level['instrument']}})")

        print(f"\n{{len(levels) + 1}}. Cancel")

        try:
            choice = int(input(f"\nSelect key level to delete (1-{{len(levels)}}): ").strip())

            if choice == len(levels) + 1:
                print("Cancelled")
                input("Press Enter to continue...")
                return

            if 1 <= choice <= len(levels):
                level_to_delete = levels.iloc[choice - 1]

                confirm = input(f"\nDelete '{{level_to_delete['level_name']}}' at ${{level_to_delete['value']}}? (y/n): ").lower()

                if confirm == 'y':
                    # Delete from database
                    import sqlite3
                    conn = sqlite3.connect(self.db.db_path)
                    cursor = conn.cursor()

                    # First delete associations
                    cursor.execute("DELETE FROM trade_levels WHERE level_id = ?", (level_to_delete['id'],))
                    # Then delete the level
                    cursor.execute("DELETE FROM key_levels WHERE id = ?", (level_to_delete['id'],))

                    conn.commit()
                    conn.close()

                    print(f"✅ Key level '{{level_to_delete['level_name']}}' deleted!")
                else:
                    print("Cancelled")
            else:
                print("❌ Invalid selection!")

        except ValueError:
            print("❌ Please enter a number!")

        input("\nPress Enter to continue...")
    def analytics_menu(self):
        """Advanced analytics menu"""
        self.display_header()
        print("\n📈 ADVANCED ANALYTICS")
        print("=" * 60)

        print("1. Per Instrument Statistics")
        print("2. Per Key Level Statistics")
        print("3. Trade-Key Level Analysis")
        print("4. Export Analytics")
        print("5. Back")

        choice = input("\nSelect: ").strip()

        if choice == '1':
            self.display_header()
            print("\n📊 PER INSTRUMENT STATISTICS")
            print("=" * 60)

            # Get all instruments
            trades = self.db.get_trades()
            if not trades.empty:
                instruments = trades['symbol'].unique()

                for instrument in instruments:
                    stats = self.db.get_stats(symbol=instrument)
                    print(f"\n{instrument}:")
                    print(f"  Trades: {stats['total_trades']}")
                    print(f"  Total PnL: ${stats['total_pnl']:,.2f}")
                    print(f"  Win Rate: {stats['win_rate']}%")
                    print(f"  Avg PnL: ${stats['avg_pnl']:,.2f}")

            input("\nPress Enter to continue...")

        elif choice == '2':
            self.display_header()
            print("\n🎯 PER KEY LEVEL STATISTICS")
            print("=" * 60)

            # Get statistics for all levels
            all_stats = self.db.get_level_statistics()

            if all_stats:
                # Sort by win rate (best first)
                sorted_stats = sorted(all_stats, key=lambda x: x['win_rate'], reverse=True)

                print("\nBest Performing Levels:")
                print("-" * 60)
                for i, stat in enumerate(sorted_stats[:5], 1):
                    print(f"{i}. {stat['level']:15} | Win Rate: {stat['win_rate']:5.1f}% | "
                          f"Trades: {stat['trade_count']:3} | Total PnL: ${stat['total_pnl']:7.2f}")

                print("\nWorst Performing Levels:")
                print("-" * 60)
                for i, stat in enumerate(sorted_stats[-5:], 1):
                    print(f"{i}. {stat['level']:15} | Win Rate: {stat['win_rate']:5.1f}% | "
                          f"Trades: {stat['trade_count']:3} | Total PnL: ${stat['total_pnl']:7.2f}")
            else:
                print("\nNo level statistics available")

            input("\nPress Enter to continue...")

    def export_menu(self):
        """Data export menu"""
        self.display_header()
        print("\n📤 DATA EXPORT")
        print("=" * 60)

        print("1. Export all trades (CSV)")
        print("2. Export key levels (CSV)")
        print("3. Export statistics (CSV)")
        print("4. Backup database")
        print("5. Back")

        choice = input("\nSelect: ").strip()

        if choice == '1':
            filename = self.db.export_trades_csv()
            print(f"\n✅ Trades exported to {filename}")
            input("\nPress Enter to continue...")

        elif choice == '2':
            filename = self.db.export_key_levels_csv()
            print(f"\n✅ Key levels exported to {filename}")
            input("\nPress Enter to continue...")

    def main_menu(self):
        """Main menu loop"""
        while self.running:
            self.display_dashboard()

            print("\nMAIN MENU:")
            print("1. 📥 Import Trades")
            print("2. 🎯 Manage Key Levels")
            print("3. 📈 Advanced Analytics")
            print("4. 📤 Export Data")
            print("5. ⚙️ Settings")
            print("0. Exit")

            choice = input("\nSelect option: ").strip()

            if choice == '1':
                self.import_menu()
            elif choice == '2':
                self.key_levels_menu()
            elif choice == '3':
                self.analytics_menu()
            elif choice == '4':
                self.export_menu()
            elif choice == '0':
                print("\n✅ Goodbye! Happy trading! 📈")
                self.running = False
            else:
                print("\n❌ Invalid option!")
                input("Press Enter to continue...")


def main():
    """Main entry point"""
    journal = ProfessionalJournal()

    try:
        journal.main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()