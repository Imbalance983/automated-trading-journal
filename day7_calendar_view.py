# day7_simple_calendar.py
# Day 7: Calendar View & Database Enhancement (Simple Version)

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import calendar
import random
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import webbrowser


def create_html_calendar(trades_df, year, month):
    """Create HTML calendar with trade data"""
    cal = calendar.Calendar()
    month_days = cal.monthdayscalendar(year, month)

    # Calculate daily P&L
    trades_df['date_only'] = trades_df['date'].dt.date
    daily_pnl = trades_df.groupby('date_only').agg({
        'pnl': 'sum',
        'id': 'count'
    }).rename(columns={'id': 'trade_count', 'pnl': 'daily_pnl'})

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trading Calendar - {calendar.month_name[month]} {year}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .calendar {{ width: 100%; max-width: 900px; margin: 0 auto; }}
            .month-header {{ text-align: center; font-size: 24px; margin-bottom: 20px; }}
            .day-names {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; margin-bottom: 10px; }}
            .day-name {{ text-align: center; font-weight: bold; padding: 10px; background: #f0f0f0; }}
            .week {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; margin-bottom: 5px; }}
            .day {{ padding: 10px; border: 1px solid #ddd; min-height: 80px; }}
            .day-number {{ font-weight: bold; margin-bottom: 5px; }}
            .profit {{ background-color: #d4edda; border-color: #c3e6cb; }}
            .loss {{ background-color: #f8d7da; border-color: #f5c6cb; }}
            .no-trades {{ background-color: #f8f9fa; color: #6c757d; }}
            .empty {{ background-color: #e9ecef; }}
            .pnl {{ font-size: 12px; }}
            .trade-count {{ font-size: 11px; color: #666; }}
            .month-stats {{ margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }}
            .stat-box {{ padding: 10px; background: white; border: 1px solid #ddd; border-radius: 3px; text-align: center; }}
            .stat-value {{ font-size: 18px; font-weight: bold; }}
            .stat-label {{ font-size: 12px; color: #666; }}
            .back-button {{ padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer; }}
        </style>
    </head>
    <body>
        <div class="calendar">
            <div class="month-header">
                {calendar.month_name[month]} {year}
                <br>
                <button class="back-button" onclick="window.history.back()">← Back</button>
            </div>
    """

    # Add month stats if we have data
    if not daily_pnl.empty:
        month_pnl = daily_pnl['daily_pnl'].sum()
        total_trades = daily_pnl['trade_count'].sum()
        profitable_days = len(daily_pnl[daily_pnl['daily_pnl'] > 0])
        total_days = len(daily_pnl)

        html += f"""
            <div class="month-stats">
                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="stat-value">${month_pnl:,.2f}</div>
                        <div class="stat-label">Month P&L</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{total_trades}</div>
                        <div class="stat-label">Total Trades</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{profitable_days}/{total_days}</div>
                        <div class="stat-label">Profitable Days</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">{(profitable_days / total_days * 100):.1f}%</div>
                        <div class="stat-label">Day Win Rate</div>
                    </div>
                </div>
            </div>
        """

    # Day names
    html += '<div class="day-names">'
    for day_name in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
        html += f'<div class="day-name">{day_name}</div>'
    html += '</div>'

    # Calendar grid
    for week in month_days:
        html += '<div class="week">'
        for day in week:
            if day != 0:
                day_date = datetime(year, month, day).date()

                if day_date in daily_pnl.index:
                    day_data = daily_pnl.loc[day_date]
                    pnl = day_data['daily_pnl']
                    trade_count = day_data['trade_count']

                    # Determine CSS class
                    if pnl > 0:
                        css_class = "profit"
                        emoji = "✅"
                    elif pnl < 0:
                        css_class = "loss"
                        emoji = "❌"
                    else:
                        css_class = "no-trades"
                        emoji = "➖"

                    html += f"""
                    <div class="day {css_class}">
                        <div class="day-number">{day}</div>
                        <div class="pnl">{emoji} ${pnl:.2f}</div>
                        <div class="trade-count">{trade_count} trade{'s' if trade_count != 1 else ''}</div>
                    </div>
                    """
                else:
                    html += f"""
                    <div class="day no-trades">
                        <div class="day-number">{day}</div>
                        <div class="pnl">No trades</div>
                    </div>
                    """
            else:
                html += '<div class="day empty">&nbsp;</div>'
        html += '</div>'

    html += """
        </div>
        <script>
            // Make days clickable to show details
            document.querySelectorAll('.day').forEach(day => {
                day.style.cursor = 'pointer';
                day.onclick = function() {
                    alert('Day clicked! In the full version, this would show trade details.');
                };
            });
        </script>
    </body>
    </html>
    """

    return html


def main():
    print("Day 7: Calendar View & Database Enhancement")
    print("=" * 50)

    # 1. Setup database (same as before)
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    # Check if trades table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
    if not cursor.fetchone():
        print("Creating trades table...")
        cursor.execute('''
        CREATE TABLE trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            symbol TEXT NOT NULL,
            type TEXT NOT NULL,
            entry_price REAL NOT NULL,
            exit_price REAL NOT NULL,
            pnl REAL NOT NULL,
            status TEXT NOT NULL,
            notes TEXT
        )
        ''')

        # Add sample data
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'XRPUSDT']
        sample_trades = []
        today = datetime.now()

        for i in range(50):
            date = today - timedelta(days=random.randint(0, 90))
            date_str = date.strftime('%Y-%m-%d %H:%M')
            symbol = random.choice(symbols)
            trade_type = random.choice(['LONG', 'SHORT'])
            entry_price = round(random.uniform(100, 50000), 2)
            pnl = round(random.uniform(-500, 500), 2)
            exit_price = round(entry_price + (pnl / 1.0), 2)
            status = 'WIN' if pnl > 0 else 'LOSS'

            sample_trades.append((
                date_str, symbol, trade_type, entry_price, exit_price,
                pnl, status, f"Trade {i + 1}"
            ))

        cursor.executemany('''
            INSERT INTO trades (date, symbol, type, entry_price, exit_price, pnl, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_trades)
        print(f"Added {len(sample_trades)} sample trades")

    conn.commit()

    # 2. Load data
    df = pd.read_sql_query("SELECT * FROM trades ORDER BY date DESC", conn)
    conn.close()

    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])

        # 3. Show basic metrics in terminal
        print("\n📊 Trading Metrics:")
        print(f"   Total Trades: {len(df)}")
        print(f"   Total P&L: ${df['pnl'].sum():.2f}")
        print(f"   Win Rate: {(len(df[df['pnl'] > 0]) / len(df) * 100):.1f}%")
        print(f"   Date Range: {df['date'].min().date()} to {df['date'].max().date()}")

        # 4. Ask user for month/year
        print("\n📅 Calendar View")
        current_year = datetime.now().year
        current_month = datetime.now().month

        year = int(input(f"Enter year ({current_year}): ") or current_year)
        month = int(input(f"Enter month (1-12, {current_month}): ") or current_month)

        # 5. Create HTML calendar
        html_content = create_html_calendar(df, year, month)

        # 6. Save and open in browser
        with open('calendar_view.html', 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"\n✅ Calendar created for {calendar.month_name[month]} {year}")
        print("   Opening in browser...")

        # Open in browser
        webbrowser.open('file://' + os.path.abspath('calendar_view.html'))

        # 7. Create key levels tables
        print("\n🗄️ Creating key levels database...")
        conn = sqlite3.connect('trading_journal.db')
        cursor = conn.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_key_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            level_type TEXT,
            symbol TEXT,
            value REAL NOT NULL,
            strength INTEGER,
            timeframe TEXT,
            notes TEXT
        )
        ''')

        # Add default levels
        cursor.execute("SELECT COUNT(*) FROM user_key_levels")
        if cursor.fetchone()[0] == 0:
            default_levels = [
                ('BTC Major Support', 'Support', 'BTCUSDT', 40000.00, 5, '1D', 'Major level'),
                ('BTC Major Resistance', 'Resistance', 'BTCUSDT', 50000.00, 5, '1D', 'Key resistance'),
                ('ETH Support', 'Support', 'ETHUSDT', 2200.00, 4, '1D', 'Strong support'),
                ('ETH Resistance', 'Resistance', 'ETHUSDT', 2800.00, 4, '1D', 'Previous highs'),
                ('Daily Pivot', 'Pivot', 'ALL', 0.00, 3, '1D', 'Standard pivot'),
            ]

            cursor.executemany('''
                INSERT INTO user_key_levels (name, level_type, symbol, value, strength, timeframe, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', default_levels)
            print(f"   Added {len(default_levels)} default key levels")

        conn.commit()
        conn.close()

        print("\n🎉 Day 7 Complete!")
        print("   - Calendar view saved as calendar_view.html")
        print("   - Database enhanced with key levels tables")
        print("   - Key metrics displayed in terminal")

    else:
        print("No trades found in database!")


if __name__ == "__main__":
    main()