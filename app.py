from flask import Flask, render_template, jsonify, request
import sqlite3
from datetime import datetime
from utils.calculations import get_all_trades, calculate_metrics, calculate_daily_summary

app = Flask(__name__)


@app.route('/')
def dashboard():
    """Main dashboard with metrics"""
    trades = get_all_trades()
    metrics = calculate_metrics(trades)

    # Get recent trades (last 10)
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, symbol, side, entry_price, exit_price, pnl, pnl_percentage, status,
               strftime('%Y-%m-%d %H:%M', entry_time) as entry_time,
               strftime('%Y-%m-%d %H:%M', exit_time) as exit_time
        FROM trades
        WHERE status = 'closed'
        ORDER BY entry_time DESC
        LIMIT 10
    ''')

    recent_trades = []
    for row in cursor.fetchall():
        recent_trades.append({
            'id': row[0],
            'symbol': row[1],
            'side': row[2],
            'entry_price': f"${float(row[3]):.2f}" if row[3] else "N/A",
            'exit_price': f"${float(row[4]):.2f}" if row[4] else "N/A",
            'pnl': f"${float(row[5]):.2f}" if row[5] else "$0.00",
            'pnl_percent': f"{float(row[6]):.2f}%" if row[6] else "0%",
            'status': row[7],
            'entry_time': row[8],
            'exit_time': row[9] if row[9] else "Open",
            'pnl_class': 'win' if row[5] and float(row[5]) > 0 else 'loss' if row[5] and float(
                row[5]) < 0 else 'breakeven'
        })

    # Get open positions
    cursor.execute('''
        SELECT symbol, side, entry_price, pnl,
               strftime('%Y-%m-%d %H:%M', entry_time) as entry_time
        FROM trades
        WHERE status = 'open'
        ORDER BY entry_time DESC
    ''')

    open_positions = []
    for row in cursor.fetchall():
        open_positions.append({
            'symbol': row[0],
            'side': row[1],
            'entry_price': f"${float(row[2]):.2f}" if row[2] else "N/A",
            'pnl': f"${float(row[3]):.2f}" if row[3] else "$0.00",
            'entry_time': row[4]
        })

    # Get account balance
    cursor.execute('SELECT balance FROM account ORDER BY timestamp DESC LIMIT 1')
    account_row = cursor.fetchone()
    account_balance = f"${float(account_row[0]):.2f}" if account_row else "$0.00"
    account_equity = f"${float(account_row[0]):.2f}" if account_row else "$0.00"

    # Get best/worst trade
    cursor.execute(
        'SELECT symbol, pnl, pnl_percentage FROM trades WHERE status = "closed" AND pnl IS NOT NULL ORDER BY pnl DESC LIMIT 1')
    best_trade_row = cursor.fetchone()
    best_trade = {
        'symbol': best_trade_row[0] if best_trade_row else "N/A",
        'pnl': f"${float(best_trade_row[1]):.2f}" if best_trade_row and best_trade_row[1] else "$0.00",
        'percent': f"{float(best_trade_row[2]):.2f}%" if best_trade_row and best_trade_row[2] else "0%"
    } if best_trade_row else {'symbol': 'N/A', 'pnl': '$0.00', 'percent': '0%'}

    cursor.execute(
        'SELECT symbol, pnl, pnl_percentage FROM trades WHERE status = "closed" AND pnl IS NOT NULL ORDER BY pnl ASC LIMIT 1')
    worst_trade_row = cursor.fetchone()
    worst_trade = {
        'symbol': worst_trade_row[0] if worst_trade_row else "N/A",
        'pnl': f"${float(worst_trade_row[1]):.2f}" if worst_trade_row and worst_trade_row[1] else "$0.00",
        'percent': f"{float(worst_trade_row[2]):.2f}%" if worst_trade_row and worst_trade_row[2] else "0%"
    } if worst_trade_row else {'symbol': 'N/A', 'pnl': '$0.00', 'percent': '0%'}

    # Get current month for calendar
    current_date = datetime.now()
    year = current_date.year
    month = current_date.month

    # Get daily summaries for calendar
    daily_summaries = calculate_daily_summary()

    conn.close()

    # Prepare calendar data
    calendar_data = {
        'year': year,
        'month': month,
        'month_name': current_date.strftime('%B'),
        'daily_summaries': {item['date']: item for item in daily_summaries}
    }

    # Consecutive wins/losses
    trades_for_streak = get_all_trades()
    current_streak = 0
    is_win_streak = None

    for trade in reversed(trades_for_streak):  # Start from most recent
        if is_win_streak is None:
            is_win_streak = trade['pnl'] > 0
            current_streak = 1
        elif (trade['pnl'] > 0) == is_win_streak:
            current_streak += 1
        else:
            break

    return render_template('dashboard.html',
                           metrics=metrics,
                           recent_trades=recent_trades,
                           open_positions=open_positions,
                           account_balance=account_balance,
                           account_equity=account_equity,
                           best_trade=best_trade,
                           worst_trade=worst_trade,
                           calendar_data=calendar_data,
                           current_streak=current_streak,
                           is_win_streak=is_win_streak)


@app.route('/calendar')
def calendar_page():
    """Separate calendar page"""
    return render_template('calendar.html')


@app.route('/key-levels')
def key_levels():
    """Key levels page"""
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT id, level_name, level_price, level_type, asset, description, created_date FROM key_levels ORDER BY created_date DESC')

    key_levels_data = []
    for row in cursor.fetchall():
        key_levels_data.append({
            'id': row[0],
            'name': row[1],
            'price': f"${float(row[2]):.2f}" if row[2] else "N/A",
            'type': row[3],
            'asset': row[4],
            'description': row[5],
            'created': row[6]
        })

    conn.close()
    return render_template('key_levels.html', key_levels=key_levels_data)


@app.route('/api/calendar-data')
def get_calendar_data():
    """Get calendar data for current month"""
    daily_summaries = calculate_daily_summary()
    return jsonify({'daily_summaries': daily_summaries})


@app.route('/api/day-trades')
def get_day_trades():
    """Get trades for a specific day"""
    date = request.args.get('date')
    if not date:
        return jsonify({'error': 'No date provided'}), 400

    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, symbol, side, entry_price, exit_price, pnl, pnl_percentage, status,
               strftime('%Y-%m-%d %H:%M', entry_time) as entry_time,
               strftime('%Y-%m-%d %H:%M', exit_time) as exit_time
        FROM trades
        WHERE strftime('%Y-%m-%d', entry_time) = ?
        ORDER BY entry_time DESC
    ''', (date,))

    trades = []
    for row in cursor.fetchall():
        trades.append({
            'id': row[0],
            'symbol': row[1],
            'side': row[2],
            'entry_price': f"${float(row[3]):.2f}" if row[3] else "N/A",
            'exit_price': f"${float(row[4]):.2f}" if row[4] else "N/A",
            'pnl': f"${float(row[5]):.2f}" if row[5] else "$0.00",
            'pnl_percent': f"{float(row[6]):.2f}%" if row[6] else "0%",
            'status': row[7],
            'entry_time': row[8],
            'exit_time': row[9] if row[9] else "Open",
            'pnl_class': 'win' if row[5] and float(row[5]) > 0 else 'loss' if row[5] and float(
                row[5]) < 0 else 'breakeven'
        })

    conn.close()

    daily_summary = calculate_daily_summary(date)

    return jsonify({
        'date': date,
        'trades': trades,
        'summary': daily_summary
    })


