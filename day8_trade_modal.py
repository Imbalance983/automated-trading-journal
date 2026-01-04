# day8_trade_modal.py - ORIGINAL COMPLETE VERSION
import sqlite3
import pandas as pd
from datetime import datetime


class TradeJournalModal:
    def __init__(self, db_path="trading_journal.db"):
        self.db_path = db_path
        self.setup_emotional_states()
        self.setup_trade_setups()
        self.ensure_database_ready()

    def ensure_database_ready(self):
        """Make sure database has required columns"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check columns
            cursor.execute("PRAGMA table_info(trades)")
            columns = [col[1] for col in cursor.fetchall()]

            has_pnl_percent = 'pnl_percent' in columns
            has_notes = 'notes' in columns

            if not has_pnl_percent or not has_notes:
                print("⚠️  Updating database structure...")

                if not has_pnl_percent:
                    cursor.execute("ALTER TABLE trades ADD COLUMN pnl_percent REAL")
                    # Calculate pnl_percent for existing trades
                    cursor.execute("SELECT id, entry_price, quantity, pnl FROM trades")
                    trades = cursor.fetchall()
                    for trade in trades:
                        trade_id, entry_price, quantity, pnl = trade
                        if entry_price > 0 and quantity > 0:
                            pnl_percent = (pnl / (entry_price * quantity)) * 100
                        else:
                            pnl_percent = 0
                        cursor.execute("UPDATE trades SET pnl_percent = ? WHERE id = ?",
                                       (pnl_percent, trade_id))
                    print("✅ Added pnl_percent column")

                if not has_notes:
                    cursor.execute("ALTER TABLE trades ADD COLUMN notes TEXT")
                    cursor.execute("UPDATE trades SET notes = '' WHERE notes IS NULL")
                    print("✅ Added notes column")

                conn.commit()

            conn.close()
        except Exception as e:
            print(f"⚠️ Database check: {e}")

    def setup_emotional_states(self):
        """Define emotional state options"""
        self.emotional_states = [
            "Confident",
            "Nervous",
            "Calm",
            "Frustrated",
            "Excited",
            "Patient",
            "Impulsive",
            "Focused",
            "Distracted",
            "Uncertain"
        ]

    def setup_trade_setups(self):
        """Define trade setup classifications"""
        self.trade_setups = [
            "Breakout",
            "Pullback",
            "Trend Following",
            "Range Trade",
            "Reversal",
            "News Trade",
            "Scalping",
            "Swing Trade",
            "Position Trade",
            "Mean Reversion"
        ]

    def display_trade_modal(self, trade_id=None):
        """Display a modal for viewing/editing trade details"""
        print("\n" + "=" * 60)
        print("📊 TRADE DETAILS MODAL")
        print("=" * 60)

        if trade_id:
            trade = self.get_trade_by_id(trade_id)
            if trade:
                self.display_existing_trade(trade)
            else:
                print(f"❌ Trade ID {trade_id} not found")
                return False
        else:
            self.display_new_trade_form()

        print("=" * 60)
        return True

    def get_trade_by_id(self, trade_id):
        """Retrieve a trade from database by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, date, symbol, side, entry_price, exit_price, 
                       quantity, pnl, pnl_percent, notes
                FROM trades 
                WHERE id = ?
            """, (trade_id,))

            trade = cursor.fetchone()
            conn.close()

            if trade:
                return {
                    'id': trade[0],
                    'date': trade[1],
                    'symbol': trade[2],
                    'side': trade[3],
                    'entry_price': trade[4],
                    'exit_price': trade[5],
                    'quantity': trade[6],
                    'pnl': trade[7],
                    'pnl_percent': trade[8] if trade[8] is not None else 0,
                    'notes': trade[9] if trade[9] else ""
                }
        except Exception as e:
            print(f"❌ Error fetching trade: {e}")

        return None

    def display_existing_trade(self, trade):
        """Display existing trade with edit options"""
        print(f"Trade ID: {trade['id']}")
        print(f"Date: {trade['date']}")
        print(f"Symbol: {trade['symbol']}")
        print(f"Side: {trade['side']}")
        print(f"Entry: ${trade['entry_price']:.2f} | Exit: ${trade['exit_price']:.2f}")
        print(f"Quantity: {trade['quantity']}")
        print(f"P&L: ${trade['pnl']:.2f} ({trade['pnl_percent']:.2f}%)")

        if trade['notes']:
            print("\n📝 Current Notes:")
            print("-" * 40)
            print(trade['notes'])
            print("-" * 40)

        # Show edit options
        print("\n🛠 EDIT OPTIONS:")
        print("1. Edit Notes")
        print("2. Add Emotional State")
        print("3. Classify Trade Setup")
        print("4. Link to Key Levels")
        print("5. Add Screenshots")
        print("6. Save and Close")
        print("0. Cancel")

        choice = input("\nSelect option (0-6): ").strip()

        if choice == "1":
            self.edit_trade_notes(trade)
        elif choice == "2":
            self.add_emotional_state(trade)
        elif choice == "3":
            self.classify_trade_setup(trade)
        elif choice == "4":
            self.link_key_levels(trade)
        elif choice == "5":
            self.add_screenshots(trade)
        elif choice == "6":
            print("✅ Changes saved!")
            return True

        return False

    def display_new_trade_form(self):
        """Display form for new trade entry"""
        print("\n➕ NEW TRADE ENTRY")
        print("-" * 40)

        # Collect basic trade info
        trade_data = {}
        trade_data['date'] = input("Date (YYYY-MM-DD): ").strip() or datetime.now().strftime("%Y-%m-%d")
        trade_data['symbol'] = input("Symbol (e.g., BTCUSDT): ").strip().upper()
        trade_data['side'] = input("Side (Long/Short): ").strip().capitalize()

        try:
            trade_data['entry_price'] = float(input("Entry Price: ").strip() or 0)
            trade_data['exit_price'] = float(input("Exit Price: ").strip() or 0)
            trade_data['quantity'] = float(input("Quantity: ").strip() or 0)
        except ValueError:
            print("❌ Please enter valid numbers for prices and quantity")
            return

        # Calculate P&L
        if trade_data['side'].lower() == 'long':
            pnl = (trade_data['exit_price'] - trade_data['entry_price']) * trade_data['quantity']
        else:
            pnl = (trade_data['entry_price'] - trade_data['exit_price']) * trade_data['quantity']

        # Calculate P&L percentage
        if trade_data['entry_price'] > 0 and trade_data['quantity'] > 0:
            pnl_percent = (pnl / (trade_data['entry_price'] * trade_data['quantity'])) * 100
        else:
            pnl_percent = 0

        trade_data['pnl'] = pnl
        trade_data['pnl_percent'] = pnl_percent

        print(f"\n💰 Calculated P&L: ${pnl:.2f} ({pnl_percent:.2f}%)")

        # Additional details
        print("\n📝 ADDITIONAL DETAILS:")
        print("1. Add Notes")
        print("2. Add Emotional State")
        print("3. Classify Trade Setup")
        print("4. Link to Key Levels")
        print("5. Skip to Save")

        choice = input("\nSelect option (1-5): ").strip()

        trade_data['notes'] = ""
        if choice == "1":
            trade_data['notes'] = self.get_rich_notes()
        if choice == "2":
            emotional_state = self.select_emotional_state()
            if emotional_state:
                trade_data['notes'] += f"\nEmotional State: {emotional_state}\n"
        if choice == "3":
            trade_setup = self.select_trade_setup()
            if trade_setup:
                trade_data['notes'] += f"\nTrade Setup: {trade_setup}\n"
        if choice == "4":
            trade_data['key_levels'] = self.select_key_levels()
        else:
            trade_data['key_levels'] = []

        # Save the trade
        save_choice = input("\n💾 Save this trade? (y/n): ").strip().lower()
        if save_choice == 'y':
            trade_id = self.save_new_trade(trade_data)
            if trade_id:
                print(f"✅ Trade #{trade_id} saved successfully!")
            else:
                print("❌ Failed to save trade")
        else:
            print("❌ Trade not saved")

    def get_rich_notes(self):
        """Get rich text notes with markdown support"""
        print("\n📝 RICH NOTES EDITOR")
        print("-" * 40)
        print("Supports markdown: **bold**, *italic*, - lists, # headers")
        print("Type your notes (press Enter twice to finish):")
        print("-" * 40)

        notes_lines = []
        while True:
            line = input()
            if line == "":
                if notes_lines and notes_lines[-1] == "":
                    notes_lines.pop()
                    break
            notes_lines.append(line)

        return "\n".join(notes_lines)

    def select_emotional_state(self):
        """Let user select emotional state"""
        print("\n😊 EMOTIONAL STATE")
        print("-" * 40)
        for i, state in enumerate(self.emotional_states, 1):
            print(f"{i}. {state}")

        while True:
            try:
                choice = int(input(f"\nSelect emotional state (1-{len(self.emotional_states)}): ").strip())
                if 1 <= choice <= len(self.emotional_states):
                    return self.emotional_states[choice - 1]
                else:
                    print("❌ Invalid choice. Try again.")
            except ValueError:
                print("❌ Please enter a number.")
                return None

    def select_trade_setup(self):
        """Let user select trade setup classification"""
        print("\n📈 TRADE SETUP CLASSIFICATION")
        print("-" * 40)
        for i, setup in enumerate(self.trade_setups, 1):
            print(f"{i}. {setup}")

        while True:
            try:
                choice = int(input(f"\nSelect trade setup (1-{len(self.trade_setups)}): ").strip())
                if 1 <= choice <= len(self.trade_setups):
                    return self.trade_setups[choice - 1]
                else:
                    print("❌ Invalid choice. Try again.")
            except ValueError:
                print("❌ Please enter a number.")
                return None

    def select_key_levels(self):
        """Let user select key levels to link"""
        print("\n📍 LINK KEY LEVELS")
        print("-" * 40)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, strength FROM key_levels ORDER BY strength DESC")
            levels = cursor.fetchall()
            conn.close()
            if not levels:
                print("⚠️ No key levels found in database.")
                return []

            print("Available Key Levels:")
            for level in levels:
                stars = "★" * level[2] + "☆" * (5 - level[2])
                print(f"{level[0]}. {level[1]} {stars}")

            print("\nEnter level IDs separated by commas (e.g., 1,3,5)")
            print("Press Enter to skip")

            selection = input("Selection: ").strip()
            if not selection:
                return []

            selected_ids = []
            for id_str in selection.split(","):
                id_str = id_str.strip()
                if id_str.isdigit():
                    selected_ids.append(int(id_str))

            return selected_ids

        except Exception as e:
            print(f"❌ Error fetching key levels: {e}")
            return []

    def save_new_trade(self, trade_data):
        """Save new trade to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO trades 
                (date, symbol, side, entry_price, exit_price, quantity, pnl, pnl_percent, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_data['date'],
                trade_data['symbol'],
                trade_data['side'],
                trade_data['entry_price'],
                trade_data['exit_price'],
                trade_data['quantity'],
                trade_data['pnl'],
                trade_data['pnl_percent'],
                trade_data.get('notes', '')
            ))

            trade_id = cursor.lastrowid

            # Link key levels if provided
            if 'key_levels' in trade_data and trade_data['key_levels']:
                for level_id in trade_data['key_levels']:
                    cursor.execute("""
                        INSERT INTO trade_key_levels (trade_id, key_level_id)
                        VALUES (?, ?)
                    """, (trade_id, level_id))

            conn.commit()
            conn.close()

            return trade_id

        except Exception as e:
            print(f"❌ Error saving trade: {e}")
            return None

    def edit_trade_notes(self, trade):
        """Edit trade notes"""
        print("\n✏️ EDIT NOTES")
        print("-" * 40)
        new_notes = self.get_rich_notes()

        if new_notes:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("UPDATE trades SET notes = ? WHERE id = ?",
                               (new_notes, trade['id']))
                conn.commit()
                conn.close()
                print("✅ Notes updated successfully!")
                trade['notes'] = new_notes
            except Exception as e:
                print(f"❌ Error updating notes: {e}")

    def add_emotional_state(self, trade):
        """Add emotional state to existing trade"""
        emotional_state = self.select_emotional_state()
        if emotional_state:
            current_notes = trade.get('notes', '')
            updated_notes = f"Emotional State: {emotional_state}\n\n{current_notes}"

            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("UPDATE trades SET notes = ? WHERE id = ?",
                               (updated_notes, trade['id']))
                conn.commit()
                conn.close()
                print(f"✅ Added emotional state: {emotional_state}")
                trade['notes'] = updated_notes
            except Exception as e:
                print(f"❌ Error adding emotional state: {e}")

    def classify_trade_setup(self, trade):
        """Classify trade setup for existing trade"""
        trade_setup = self.select_trade_setup()
        if trade_setup:
            current_notes = trade.get('notes', '')
            updated_notes = f"Trade Setup: {trade_setup}\n\n{current_notes}"

            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("UPDATE trades SET notes = ? WHERE id = ?",
                               (updated_notes, trade['id']))
                conn.commit()
                conn.close()
                print(f"✅ Classified as: {trade_setup}")
                trade['notes'] = updated_notes
            except Exception as e:
                print(f"❌ Error classifying trade: {e}")

    def link_key_levels(self, trade):
        """Link key levels to existing trade"""
        selected_ids = self.select_key_levels()
        if selected_ids:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Remove existing links
                cursor.execute("DELETE FROM trade_key_levels WHERE trade_id = ?", (trade['id'],))

                # Add new links
                for level_id in selected_ids:
                    cursor.execute("""
                        INSERT INTO trade_key_levels (trade_id, key_level_id)
                        VALUES (?, ?)
                    """, (trade['id'], level_id))

                conn.commit()
                conn.close()
                print(f"✅ Linked {len(selected_ids)} key level(s) to trade")

            except Exception as e:
                print(f"❌ Error linking key levels: {e}")

    def add_screenshots(self, trade):
        """Add screenshot references to trade"""
        print("\n🖼️ SCREENSHOT SYSTEM")
        print("-" * 40)
        print("1. Enter screenshot filenames")
        print("2. List existing screenshots")
        print("3. Back to menu")

        choice = input("\nSelect option (1-3): ").strip()

        if choice == "1":
            self.upload_screenshots(trade)
        elif choice == "2":
            self.list_screenshots(trade)

    def upload_screenshots(self, trade):
        """Handle screenshot upload (filename entry)"""
        print("\n📤 ENTER SCREENSHOT FILENAMES")
        print("-" * 40)
        print("Enter one filename per line (e.g., 'chart_breakout.png')")
        print("Press Enter on an empty line to finish:")
        print("-" * 40)

        screenshots = []
        empty_count = 0

        while True:
            filename = input("Filename: ").strip()

            if filename == "":
                empty_count += 1
                if empty_count >= 1:  # Changed from 2 to 1
                    break
            else:
                empty_count = 0  # Reset empty count if user enters something
                screenshots.append(filename)

        if screenshots:
            current_notes = trade.get('notes', '')
            screenshots_text = "\n📸 SCREENSHOTS:\n" + "\n".join([f"- {ss}" for ss in screenshots])
            updated_notes = f"{current_notes}\n\n{screenshots_text}" if current_notes else screenshots_text

            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("UPDATE trades SET notes = ? WHERE id = ?",
                               (updated_notes, trade['id']))
                conn.commit()
                conn.close()
                print(f"✅ Added {len(screenshots)} screenshot(s)")
                trade['notes'] = updated_notes
            except Exception as e:
                print(f"❌ Error adding screenshots: {e}")
        else:
            print("⚠️ No screenshots added")



        if screenshots:
            current_notes = trade.get('notes', '')
            screenshots_text = "\n📸 SCREENSHOTS:\n" + "\n".join([f"- {ss}" for ss in screenshots])
            updated_notes = f"{current_notes}\n\n{screenshots_text}" if current_notes else screenshots_text

            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("UPDATE trades SET notes = ? WHERE id = ?",
                               (updated_notes, trade['id']))
                conn.commit()
                conn.close()
                print(f"✅ Added {len(screenshots)} screenshot(s)")
                trade['notes'] = updated_notes
            except Exception as e:
                print(f"❌ Error adding screenshots: {e}")

    def list_screenshots(self, trade):
        """List screenshots linked to trade"""
        if trade.get('notes') and '📸 SCREENSHOTS:' in trade['notes']:
            print("\n📸 ATTACHED SCREENSHOTS:")
            print("-" * 40)
            notes = trade['notes']
            start_idx = notes.find('📸 SCREENSHOTS:')
            if start_idx != -1:
                screenshot_section = notes[start_idx:]
                lines = screenshot_section.split('\n')
                for line in lines[1:]:
                    if line.strip().startswith('-'):
                        print(f"  {line.strip()}")
        else:
            print("⚠️ No screenshots attached to this trade")

    def view_all_trades(self):
        """Display all trades in a table"""
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("""
                SELECT id, date, symbol, side, entry_price, exit_price, 
                       quantity, pnl, pnl_percent 
                FROM trades 
                ORDER BY date DESC
            """, conn)
            conn.close()

            print("\n" + "=" * 80)
            print("📊 ALL TRADES")
            print("=" * 80)

            if df.empty:
                print("No trades found in database.")
                input("\nPress Enter to continue...")
                return

            pd.set_option('display.max_rows', None)
            pd.set_option('display.width', None)

            # Display in pages if there are many trades
            if len(df) > 20:
                print("📄 Displaying first 20 trades (scroll with arrow keys):")
                print(df.head(20).to_string(index=False))
            else:
                print(df.to_string(index=False))

            # Show summary
            total_trades = len(df)
            winning_trades = len(df[df['pnl'] > 0])
            losing_trades = len(df[df['pnl'] < 0])
            total_pnl = df['pnl'].sum()
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

            print("\n" + "=" * 80)
            print(f"📈 SUMMARY:")
            print(f"Total Trades: {total_trades}")
            print(f"Winning Trades: {winning_trades}")
            print(f"Losing Trades: {losing_trades}")
            print(f"Win Rate: {win_rate:.1f}%")

            # Color code the P&L
            if total_pnl > 0:
                print(f"💰 Total P&L: +${total_pnl:.2f} (PROFIT)")
            elif total_pnl < 0:
                print(f"📉 Total P&L: ${total_pnl:.2f} (LOSS)")
            else:
                print(f"➖ Total P&L: ${total_pnl:.2f} (BREAK EVEN)")

            print("=" * 80)

            # PAUSE so user can read
            input("\nPress Enter to return to main menu...")

        except Exception as e:
            print(f"❌ Error displaying trades: {e}")
            input("\nPress Enter to continue...")


def main():
    """Main function to run the trade modal system"""
    journal = TradeJournalModal()

    print("\n" + "=" * 60)
    print("📊 TRADE JOURNAL MODAL SYSTEM - DAY 8")
    print("=" * 60)

    while True:
        print("\n📋 MAIN MENU:")
        print("1. View/Edit Existing Trade")
        print("2. Enter New Trade")
        print("3. View All Trades")
        print("4. Exit")

        choice = input("\nSelect option (1-4): ").strip()

        if choice == "1":
            try:
                trade_id = int(input("Enter Trade ID: ").strip())
                journal.display_trade_modal(trade_id)
            except ValueError:
                print("❌ Please enter a valid trade ID number")

        elif choice == "2":
            journal.display_trade_modal()  # No ID = new trade

        elif choice == "3":
            journal.view_all_trades()

        elif choice == "4":
            print("\n👋 Goodbye!")
            break

        else:
            print("❌ Invalid choice. Please select 1-4.")


if __name__ == "__main__":
    main()