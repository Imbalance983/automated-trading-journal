# day9_analytics.py - COMPLETE FINAL VERSION
# Day 9: Advanced Analytics & Reporting

import numpy as np
import csv


class TradingAnalytics:
    def __init__(self, db_path='trading_journal.db'):
        """Initialize analytics with database connection"""
        self.db_path = db_path

    def connect(self):
        """Connect to database"""
        import sqlite3
        return sqlite3.connect(self.db_path)

    def show_all_tables(self):
        """Show all tables and their structure"""
        conn = self.connect()
        cursor = conn.cursor()

        print("=== ALL DATABASE TABLES ===")

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
            print(f"\n📊 Table: {table_name}")

            # Get columns for this table
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            for col in columns:
                print(f"  - {col[1]} ({col[2]})")

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  Rows: {count}")

        conn.close()

    def add_missing_columns(self):
        """Add emotional_state and setup_classification columns if missing"""
        conn = self.connect()
        cursor = conn.cursor()

        print("=== ADDING MISSING COLUMNS ===")

        # Check if emotional_state exists
        cursor.execute("PRAGMA table_info(trades)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'emotional_state' not in columns:
            print("Adding emotional_state column...")
            cursor.execute("ALTER TABLE trades ADD COLUMN emotional_state TEXT")
            print("✅ emotional_state column added")

        if 'setup_classification' not in columns:
            print("Adding setup_classification column...")
            cursor.execute("ALTER TABLE trades ADD COLUMN setup_classification TEXT")
            print("✅ setup_classification column added")

        conn.commit()
        conn.close()
        print("Done!")

    def simple_verification(self):
        """Simple verification for Day 9 analytics"""
        conn = self.connect()
        cursor = conn.cursor()

        print("=== SIMPLE DATABASE VERIFICATION ===")

        # Check trade count
        cursor.execute("SELECT COUNT(*) FROM trades")
        trade_count = cursor.fetchone()[0]
        print(f"✅ {trade_count} trades in database")

        # Check if we have any emotional_state data
        cursor.execute("SELECT COUNT(*) FROM trades WHERE emotional_state IS NOT NULL AND emotional_state != ''")
        emotional_count = cursor.fetchone()[0]
        print(f"✅ {emotional_count} trades with emotional state recorded")

        # Check if we have any setup_classification data
        cursor.execute(
            "SELECT COUNT(*) FROM trades WHERE setup_classification IS NOT NULL AND setup_classification != ''")
        setup_count = cursor.fetchone()[0]
        print(f"✅ {setup_count} trades with setup classification recorded")

        # Check key levels
        cursor.execute("SELECT COUNT(*) FROM key_levels")
        key_levels_count = cursor.fetchone()[0]
        print(f"✅ {key_levels_count} key levels in database")

        # Check trade-key level links
        cursor.execute("SELECT COUNT(*) FROM trade_key_levels")
        links_count = cursor.fetchone()[0]
        print(f"✅ {links_count} trade-key level links")

        conn.close()

    def add_sample_analytics_data(self):
        """Add sample emotional state and setup classification data for testing"""
        conn = self.connect()
        cursor = conn.cursor()

        print("=== ADDING SAMPLE ANALYTICS DATA ===")

        # Sample emotional states and setups for testing
        emotional_states = ['Confident', 'Nervous', 'Calm', 'Excited', 'Fearful', 'Patient', 'Impulsive', 'Disciplined']
        setup_classifications = ['Breakout', 'Pullback', 'Trend Following', 'Reversal', 'Range Bound',
                                 'Scalping', 'Swing Trade', 'Position Trade']

        # Update first 8 trades with sample data
        for i in range(1, 9):
            emotional = emotional_states[(i - 1) % len(emotional_states)]
            setup = setup_classifications[(i - 1) % len(setup_classifications)]

            cursor.execute("""
                UPDATE trades 
                SET emotional_state = ?, setup_classification = ?
                WHERE id = ?
            """, (emotional, setup, i))

            print(f"Trade {i}: {emotional} / {setup}")

        conn.commit()

        # Verify the updates
        cursor.execute("SELECT COUNT(*) FROM trades WHERE emotional_state IS NOT NULL")
        updated_count = cursor.fetchone()[0]

        print(f"\n✅ {updated_count} trades updated with sample data")
        conn.close()

    def emotional_state_analysis(self):
        """Analyze performance by emotional state"""
        conn = self.connect()
        cursor = conn.cursor()

        print("\n😊 P&L BY EMOTIONAL STATE")
        print("-" * 40)

        cursor.execute("""
            SELECT emotional_state,
                   COUNT(*) as total_trades,
                   SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                   SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losses,
                   SUM(pnl) as total_pnl,
                   AVG(pnl) as avg_pnl,
                   AVG(pnl_percent) as avg_pnl_percent
            FROM trades
            WHERE emotional_state IS NOT NULL AND emotional_state != ''
            GROUP BY emotional_state
            ORDER BY total_pnl DESC
        """)

        emotional_states = cursor.fetchall()

        if emotional_states:
            print(f"{'Emotional State':15} | {'Trades':6} | {'Wins':4} | {'Losses':6} | "
                  f"{'Total P&L':10} | {'Avg P&L':9} | {'Avg %':6}")
            print("-" * 90)

            for state in emotional_states:
                state_name, total, wins, losses, total_pnl, avg_pnl, avg_percent = state
                total_pnl = total_pnl or 0
                avg_pnl = avg_pnl or 0
                avg_percent = avg_percent or 0

                print(f"{state_name:15} | {total:6} | {wins:4} | {losses:6} | "
                      f"${total_pnl:8.2f} | ${avg_pnl:7.2f} | {avg_percent:5.1f}%")
        else:
            print("No emotional state data available")

        conn.close()

    def key_level_effectiveness(self):
        """Analyze effectiveness of key levels"""
        conn = self.connect()
        cursor = conn.cursor()

        print("\n📍 KEY LEVEL EFFECTIVENESS ANALYSIS")
        print("-" * 40)

        # Get trades linked to key levels
        cursor.execute("""
            SELECT 
                kl.name as key_level,
                kl.strength,
                COUNT(DISTINCT t.id) as total_trades,
                SUM(CASE WHEN t.pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN t.pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                AVG(t.pnl) as avg_pnl,
                SUM(t.pnl) as total_pnl
            FROM key_levels kl
            LEFT JOIN trade_key_levels tkl ON kl.id = tkl.key_level_id
            LEFT JOIN trades t ON tkl.trade_id = t.id
            WHERE t.id IS NOT NULL
            GROUP BY kl.id, kl.name, kl.strength
            ORDER BY total_pnl DESC
        """)

        key_levels = cursor.fetchall()

        if key_levels:
            print(f"{'Key Level':25} | {'Strength':8} | {'Trades':6} | {'Wins':4} | {'Losses':6} | "
                  f"{'Avg P&L':9} | {'Total P&L':10}")
            print("-" * 95)

            for level in key_levels:
                name, strength, total, wins, losses, avg_pnl, total_pnl = level
                avg_pnl = avg_pnl or 0
                total_pnl = total_pnl or 0

                # Convert strength to stars
                stars = "★" * strength + "☆" * (5 - strength)

                print(f"{name:25} | {stars:8} | {total:6} | {wins:4} | {losses:6} | "
                      f"${avg_pnl:7.2f} | ${total_pnl:8.2f}")
        else:
            print("No trades linked to key levels yet")
            print("\nAvailable key levels:")
            cursor.execute("SELECT name, strength FROM key_levels")
            all_levels = cursor.fetchall()
            for level in all_levels:
                name, strength = level
                stars = "★" * strength + "☆" * (5 - strength)
                print(f"  {name:25} | {stars}")

        conn.close()

    def advanced_statistics(self):
        """Calculate advanced trading statistics"""
        conn = self.connect()
        cursor = conn.cursor()

        print("\n📊 ADVANCED TRADING STATISTICS")
        print("-" * 40)

        # Get all P&L values
        cursor.execute("SELECT pnl FROM trades WHERE pnl IS NOT NULL")
        pnl_values = [row[0] for row in cursor.fetchall()]

        if not pnl_values:
            print("No P&L data available")
            conn.close()
            return

        # Convert to numpy array for calculations
        pnl_array = np.array(pnl_values)

        # 1. Average Win/Loss Ratio
        winning_trades = pnl_array[pnl_array > 0]
        losing_trades = pnl_array[pnl_array < 0]

        avg_win = np.mean(winning_trades) if len(winning_trades) > 0 else 0
        avg_loss = abs(np.mean(losing_trades)) if len(losing_trades) > 0 else 0

        win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else float('inf')

        print(f"Average Win/Loss Ratio: {win_loss_ratio:.2f}:1")
        print(f"Average Win: ${avg_win:.2f}")
        print(f"Average Loss: ${avg_loss:.2f}")

        # 2. Maximum Drawdown
        cumulative = np.cumsum(pnl_array)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = running_max - cumulative
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0

        print(f"Maximum Drawdown: ${max_drawdown:.2f}")

        # 3. Profit Factor
        total_profits = np.sum(winning_trades)
        total_losses = abs(np.sum(losing_trades))
        profit_factor = total_profits / total_losses if total_losses > 0 else float('inf')

        print(f"Profit Factor: {profit_factor:.2f}")

        # 4. Consecutive Wins/Losses
        signs = np.sign(pnl_array)
        current_streak = 0
        max_win_streak = 0
        max_loss_streak = 0

        for sign in signs:
            if sign > 0:  # Win
                current_streak = max(current_streak, 0) + 1
                max_win_streak = max(max_win_streak, current_streak)
            elif sign < 0:  # Loss
                current_streak = min(current_streak, 0) - 1
                max_loss_streak = min(max_loss_streak, current_streak)

        max_loss_streak = abs(max_loss_streak)

        print(f"Longest Win Streak: {max_win_streak} trades")
        print(f"Longest Loss Streak: {max_loss_streak} trades")

        # 5. Expectancy
        win_rate = len(winning_trades) / len(pnl_array)
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

        print(f"System Expectancy: ${expectancy:.2f} per trade")

        # 6. Sharpe Ratio (simplified - using P&L as returns)
        if len(pnl_array) > 1:
            returns = pnl_array
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = avg_return / std_return if std_return > 0 else 0
            print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
        else:
            print("Sharpe Ratio: Need more trades to calculate")

        conn.close()

    def export_to_csv(self, filename='trading_report.csv'):
        """Export trading data to CSV file"""
        conn = self.connect()
        cursor = conn.cursor()

        print(f"\n💾 EXPORTING DATA TO CSV: {filename}")
        print("-" * 40)

        # Get all trades with their data
        cursor.execute("""
            SELECT 
                t.id,
                t.symbol,
                t.side,
                t.entry_price,
                t.exit_price,
                t.quantity,
                t.pnl,
                t.pnl_percent,
                t.entry_time,
                t.exit_time,
                t.date,
                t.emotional_state,
                t.setup_classification,
                t.notes,
                GROUP_CONCAT(kl.name, ', ') as key_levels
            FROM trades t
            LEFT JOIN trade_key_levels tkl ON t.id = tkl.trade_id
            LEFT JOIN key_levels kl ON tkl.key_level_id = kl.id
            GROUP BY t.id
            ORDER BY t.entry_time
        """)

        trades = cursor.fetchall()

        if not trades:
            print("No trades to export")
            conn.close()
            return False

        # Define CSV headers
        headers = ['ID', 'Symbol', 'Side', 'Entry Price', 'Exit Price', 'Quantity',
                   'P&L', 'P&L %', 'Entry Time', 'Exit Time', 'Date',
                   'Emotional State', 'Setup Classification', 'Notes', 'Key Levels']

        # Write to CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)

            for trade in trades:
                writer.writerow(trade)

        print(f"✅ Exported {len(trades)} trades to {filename}")

        # Also export a summary report
        summary_filename = 'trading_summary.csv'
        self.export_summary_to_csv(summary_filename)

        conn.close()
        return True

    def export_summary_to_csv(self, filename='trading_summary.csv'):
        """Export summary statistics to CSV"""
        print(f"\n📊 EXPORTING SUMMARY TO CSV: {filename}")
        print("-" * 40)

        # Calculate summary statistics
        conn = self.connect()
        cursor = conn.cursor()

        # Basic stats
        cursor.execute("SELECT COUNT(*) FROM trades")
        total_trades = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM trades WHERE pnl > 0")
        winning_trades = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(pnl) FROM trades")
        total_pnl = cursor.fetchone()[0] or 0

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # Setup classification stats
        cursor.execute("""
            SELECT setup_classification, COUNT(*), AVG(pnl)
            FROM trades 
            WHERE setup_classification IS NOT NULL 
            GROUP BY setup_classification
        """)
        setup_stats = cursor.fetchall()

        # Emotional state stats
        cursor.execute("""
            SELECT emotional_state, COUNT(*), AVG(pnl)
            FROM trades 
            WHERE emotional_state IS NOT NULL 
            GROUP BY emotional_state
        """)
        emotion_stats = cursor.fetchall()

        # Write summary CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Overall summary
            writer.writerow(['CATEGORY', 'METRIC', 'VALUE'])
            writer.writerow(['Overall', 'Total Trades', total_trades])
            writer.writerow(['Overall', 'Winning Trades', winning_trades])
            writer.writerow(['Overall', 'Win Rate', f'{win_rate:.1f}%'])
            writer.writerow(['Overall', 'Total P&L', f'${total_pnl:.2f}'])
            writer.writerow([])  # Empty row

            # Setup classification
            writer.writerow(['SETUP CLASSIFICATION', 'TRADE COUNT', 'AVG P&L'])
            for setup, count, avg_pnl in setup_stats:
                writer.writerow([setup, count, f'${avg_pnl:.2f}' if avg_pnl else '$0.00'])
            writer.writerow([])  # Empty row

            # Emotional state
            writer.writerow(['EMOTIONAL STATE', 'TRADE COUNT', 'AVG P&L'])
            for emotion, count, avg_pnl in emotion_stats:
                writer.writerow([emotion, count, f'${avg_pnl:.2f}' if avg_pnl else '$0.00'])

        print(f"✅ Exported summary report to {filename}")
        conn.close()

    def performance_dashboard(self):
        """Display complete performance analytics dashboard"""
        conn = self.connect()

        print("=" * 60)
        print("📊 PERFORMANCE ANALYTICS DASHBOARD")
        print("=" * 60)

        # 1. Basic Performance Metrics
        print("\n📈 BASIC PERFORMANCE METRICS")
        print("-" * 40)

        # Total trades
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM trades")
        total_trades = cursor.fetchone()[0]

        # Winning trades
        cursor.execute("SELECT COUNT(*) FROM trades WHERE pnl > 0")
        winning_trades = cursor.fetchone()[0]

        # Losing trades
        cursor.execute("SELECT COUNT(*) FROM trades WHERE pnl < 0")
        losing_trades = cursor.fetchone()[0]

        # Total P&L
        cursor.execute("SELECT SUM(pnl) FROM trades")
        total_pnl = cursor.fetchone()[0] or 0

        # Win rate
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        print(f"Total Trades: {total_trades}")
        print(f"Winning Trades: {winning_trades}")
        print(f"Losing Trades: {losing_trades}")
        print(f"Win Rate: {win_rate:.1f}%")
        print(f"Total P&L: ${total_pnl:.2f}")

        # 2. Win Rate by Trade Setup Type
        print("\n🎯 WIN RATE BY TRADE SETUP TYPE")
        print("-" * 40)

        cursor.execute("""
            SELECT setup_classification,
                   COUNT(*) as total_trades,
                   SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                   AVG(CASE WHEN pnl > 0 THEN pnl ELSE NULL END) as avg_win,
                   AVG(CASE WHEN pnl < 0 THEN pnl ELSE NULL END) as avg_loss
            FROM trades
            WHERE setup_classification IS NOT NULL AND setup_classification != ''
            GROUP BY setup_classification
            ORDER BY wins DESC
        """)

        setups = cursor.fetchall()

        if setups:
            for setup in setups:
                setup_name, total, wins, avg_win, avg_loss = setup
                win_rate_setup = (wins / total * 100) if total > 0 else 0
                avg_win = avg_win or 0
                avg_loss = avg_loss or 0

                print(f"{setup_name:20} | Trades: {total:2} | Win Rate: {win_rate_setup:5.1f}% | "
                      f"Avg Win: ${avg_win:7.2f} | Avg Loss: ${avg_loss:7.2f}")
        else:
            print("No setup classification data available")

        conn.close()

        # 3. Emotional State Analysis
        self.emotional_state_analysis()

        # 4. Key Level Effectiveness Analysis
        self.key_level_effectiveness()

        # 5. Advanced Statistics
        self.advanced_statistics()

        # 6. Export option reminder
        print("\n💾 DATA EXPORT OPTIONS")
        print("-" * 40)
        print("Use analytics.export_to_csv() to export full data")
        print("Files created: trading_report.csv & trading_summary.csv")