@app.route('/api/refresh-data')
def refresh_data():
    """Manually trigger data refresh"""
    try:
        return jsonify({
            'success': True,
            'message': 'Refresh endpoint - add your Bybit fetch logic here'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/trade/<int:trade_id>')
def get_trade_details(trade_id):
    """Get detailed information for a specific trade"""
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    cursor.execute(
        'SELECT id, symbol, side, entry_price, exit_price, pnl, pnl_percentage, status, entry_time, exit_time, notes FROM trades WHERE id = ?',
        (trade_id,))

    row = cursor.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Trade not found'}), 404

    trade = {
        'id': row[0],
        'symbol': row[1],
        'side': row[2],
        'entry_price': float(row[3]) if row[3] else 0,
        'exit_price': float(row[4]) if row[4] else 0,
        'pnl': float(row[5]) if row[5] else 0,
        'pnl_percent': float(row[6]) if row[6] else 0,
        'status': row[7],
        'entry_time': row[8],
        'exit_time': row[9] if row[9] else None,
        'notes': row[10] if row[10] else ''
    }

    conn.close()
    return jsonify(trade)


def init_db():
    """Initialize database"""
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            side TEXT NOT NULL,
            entry_price REAL,
            exit_price REAL,
            pnl REAL,
            pnl_percentage REAL,
            status TEXT,
            entry_time TIMESTAMP,
            exit_time TIMESTAMP,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS account (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            balance REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS key_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level_name TEXT NOT NULL,
            level_price REAL,
            level_type TEXT,
            asset TEXT,
            description TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully")


if __name__ == '__main__':
    init_db()

    print("Trading Journal starting on http://127.0.0.1:5000")
    print("Metrics calculations FIXED and working correctly!")
    app.run(debug=True)