from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
import os
import json
import atexit
from backup_system import backup_data

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
CORS(app)


# Initialize database
def init_db():
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    # Trades table with screenshots
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset TEXT NOT NULL,
        side TEXT NOT NULL,
        entry_price REAL NOT NULL,
        exit_price REAL NOT NULL,
        quantity REAL NOT NULL,
        entry_time TEXT NOT NULL,
        exit_time TEXT NOT NULL,
        pnl REAL NOT NULL,
        key_level TEXT,
        key_level_type TEXT,
        confirmation TEXT,
        model TEXT,
        weekly_bias TEXT,
        daily_bias TEXT,
        notes TEXT,
        screenshot_url TEXT,
        status TEXT DEFAULT 'closed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute("PRAGMA table_info(trades)")
    existing_cols = {row[1] for row in cursor.fetchall()}
    if 'weekly_bias' not in existing_cols:
        cursor.execute("ALTER TABLE trades ADD COLUMN weekly_bias TEXT")
    if 'daily_bias' not in existing_cols:
        cursor.execute("ALTER TABLE trades ADD COLUMN daily_bias TEXT")

    # API credentials table with remember_me
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS api_credentials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exchange TEXT DEFAULT 'bybit',
        api_key TEXT,
        api_secret TEXT,
        remember_me INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Add sample data for December 2025 if empty
    cursor.execute("SELECT COUNT(*) FROM trades")
    if cursor.fetchone()[0] == 0:
        sample_trades = [
            ('BTCUSDT', 'long', 85000, 87000, 0.1, '2025-12-01 09:00:00', '2025-12-01 10:30:00', 200, '85000',
             'support', 'break_retest', 'Bull Flag', 'Good trade'),
            ('ETHUSDT', 'short', 4500, 4400, 1.0, '2025-12-01 14:00:00', '2025-12-01 15:00:00', 100, '4500',
             'resistance', 'candle_pattern', 'Evening Star', 'Scalp'),
            ('SOLUSDT', 'long', 200, 210, 10.0, '2025-12-02 10:00:00', '2025-12-02 12:00:00', 100, '200', 'trendline',
             'volume_spike', 'Breakout', 'Volume spike'),
            ('BTCUSDT', 'short', 86000, 85500, 0.2, '2025-12-03 11:00:00', '2025-12-03 13:00:00', -100, '86000',
             'resistance', 'divergence', 'RSI Div', 'Failed'),
            ('ETHUSDT', 'long', 4400, 4600, 0.5, '2025-12-05 09:30:00', '2025-12-05 16:00:00', 100, '4400', 'fibonacci',
             'multiple_timeframe', 'Fib', '4H TF'),
            ('SOLUSDT', 'short', 210, 205, 5.0, '2025-12-05 14:00:00', '2025-12-05 15:30:00', 25, '210', 'pivot',
             'break_retest', 'Pivot Reject', 'Weekly pivot'),
            ('BTCUSDT', 'long', 85500, 86500, 0.15, '2025-12-10 10:00:00', '2025-12-10 14:00:00', 150, '85500',
             'support', 'candle_pattern', 'Hammer', 'Daily support'),
            ('ETHUSDT', 'short', 4550, 4500, 2.0, '2025-12-15 13:00:00', '2025-12-15 15:00:00', 100, '4550',
             'resistance', 'volume_spike', 'Volume Wall', 'Rejection'),
            ('SOLUSDT', 'long', 195, 210, 8.0, '2025-12-20 09:00:00', '2025-12-20 18:00:00', 120, '195', 'support',
             'break_retest', 'Double Bottom', 'Reversal'),
            ('BTCUSDT', 'long', 87000, 88000, 0.05, '2025-12-25 11:00:00', '2025-12-25 13:00:00', 50, '87000',
             'trendline', 'multiple_timeframe', 'Trend', 'Christmas')
        ]

        cursor.executemany('''
            INSERT INTO trades (asset, side, entry_price, exit_price, quantity, entry_time, exit_time, 
                              pnl, key_level, key_level_type, confirmation, model, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_trades)

    conn.commit()
    conn.close()


init_db()


def get_db_connection():
    conn = sqlite3.connect('trading_journal.db')
    conn.row_factory = sqlite3.Row
    return conn


# ================== BASIC ROUTES ==================
@app.route('/')
def index():
    return render_template('single_page.html')


@app.route('/api/trades', methods=['GET'])
def get_trades():
    period = request.args.get('period', 'all')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Build query based on period
    query = "SELECT * FROM trades WHERE 1=1"
    params = []

    if period == 'today':
        query += " AND DATE(entry_time) = DATE('now')"
    elif period == 'week':
        query += " AND entry_time >= DATE('now', '-7 days')"
    elif period == 'month':
        query += " AND strftime('%Y-%m', entry_time) = strftime('%Y-%m', 'now')"

    query += " ORDER BY entry_time DESC"
    cursor.execute(query, params)

    trades = [dict(row) for row in cursor.fetchall()]

    # Calculate statistics
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t['pnl'] > 0)
    losing_trades = sum(1 for t in trades if t['pnl'] < 0)
    total_pnl = sum(t['pnl'] for t in trades)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

    # Calculate average win/loss
    wins = [t['pnl'] for t in trades if t['pnl'] > 0]
    losses = [t['pnl'] for t in trades if t['pnl'] < 0]
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0

    # Calculate profit factor
    total_wins = sum(wins) if wins else 0
    total_losses = abs(sum(losses)) if losses else 0
    profit_factor = total_wins / total_losses if total_losses > 0 else 0

    # Key levels stats
    cursor.execute('''
        SELECT key_level_type, COUNT(*) as count 
        FROM trades 
        WHERE key_level_type IS NOT NULL AND key_level_type != ''
        GROUP BY key_level_type
    ''')
    key_levels = {row['key_level_type']: row['count'] for row in cursor.fetchall()}

    # Confirmations stats
    cursor.execute('''
        SELECT confirmation, COUNT(*) as count 
        FROM trades 
        WHERE confirmation IS NOT NULL AND confirmation != ''
        GROUP BY confirmation
    ''')
    confirmations = {row['confirmation']: row['count'] for row in cursor.fetchall()}

    # Models stats
    cursor.execute('''
        SELECT model, COUNT(*) as count 
        FROM trades 
        WHERE model IS NOT NULL AND model != ''
        GROUP BY model
    ''')
    models = {row['model']: row['count'] for row in cursor.fetchall()}

    conn.close()

    return jsonify({
        'trades': trades,
        'statistics': {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'total_pnl': total_pnl,
            'win_rate': round(win_rate, 1),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'key_levels': key_levels,
            'confirmations': confirmations,
            'models': models
        }
    })


@app.route('/api/trades/<int:trade_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_trade(trade_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute('SELECT * FROM trades WHERE id = ?', (trade_id,))
        trade = cursor.fetchone()
        conn.close()
        return jsonify(dict(trade)) if trade else ('', 404)

    elif request.method == 'PUT':
        data = request.json
        cursor.execute('''
            UPDATE trades SET
                asset = ?, side = ?, entry_price = ?, exit_price = ?, quantity = ?,
                entry_time = ?, exit_time = ?, pnl = ?, key_level = ?, key_level_type = ?,
                confirmation = ?, model = ?, weekly_bias = ?, daily_bias = ?, notes = ?, screenshot_url = ?
            WHERE id = ?
        ''', (
            data['asset'], data['side'], data['entry_price'], data['exit_price'], data['quantity'],
            data['entry_time'], data['exit_time'], data['pnl'], data.get('key_level'),
            data.get('key_level_type'), data.get('confirmation'), data.get('model'),
            data.get('weekly_bias'), data.get('daily_bias'),
            data.get('notes'), data.get('screenshot_url'), trade_id
        ))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM trades WHERE id = ?', (trade_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})


@app.route('/api/trades', methods=['POST'])
def create_trade():
    data = request.json

    # Calculate P&L
    if data['side'] == 'long':
        pnl = (float(data['exit_price']) - float(data['entry_price'])) * float(data['quantity'])
    else:
        pnl = (float(data['entry_price']) - float(data['exit_price'])) * float(data['quantity'])

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO trades (asset, side, entry_price, exit_price, quantity, entry_time, exit_time, pnl,
                          key_level, key_level_type, confirmation, model, weekly_bias, daily_bias, notes, screenshot_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['asset'], data['side'], data['entry_price'], data['exit_price'], data['quantity'],
        data['entry_time'], data['exit_time'], pnl, data.get('key_level'), data.get('key_level_type'),
        data.get('confirmation'), data.get('model'), data.get('weekly_bias'), data.get('daily_bias'),
        data.get('notes'), data.get('screenshot_url')
    ))

    trade_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'id': trade_id})


# ================== ENHANCED FEATURES ==================
# Calendar data with full day color coding
@app.route('/api/calendar_data', methods=['GET'])
def get_calendar_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 
            DATE(entry_time) as trade_date,
            SUM(pnl) as daily_pnl,
            COUNT(*) as trade_count,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades
        FROM trades 
        GROUP BY DATE(entry_time)
        ORDER BY trade_date
    ''')

    rows = cursor.fetchall()
    conn.close()

    events = []
    for row in rows:
        win_rate = (row['winning_trades'] / row['trade_count'] * 100) if row['trade_count'] > 0 else 0

        # Determine color based on P&L
        if row['daily_pnl'] > 0:
            color = '#4CAF50'  # Green
        elif row['daily_pnl'] < 0:
            color = '#f44336'  # Red
        else:
            color = '#9E9E9E'  # Gray

        events.append({
            'title': f"${row['daily_pnl']:.0f} | {row['trade_count']} trades | {win_rate:.0f}% WR",
            'start': row['trade_date'],
            'allDay': True,
            'backgroundColor': color,
            'borderColor': color,
            'textColor': '#ffffff',
            'extendedProps': {
                'pnl': row['daily_pnl'],
                'trade_count': row['trade_count'],
                'win_rate': win_rate
            }
        })

    return jsonify(events)


