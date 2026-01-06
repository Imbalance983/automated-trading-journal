from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
import os
import json
import atexit

try:
    # pybit v3+
    from pybit.unified_trading import HTTP as BybitHTTP
except Exception:
    try:
        # fallback for older pybit
        from pybit import HTTP as BybitHTTP
    except Exception:
        BybitHTTP = None

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
    if 'screenshot_url' not in existing_cols:
        cursor.execute("ALTER TABLE trades ADD COLUMN screenshot_url TEXT")

    # Ensure existing rows have bias values so filters work even if user never set them
    cursor.execute(
        "UPDATE trades SET weekly_bias = 'neutral' WHERE weekly_bias IS NULL OR TRIM(weekly_bias) = ''"
    )
    cursor.execute(
        "UPDATE trades SET daily_bias = 'neutral' WHERE daily_bias IS NULL OR TRIM(daily_bias) = ''"
    )

    # API credentials (Bybit)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS api_credentials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exchange TEXT NOT NULL,
        api_key TEXT,
        api_secret TEXT,
        network TEXT DEFAULT 'mainnet',
        remember_me INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute("PRAGMA table_info(api_credentials)")
    creds_cols = {row[1] for row in cursor.fetchall()}
    if 'network' not in creds_cols:
        cursor.execute("ALTER TABLE api_credentials ADD COLUMN network TEXT DEFAULT 'mainnet'")
    if 'remember_me' not in creds_cols:
        cursor.execute("ALTER TABLE api_credentials ADD COLUMN remember_me INTEGER DEFAULT 0")

    # Track already-imported Bybit trades to prevent duplicates
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bybit_imports (
        external_id TEXT PRIMARY KEY,
        network TEXT,
        imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Add sample data for December 2025 if empty
    cursor.execute("SELECT COUNT(*) FROM trades")
    if cursor.fetchone()[0] == 0:
        sample_trades = [
            ('BTCUSDT', 'long', 85000, 87000, 0.1, '2025-12-01 09:00:00', '2025-12-01 10:30:00', 200, '85000',
             'support', 'break_retest', 'Bull Flag', 'Good trade', 'bullish', 'neutral'),
            ('ETHUSDT', 'short', 4500, 4400, 1.0, '2025-12-01 14:00:00', '2025-12-01 15:00:00', 100, '4500',
             'resistance', 'candle_pattern', 'Evening Star', 'Scalp', 'bearish', 'bearish'),
            ('SOLUSDT', 'long', 200, 210, 10.0, '2025-12-02 10:00:00', '2025-12-02 12:00:00', 100, '200', 'trendline',
             'volume_spike', 'Breakout', 'Volume spike', 'bullish', 'bullish'),
            ('BTCUSDT', 'short', 86000, 85500, 0.2, '2025-12-03 11:00:00', '2025-12-03 13:00:00', -100, '86000',
             'resistance', 'divergence', 'RSI Div', 'Failed', 'bearish', 'neutral'),
            ('ETHUSDT', 'long', 4400, 4600, 0.5, '2025-12-05 09:30:00', '2025-12-05 16:00:00', 100, '4400', 'fibonacci',
             'multiple_timeframe', 'Fib', '4H TF', 'neutral', 'bullish'),
            ('SOLUSDT', 'short', 210, 205, 5.0, '2025-12-05 14:00:00', '2025-12-05 15:30:00', 25, '210', 'pivot',
             'break_retest', 'Pivot Reject', 'Weekly pivot', 'bearish', 'bearish'),
            ('BTCUSDT', 'long', 85500, 86500, 0.15, '2025-12-10 10:00:00', '2025-12-10 14:00:00', 150, '85500',
             'support', 'candle_pattern', 'Hammer', 'Daily support', 'bullish', 'neutral'),
            ('ETHUSDT', 'short', 4550, 4500, 2.0, '2025-12-15 13:00:00', '2025-12-15 15:00:00', 100, '4550',
             'resistance', 'volume_spike', 'Volume Wall', 'Rejection', 'bearish', 'bearish'),
            ('SOLUSDT', 'long', 195, 210, 8.0, '2025-12-20 09:00:00', '2025-12-20 18:00:00', 120, '195', 'support',
             'break_retest', 'Double Bottom', 'Reversal', 'bullish', 'bullish'),
            ('BTCUSDT', 'long', 87000, 88000, 0.05, '2025-12-25 11:00:00', '2025-12-25 13:00:00', 50, '87000',
             'trendline', 'multiple_timeframe', 'Trend', 'Christmas', 'neutral', 'bullish')
        ]

        cursor.executemany('''
            INSERT INTO trades (asset, side, entry_price, exit_price, quantity, entry_time, exit_time, 
                              pnl, key_level, key_level_type, confirmation, model, notes, weekly_bias, daily_bias)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Build query based on period
    query = "SELECT * FROM trades WHERE 1=1"
    params = []

    if start_date and end_date:
        query += " AND DATE(entry_time) BETWEEN ? AND ?"
        params.extend([start_date, end_date])

    if period == 'today':
        query += " AND DATE(entry_time) = DATE('now')"
    elif period == 'week':
        query += " AND entry_time >= DATE('now', '-7 days')"
    elif period == 'month':
        query += " AND strftime('%Y-%m', entry_time) = strftime('%Y-%m', 'now')"

    query += " ORDER BY entry_time DESC"
    cursor.execute(query, params)

    trades = [dict(row) for row in cursor.fetchall()]

    # Ensure bias fields are always present so filters work even if older trades have blanks
    for t in trades:
        if not t.get('weekly_bias') or str(t.get('weekly_bias')).strip() == '':
            t['weekly_bias'] = 'neutral'
        if not t.get('daily_bias') or str(t.get('daily_bias')).strip() == '':
            t['daily_bias'] = 'neutral'

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
        win_rate = round(win_rate, 1)

        # Determine color based on P&L
        if row['daily_pnl'] > 0:
            color = '#4CAF50'  # Green
        elif row['daily_pnl'] < 0:
            color = '#f44336'  # Red
        else:
            color = '#9E9E9E'  # Gray

        events.append({
            'title': f"${row['daily_pnl']:.0f} | {row['trade_count']} trades | {round(win_rate, 1)}% WR",
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
    network = (data.get('network') or 'mainnet').strip().lower()
    remember_me = data.get('remember_me', False)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing
    cursor.execute('DELETE FROM api_credentials')

    # Insert new with remember_me flag
    cursor.execute(
        'INSERT INTO api_credentials (exchange, api_key, api_secret, network, remember_me) VALUES (?, ?, ?, ?, ?)',
        ('bybit', api_key, api_secret, network, 1 if remember_me else 0)
    )

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
            'network': creds['network'] if 'network' in creds.keys() else 'mainnet',
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
        net = creds['network'] if 'network' in creds.keys() else 'mainnet'
        return jsonify({'connected': True, 'status': f'Configured ({net})'})
    return jsonify({'connected': False, 'status': 'Not configured'})


def _get_saved_bybit_credentials():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM api_credentials LIMIT 1')
    creds = cursor.fetchone()
    conn.close()
    return dict(creds) if creds else None


def _create_bybit_client(api_key, api_secret, network):
    if BybitHTTP is None:
        raise RuntimeError('pybit is not installed or could not be imported')

    is_testnet = str(network or 'mainnet').strip().lower() == 'testnet'

    # pybit.unified_trading.HTTP signature: HTTP(testnet=bool, api_key=..., api_secret=...)
    try:
        return BybitHTTP(testnet=is_testnet, api_key=api_key, api_secret=api_secret)
    except TypeError:
        # legacy pybit.HTTP signature: HTTP(endpoint=..., api_key=..., api_secret=...)
        endpoint = 'https://api-testnet.bybit.com' if is_testnet else 'https://api.bybit.com'
        return BybitHTTP(endpoint=endpoint, api_key=api_key, api_secret=api_secret)


def _parse_bybit_time(bybit_time):
    if not bybit_time:
        return None
    try:
        # Bybit commonly uses ms timestamps, sometimes as strings.
        if isinstance(bybit_time, (int, float)):
            return datetime.utcfromtimestamp(float(bybit_time) / 1000).strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(bybit_time, str) and bybit_time.isdigit():
            return datetime.utcfromtimestamp(int(bybit_time) / 1000).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return None

    return str(bybit_time)


@app.route('/api/sync_bybit_trades', methods=['POST'])
def sync_bybit_trades():
    creds = _get_saved_bybit_credentials()
    if not creds or not creds.get('api_key') or not creds.get('api_secret'):
        return jsonify({'success': False, 'message': 'Save your Bybit API key/secret first.', 'trades_synced': 0}), 400

    network = (creds.get('network') or 'mainnet').strip().lower()

    try:
        client = _create_bybit_client(creds['api_key'], creds['api_secret'], network)
    except Exception as e:
        return jsonify({'success': False, 'message': f'Bybit client init failed: {e}', 'trades_synced': 0}), 500

    # Fetch closed PnL items from Bybit.
    # User preference: USDT linear only.
    all_items = []
    category = 'linear'
    cursor_val = None
    max_pages = 20
    pages = 0

    while pages < max_pages:
        pages += 1
        try:
            kwargs = {'category': category, 'limit': 200}
            if cursor_val:
                # unified_trading uses cursor, response returns nextPageCursor
                kwargs['cursor'] = cursor_val
            resp = client.get_closed_pnl(**kwargs)
        except TypeError:
            # legacy pybit may require positional args or different cursor key
            try:
                if cursor_val:
                    resp = client.get_closed_pnl(category=category, limit=200, cursor=cursor_val)
                else:
                    resp = client.get_closed_pnl(category=category, limit=200)
            except Exception:
                break
        except Exception:
            break

        result = (resp or {}).get('result') or {}
        items = result.get('list') or []
        if isinstance(items, list) and items:
            all_items.extend(items)

        next_cursor = result.get('nextPageCursor') or result.get('next_cursor') or result.get('cursor')
        if not next_cursor or next_cursor == cursor_val:
            break
        cursor_val = next_cursor

    if not all_items:
        return jsonify({'success': True, 'message': 'No closed trades found to import.', 'trades_synced': 0})

    conn = get_db_connection()
    cursor = conn.cursor()
    inserted = 0

    for item in all_items:
        # Prefer orderId as unique, fallback to execId if present.
        external_id = item.get('orderId') or item.get('execId') or item.get('tradeId')
        if not external_id:
            continue

        # Dedupe
        cursor.execute('SELECT 1 FROM bybit_imports WHERE external_id = ? LIMIT 1', (external_id,))
        if cursor.fetchone():
            continue

        symbol = item.get('symbol') or ''
        if symbol and not str(symbol).upper().endswith('USDT'):
            continue

        side = (item.get('side') or '').strip().lower()
        qty = float(item.get('qty') or 0)
        entry_price = float(item.get('avgEntryPrice') or item.get('entryPrice') or 0)
        exit_price = float(item.get('avgExitPrice') or item.get('exitPrice') or 0)
        pnl = float(item.get('closedPnl') or item.get('pnl') or 0)

        entry_time = _parse_bybit_time(item.get('createdTime') or item.get('createdTimeE3') or item.get('created_at'))
        exit_time = _parse_bybit_time(item.get('updatedTime') or item.get('updatedTimeE3') or item.get('updated_at'))
        if not entry_time:
            entry_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        if not exit_time:
            exit_time = entry_time

        if side not in ('long', 'short'):
            # Bybit returns Buy/Sell
            if side == 'buy':
                side = 'long'
            elif side == 'sell':
                side = 'short'
            else:
                side = 'long'

        cursor.execute(
            '''
            INSERT INTO trades (
                asset, side, entry_price, exit_price, quantity,
                entry_time, exit_time, pnl,
                key_level, key_level_type, confirmation, model,
                weekly_bias, daily_bias, notes, screenshot_url, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                symbol, side, entry_price, exit_price, qty,
                entry_time, exit_time, pnl,
                None, None, None, None,
                'neutral', 'neutral', 'Imported from Bybit', None, 'closed'
            )
        )

        cursor.execute(
            'INSERT INTO bybit_imports (external_id, network) VALUES (?, ?)',
            (external_id, network)
        )
        inserted += 1

    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'message': f'Imported {inserted} trade(s) from Bybit ({network}).',
        'trades_synced': inserted
    })


@app.route('/api/bulk_fill_bias', methods=['POST'])
def bulk_fill_bias():
    data = request.json or {}
    weekly_value = (data.get('weekly_bias') or 'neutral').strip().lower()
    daily_value = (data.get('daily_bias') or 'neutral').strip().lower()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE trades SET weekly_bias = ? WHERE weekly_bias IS NULL OR TRIM(weekly_bias) = ''",
        (weekly_value,),
    )
    weekly_updated = cursor.rowcount

    cursor.execute(
        "UPDATE trades SET daily_bias = ? WHERE daily_bias IS NULL OR TRIM(daily_bias) = ''",
        (daily_value,),
    )
    daily_updated = cursor.rowcount

    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'weekly_updated': weekly_updated,
        'daily_updated': daily_updated,
        'weekly_bias': weekly_value,
        'daily_bias': daily_value,
    })


if __name__ == '__main__':
    # Register backup function to run on app exit
    # atexit.register(backup_data)
    app.run(debug=True, port=5000)