# Get trades for a specific day
@app.route('/api/trades_by_date', methods=['GET'])
def get_trades_by_date():
    date_str = request.args.get('date')
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM trades 
        WHERE DATE(entry_time) = ? 
        ORDER BY entry_time DESC
    ''', (date_str,))

    trades = [dict(row) for row in cursor.fetchall()]

    # Calculate daily stats
    total_pnl = sum(t['pnl'] for t in trades)
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t['pnl'] > 0)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

    conn.close()

    return jsonify({
        'trades': trades,
        'daily_stats': {
            'total_pnl': total_pnl,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'win_rate': round(win_rate, 1)
        }
    })


# P&L chart data
@app.route('/api/pnl_data', methods=['GET'])
def get_pnl_data():
    period = request.args.get('period', 'all')

    conn = get_db_connection()
    cursor = conn.cursor()

    if period == 'today':
        query = "SELECT DATE(entry_time) as date, SUM(pnl) as pnl FROM trades WHERE DATE(entry_time) = DATE('now') GROUP BY DATE(entry_time) ORDER BY date"
    elif period == 'week':
        query = "SELECT DATE(entry_time) as date, SUM(pnl) as pnl FROM trades WHERE entry_time >= DATE('now', '-7 days') GROUP BY DATE(entry_time) ORDER BY date"
    elif period == 'month':
        query = "SELECT DATE(entry_time) as date, SUM(pnl) as pnl FROM trades WHERE strftime('%Y-%m', entry_time) = strftime('%Y-%m', 'now') GROUP BY DATE(entry_time) ORDER BY date"
    else:
        query = "SELECT DATE(entry_time) as date, SUM(pnl) as pnl FROM trades GROUP BY DATE(entry_time) ORDER BY date"

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    dates = [row['date'] for row in rows]
    daily_pnl = [row['pnl'] for row in rows]

    # Calculate cumulative P&L
    cumulative = []
    running_total = 0
    for pnl in daily_pnl:
        running_total += pnl
        cumulative.append(running_total)

    return jsonify({
        'dates': dates,
        'daily_pnl': daily_pnl,
        'cumulative_pnl': cumulative
    })


# Bybit API routes with remember me
@app.route('/api/save_bybit_credentials', methods=['POST'])
def save_bybit_credentials():
    data = request.json
    api_key = data.get('api_key')
    api_secret = data.get('api_secret')
    remember_me = data.get('remember_me', False)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing
    cursor.execute('DELETE FROM api_credentials')

    # Insert new with remember_me flag
    cursor.execute('INSERT INTO api_credentials (exchange, api_key, api_secret, remember_me) VALUES (?, ?, ?, ?)',
                   ('bybit', api_key, api_secret, 1 if remember_me else 0))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Credentials saved'})


@app.route('/api/get_bybit_credentials', methods=['GET'])
def get_bybit_credentials():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM api_credentials WHERE remember_me = 1 LIMIT 1')
    creds = cursor.fetchone()
    conn.close()

    if creds and creds['api_key']:
        return jsonify({
            'connected': True,
            'api_key': creds['api_key'],
            'api_secret': creds['api_secret'],
            'remember_me': bool(creds['remember_me'])
        })
    return jsonify({'connected': False})


@app.route('/api/get_bybit_status', methods=['GET'])
def get_bybit_status():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM api_credentials LIMIT 1')
    creds = cursor.fetchone()
    conn.close()

    if creds and creds['api_key']:
        return jsonify({'connected': True, 'status': 'Configured (not connected)'})
    return jsonify({'connected': False, 'status': 'Not configured'})


@app.route('/api/sync_bybit_trades', methods=['POST'])
def sync_bybit_trades():
    # This would integrate with actual Bybit API
    return jsonify({
        'success': True,
        'message': 'Bybit sync would work with real API keys',
        'count': 0
    })


if __name__ == '__main__':
    # Register backup function to run on app exit
    atexit.register(backup_data)
    app.run(debug=True, port=5000)