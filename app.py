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
app.secret_key = 'your-secret-key-here-change-in-production'
CORS(app)


# ================== DATABASE INITIALIZATION ==================
def init_db():
    """Initialize database with all required tables and sample data"""
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    # Trades table
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

    # Add missing columns if they don't exist
    cursor.execute("PRAGMA table_info(trades)")
    existing_cols = {row[1] for row in cursor.fetchall()}

    if 'weekly_bias' not in existing_cols:
        cursor.execute("ALTER TABLE trades ADD COLUMN weekly_bias TEXT")
    if 'daily_bias' not in existing_cols:
        cursor.execute("ALTER TABLE trades ADD COLUMN daily_bias TEXT")
    if 'screenshot_url' not in existing_cols:
        cursor.execute("ALTER TABLE trades ADD COLUMN screenshot_url TEXT")

    # Ensure existing rows have default bias values
    cursor.execute(
        "UPDATE trades SET weekly_bias = 'neutral' WHERE weekly_bias IS NULL OR TRIM(weekly_bias) = ''"
    )
    cursor.execute(
        "UPDATE trades SET daily_bias = 'neutral' WHERE daily_bias IS NULL OR TRIM(daily_bias) = ''"
    )

    # API credentials table
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

    # Track imported Bybit trades to prevent duplicates
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bybit_imports (
        external_id TEXT PRIMARY KEY,
        network TEXT,
        imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Add sample data if database is empty
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
    """Get database connection with row factory"""
    conn = sqlite3.connect('trading_journal.db')
    conn.row_factory = sqlite3.Row
    return conn


# ================== BASIC ROUTES ==================
@app.route('/')
def index():
    """Render main application page"""
    return render_template('single_page.html')


@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Get all trades with statistics"""
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

    # Ensure bias fields always have values
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

    # Average win/loss
    wins = [t['pnl'] for t in trades if t['pnl'] > 0]
    losses = [t['pnl'] for t in trades if t['pnl'] < 0]
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = sum(losses) / len(losses) if losses else 0

    # Profit factor
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
    """Get, update, or delete a specific trade"""
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
    """Create a new trade"""
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
        data.get('confirmation'), data.get('model'), data.get('weekly_bias', 'neutral'),
        data.get('daily_bias', 'neutral'), data.get('notes'), data.get('screenshot_url')
    ))

    trade_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'id': trade_id})


# ================== CALENDAR & ANALYTICS ==================
@app.route('/api/calendar_data', methods=['GET'])
def get_calendar_data():
    """Get calendar data with daily P&L"""
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
            'title': f"${row['daily_pnl']:.0f} | {row['trade_count']} trades | {round(win_rate, 1)}% WR",
            'start': row['trade_date'],
            'allDay': True,
            'backgroundColor': color,
            'borderColor': color,
            'textColor': '#ffffff',
            'extendedProps': {
                'pnl': row['daily_pnl'],
                'trade_count': row['trade_count'],
                'win_rate': round(win_rate, 1)
            }
        })

    return jsonify(events)


@app.route('/api/trades_by_date', methods=['GET'])
def get_trades_by_date():
    """Get trades for a specific date"""
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


@app.route('/api/pnl_data', methods=['GET'])
def get_pnl_data():
    """Get P&L chart data"""
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


# ================== BYBIT INTEGRATION ==================
def _get_saved_bybit_credentials():
    """Retrieve saved Bybit credentials from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM api_credentials LIMIT 1')
    creds = cursor.fetchone()
    conn.close()
    return dict(creds) if creds else None


def _create_bybit_client(api_key, api_secret, network):
    """Create Bybit API client"""
    if BybitHTTP is None:
        raise RuntimeError('pybit is not installed or could not be imported')

    is_testnet = str(network or 'mainnet').strip().lower() == 'testnet'

    try:
        # pybit v3+ unified_trading
        return BybitHTTP(testnet=is_testnet, api_key=api_key, api_secret=api_secret)
    except TypeError:
        # legacy pybit
        endpoint = 'https://api-testnet.bybit.com' if is_testnet else 'https://api.bybit.com'
        return BybitHTTP(endpoint=endpoint, api_key=api_key, api_secret=api_secret)


def _parse_bybit_time(bybit_time):
    """Parse Bybit timestamp to datetime string"""
    if not bybit_time:
        return None
    try:
        # Bybit uses millisecond timestamps
        if isinstance(bybit_time, (int, float)):
            return datetime.utcfromtimestamp(float(bybit_time) / 1000).strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(bybit_time, str) and bybit_time.isdigit():
            return datetime.utcfromtimestamp(int(bybit_time) / 1000).strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return None
    return str(bybit_time)


def _debug_log(session_id, run_id, hypothesis_id, location, message, data):
    """Helper function to write debug logs"""
    try:
        import os
        import json
        log_path = r'c:\Users\Owner\Desktop\TJ\.cursor\debug.log'
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        log_data = {
            'sessionId': session_id,
            'runId': run_id,
            'hypothesisId': hypothesis_id,
            'location': location,
            'message': message,
            'data': data,
            'timestamp': int(datetime.utcnow().timestamp() * 1000)
        }
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_data) + '\n')
    except Exception:
        pass  # Silently fail to not break the application


def _safe_float(value, default=0.0):
    """Safely convert to float with validation"""
    if value is None or value == '':
        return default
    try:
        result = float(value)
        # Check for NaN or infinity
        if result != result or result == float('inf') or result == float('-inf'):
            return default
        return result
    except (ValueError, TypeError):
        return default


def _validate_and_normalize_trade(item, network, item_index=None):
    """Validate and normalize a Bybit trade item"""
    # #region agent log
    _debug_log('debug-session', 'run1', 'A', 'app.py:_validate_and_normalize_trade', 'Trade validation started', {
        'available_fields': list(item.keys())[:10],
        'orderId': item.get('orderId'),
        'execId': item.get('execId'),
        'tradeId': item.get('tradeId'),
        'symbol': item.get('symbol'),
        'item_index': item_index
    })
    # #endregion
    
    # Extract and validate external ID
    # For closed PnL positions, Bybit may not have orderId/execId/tradeId
    # Use a composite key: symbol + side + createdTime + closedPnl (to handle multiple closes of same position)
    external_id = (item.get('orderId') or item.get('execId') or item.get('tradeId') or 
                  item.get('orderLinkId'))
    
    # If no direct ID, create composite from symbol + side + createdTime + updatedTime + closedPnl
    # Use updatedTime to differentiate multiple closes of the same position
    # ALWAYS include item_index to ensure uniqueness within the same sync run
    if not external_id:
        symbol = item.get('symbol', '')
        side = item.get('side', '')
        created_time = str(item.get('createdTime') or item.get('createdTimeE3') or item.get('created_at') or '')
        updated_time = str(item.get('updatedTime') or item.get('updatedTimeE3') or item.get('updated_at') or '')
        closed_pnl = str(item.get('closedPnl') or item.get('pnl') or item.get('realizedPnl') or '')
        # Also try to use positionIdx or other unique fields
        position_idx = str(item.get('positionIdx') or item.get('positionId') or '')
        # CRITICAL: Always include item_index to ensure uniqueness
        # If item_index is None, use a hash of the full item as fallback
        if item_index is not None:
            # Use item_index to guarantee uniqueness
            external_id = f"{symbol}_{side}_{item_index}_{created_time}_{updated_time}" if symbol and side else f"trade_{item_index}_{created_time}"
        else:
            # Fallback: use hash of full item data
            import hashlib
            import json
            item_str = json.dumps(item, sort_keys=True, default=str)
            hash_suffix = hashlib.md5(item_str.encode()).hexdigest()[:12]
            external_id = f"{symbol}_{side}_{hash_suffix}" if symbol and side else f"trade_{hash_suffix}"
    if not external_id or external_id == 'None_None_None':
        # #region agent log
        print(f"[DEBUG] No external ID found. Available fields: {list(item.keys())}")
        _debug_log('debug-session', 'run1', 'A', 'app.py:_validate_and_normalize_trade', 'No external ID found - checking all fields', {
            'all_fields': list(item.keys()),
            'item_sample': {k: str(v)[:50] for k, v in list(item.items())[:10]}
        })
        # #endregion
        return None, "No external ID found"

    external_id = str(external_id).strip()
    if not external_id:
        return None, "Empty external ID"
    
    # #region agent log
    print(f"[DEBUG] External ID extracted: {external_id} (type: {type(external_id).__name__})")
    _debug_log('debug-session', 'run1', 'A', 'app.py:_validate_and_normalize_trade', 'External ID extracted', {
        'external_id': external_id,
        'external_id_type': type(external_id).__name__
    })
    # #endregion

    # Validate and normalize symbol
    symbol = item.get('symbol')
    if not symbol:
        return None, "Missing symbol"

    symbol = str(symbol).strip().upper()
    if not symbol:
        return None, "Empty symbol after strip"

    # Validate and normalize side
    side = str(item.get('side', '')).strip().lower()
    if side == 'buy':
        side = 'long'
    elif side == 'sell':
        side = 'short'
    elif not side:
        # If side is missing, try to infer from other fields
        return None, "Missing side"
    else:
        # Unknown side value
        side = 'long'  # default fallback

    # Extract and validate numeric fields
    qty = _safe_float(item.get('qty') or item.get('size'), 0.0)
    entry_price = _safe_float(
        item.get('avgEntryPrice') or item.get('entryPrice') or item.get('price'),
        0.0
    )
    exit_price = _safe_float(
        item.get('avgExitPrice') or item.get('exitPrice') or item.get('price'),
        0.0
    )
    pnl = _safe_float(
        item.get('closedPnl') or item.get('pnl') or item.get('realizedPnl'),
        0.0
    )

    # Validate required numeric fields
    if qty <= 0.0:
        return None, f"Invalid quantity: {qty}"
    if entry_price <= 0.0:
        return None, f"Invalid entry price: {entry_price}"
    if exit_price <= 0.0:
        return None, f"Invalid exit price: {exit_price}"

    # Parse timestamps
    current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    entry_time = _parse_bybit_time(
        item.get('createdTime') or item.get('createdTimeE3') or
        item.get('created_at') or item.get('timestamp')
    )
    exit_time = _parse_bybit_time(
        item.get('updatedTime') or item.get('updatedTimeE3') or
        item.get('updated_at') or item.get('timestamp')
    )

    # Ensure times are valid
    if not entry_time or not isinstance(entry_time, str) or not entry_time.strip():
        entry_time = current_time
    if not exit_time or not isinstance(exit_time, str) or not exit_time.strip():
        exit_time = entry_time

    # Return normalized trade data
    return {
        'external_id': external_id,
        'symbol': symbol,
        'side': side,
        'qty': qty,
        'entry_price': entry_price,
        'exit_price': exit_price,
        'pnl': pnl,
        'entry_time': entry_time,
        'exit_time': exit_time,
        'network': network
    }, None


@app.route('/api/save_bybit_credentials', methods=['POST'])
def save_bybit_credentials():
    """Save Bybit API credentials"""
    data = request.json
    api_key = data.get('api_key')
    api_secret = data.get('api_secret')
    network = (data.get('network') or 'mainnet').strip().lower()
    remember_me = data.get('remember_me', False)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Clear existing credentials
    cursor.execute('DELETE FROM api_credentials')

    # Insert new credentials
    cursor.execute(
        'INSERT INTO api_credentials (exchange, api_key, api_secret, network, remember_me) VALUES (?, ?, ?, ?, ?)',
        ('bybit', api_key, api_secret, network, 1 if remember_me else 0)
    )

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Credentials saved'})


@app.route('/api/get_bybit_credentials', methods=['GET'])
def get_bybit_credentials():
    """Get saved Bybit credentials (only if remember_me is enabled)"""
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
    """Get Bybit connection status"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM api_credentials LIMIT 1')
    creds = cursor.fetchone()
    conn.close()

    if creds and creds['api_key']:
        net = creds['network'] if 'network' in creds.keys() else 'mainnet'
        return jsonify({'connected': True, 'status': f'Configured ({net})'})
    return jsonify({'connected': False, 'status': 'Not configured'})


@app.route('/api/sync_bybit_trades', methods=['POST'])
def sync_bybit_trades():
    """Sync trades from Bybit - FIXED VERSION"""
    # #region agent log
    SYNC_VERSION = "v2.1_with_hash_fix"
    print(f"[DEBUG] SYNC FUNCTION CALLED - Version: {SYNC_VERSION}")
    print("[DEBUG] Log file should be at: c:\\Users\\Owner\\Desktop\\TJ\\.cursor\\debug.log")
    _debug_log('debug-session', 'run1', 'ALL', 'app.py:sync_bybit_trades', 'SYNC FUNCTION CALLED', {
        'function': 'sync_bybit_trades',
        'method': 'POST',
        'version': SYNC_VERSION
    })
    # #endregion
    
    print("\n" + "=" * 60)
    print("BYBIT SYNC STARTED")
    print("=" * 60)

    conn = None
    try:
        # Get credentials
        creds = _get_saved_bybit_credentials()
        if not creds or not creds.get('api_key') or not creds.get('api_secret'):
            return jsonify({
                'success': False,
                'message': 'Please save your Bybit API credentials first.',
                'trades_synced': 0
            }), 400

        network = (creds.get('network') or 'mainnet').strip().lower()
        print(f"Network: {network}")
        print(f"API Key: {creds['api_key'][:10]}...")
        
        # #region agent log
        _debug_log('debug-session', 'run1', 'B', 'app.py:sync_bybit_trades', 'Network value determined', {
            'network': network,
            'network_raw': creds.get('network'),
            'network_type': type(network).__name__
        })
        # #endregion

        # Create Bybit client
        try:
            client = _create_bybit_client(creds['api_key'], creds['api_secret'], network)
            print("Bybit client created successfully")
        except Exception as e:
            print(f"Failed to create Bybit client: {e}")
            return jsonify({
                'success': False,
                'message': f'Failed to connect to Bybit: {str(e)}',
                'trades_synced': 0
            }), 500

        # Fetch closed positions from Bybit
        print("\nFetching closed positions from Bybit...")
        all_items = []
        categories = ['linear', 'inverse']  # Try both categories

        for category in categories:
            cursor_val = None
            max_pages = 20
            pages = 0

            print(f"\nCategory: {category}")

            while pages < max_pages:
                pages += 1
                try:
                    kwargs = {'category': category, 'limit': 100}
                    if cursor_val:
                        kwargs['cursor'] = cursor_val

                    resp = client.get_closed_pnl(**kwargs)

                    if not resp:
                        print(f"  Page {pages}: Empty response")
                        break

                    result = resp.get('result', {})
                    items = result.get('list', [])

                    if not items:
                        print(f"  Page {pages}: No items")
                        break

                    print(f"  Page {pages}: Found {len(items)} items")
                    all_items.extend(items)

                    # Check for next page
                    next_cursor = result.get('nextPageCursor') or result.get('cursor')
                    if not next_cursor or next_cursor == cursor_val:
                        break
                    cursor_val = next_cursor

                except Exception as e:
                    print(f"  Page {pages}: API error - {e}")
                    break

        print(f"\nTotal items fetched: {len(all_items)}")
        
        # #region agent log
        if all_items:
            sample_item = all_items[0]
            print(f"[DEBUG] Sample item fields: {list(sample_item.keys())}")
            print(f"[DEBUG] Sample item data: {json.dumps(dict(sample_item), default=str, indent=2)[:500]}")
            # Save full response to file for inspection
            try:
                with open(r'c:\Users\Owner\Desktop\TJ\.cursor\bybit_response_sample.json', 'w', encoding='utf-8') as f:
                    json.dump(dict(sample_item), f, default=str, indent=2)
                print(f"[DEBUG] Saved sample response to .cursor\\bybit_response_sample.json")
            except Exception as e:
                print(f"[DEBUG] Failed to save sample: {e}")
            _debug_log('debug-session', 'run1', 'A', 'app.py:sync_bybit_trades', 'Sample API response item', {
                'total_items': len(all_items),
                'sample_fields': list(sample_item.keys()),
                'sample_orderId': sample_item.get('orderId'),
                'sample_execId': sample_item.get('execId'),
                'sample_tradeId': sample_item.get('tradeId'),
                'sample_symbol': sample_item.get('symbol'),
                'sample_full': dict(sample_item)
            })
        # #endregion

        if not all_items:
            return jsonify({
                'success': True,
                'message': 'No closed positions found on Bybit.',
                'trades_synced': 0
            })

        # Process and insert trades
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # #region agent log
        cursor.execute('SELECT external_id, network FROM bybit_imports LIMIT 10')
        existing_imports = cursor.fetchall()
        _debug_log('debug-session', 'run1', 'B', 'app.py:sync_bybit_trades', 'Existing bybit_imports table contents', {
            'existing_count': len(existing_imports),
            'sample_imports': [{'external_id': row[0], 'network': row[1], 'external_id_type': type(row[0]).__name__} for row in existing_imports[:5]]
        })
        # #endregion

        inserted = 0
        skipped = 0
        errors = []

        print("\nProcessing trades...")
        print(f"[DEBUG] Processing {len(all_items)} items from Bybit API")
        
        # Save all items to file for inspection
        try:
            with open(r'c:\Users\Owner\Desktop\TJ\.cursor\all_bybit_items.json', 'w', encoding='utf-8') as f:
                json.dump(all_items, f, default=str, indent=2)
            print(f"[DEBUG] Saved all {len(all_items)} items to .cursor\\all_bybit_items.json")
        except Exception as e:
            print(f"[DEBUG] Failed to save items: {e}")
        
        # Track external_ids seen in this sync run to detect duplicates within the same batch
        seen_external_ids = set()
        external_ids_generated = []  # Track all generated external_ids
        
        for i, item in enumerate(all_items, 1):
            try:
                print(f"[DEBUG] Processing item {i}/{len(all_items)}")
                # Validate and normalize trade - pass index to ensure uniqueness
                trade_data, error = _validate_and_normalize_trade(item, network, item_index=i)

                if error:
                    skipped += 1
                    print(f"[DEBUG] Item {i} validation failed: {error}")
                    # #region agent log
                    _debug_log('debug-session', 'run1', 'A', 'app.py:sync_bybit_trades', 'Trade validation failed', {
                        'item_index': i,
                        'error': error,
                        'item_keys': list(item.keys())[:15],
                        'item_sample': {k: str(v)[:100] for k, v in list(item.items())[:10]}
                    })
                    # #endregion
                    if len(errors) < 5:  # Only store first 5 errors
                        errors.append(f"Item {i}: {error}")
                    continue
                
                print(f"[DEBUG] Item {i} validated successfully. External ID: {trade_data['external_id']}")
                external_ids_generated.append({
                    'index': i,
                    'external_id': trade_data['external_id'],
                    'symbol': trade_data.get('symbol'),
                    'side': trade_data.get('side')
                })

                # #region agent log
                _debug_log('debug-session', 'run1', 'B', 'app.py:sync_bybit_trades', 'Before duplicate check', {
                    'external_id': trade_data['external_id'],
                    'external_id_type': type(trade_data['external_id']).__name__,
                    'network': network,
                    'network_type': type(network).__name__,
                    'symbol': trade_data.get('symbol'),
                    'seen_in_this_run': trade_data['external_id'] in seen_external_ids
                })
                # #endregion
                
                # Check if we've already seen this external_id in this sync run
                if trade_data['external_id'] in seen_external_ids:
                    skipped += 1
                    print(f"[DEBUG] DUPLICATE DETECTED in same run! External ID: {trade_data['external_id']}, Symbol: {trade_data.get('symbol')}")
                    print(f"[DEBUG] Seen external IDs so far: {list(seen_external_ids)}")
                    _debug_log('debug-session', 'run1', 'B', 'app.py:sync_bybit_trades', 'Duplicate in same sync run', {
                        'external_id': trade_data['external_id'],
                        'symbol': trade_data.get('symbol'),
                        'seen_ids': list(seen_external_ids)
                    })
                    continue
                
                # Check existing imports for this external_id (any network)
                cursor.execute('SELECT external_id, network FROM bybit_imports WHERE external_id = ?', (trade_data['external_id'],))
                existing_imports = cursor.fetchall()
                
                # #region agent log
                _debug_log('debug-session', 'run1', 'B', 'app.py:sync_bybit_trades', 'Existing imports found', {
                    'external_id': trade_data['external_id'],
                    'existing_count': len(existing_imports),
                    'existing_imports': [{'external_id': row[0], 'network': row[1]} for row in existing_imports[:3]]
                })
                # #endregion
                
                # Check if already imported with same network
                cursor.execute(
                    'SELECT 1 FROM bybit_imports WHERE external_id = ? AND network = ? LIMIT 1',
                    (trade_data['external_id'], network)
                )
                duplicate_found = cursor.fetchone()
                
                # #region agent log
                _debug_log('debug-session', 'run1', 'B', 'app.py:sync_bybit_trades', 'Duplicate check result', {
                    'external_id': trade_data['external_id'],
                    'network': network,
                    'is_duplicate': bool(duplicate_found),
                    'query_params': {'external_id': trade_data['external_id'], 'network': network}
                })
                # #endregion
                
                if duplicate_found:
                    skipped += 1
                    print(f"[DEBUG] DUPLICATE found in database! External ID: {trade_data['external_id']}, Network: {network}")
                    # #region agent log
                    _debug_log('debug-session', 'run1', 'B', 'app.py:sync_bybit_trades', 'Trade marked as duplicate (from DB) and skipped', {
                        'external_id': trade_data['external_id'],
                        'network': network,
                        'symbol': trade_data.get('symbol'),
                        'skipped_count': skipped
                    })
                    # #endregion
                    continue
                
                # Mark this external_id as seen in this run
                seen_external_ids.add(trade_data['external_id'])
                print(f"[DEBUG] Item {i} passed duplicate check. Will insert. External ID: {trade_data['external_id']}")

                # Insert trade into database
                cursor.execute('''
                    INSERT INTO trades (
                        symbol, asset, side, entry_price, exit_price, quantity,
                        entry_time, exit_time, pnl,
                        key_level, key_level_type, confirmation, model,
                        weekly_bias, daily_bias, notes, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade_data['symbol'],  # symbol column
                    trade_data['symbol'],  # asset column (same value)
                    trade_data['side'],
                    trade_data['entry_price'],
                    trade_data['exit_price'],
                    trade_data['qty'],
                    trade_data['entry_time'],
                    trade_data['exit_time'],
                    trade_data['pnl'],
                    None,  # key_level
                    None,  # key_level_type
                    None,  # confirmation
                    None,  # model
                    'neutral',  # weekly_bias
                    'neutral',  # daily_bias
                    f'Imported from Bybit ({network})',  # notes
                    'closed'  # status
                ))

                # Mark as imported
                cursor.execute(
                    'INSERT INTO bybit_imports (external_id, network) VALUES (?, ?)',
                    (trade_data['external_id'], network)
                )
                
                # #region agent log
                _debug_log('debug-session', 'run1', 'A', 'app.py:sync_bybit_trades', 'Trade successfully inserted', {
                    'external_id': trade_data['external_id'],
                    'network': network,
                    'symbol': trade_data.get('symbol'),
                    'inserted_count': inserted + 1
                })
                # #endregion

                inserted += 1

                if inserted % 10 == 0:
                    print(f"  Processed {inserted} trades...")

            except Exception as e:
                skipped += 1
                if len(errors) < 5:
                    errors.append(f"Item {i}: {str(e)}")
                continue

        # Commit all changes
        conn.commit()

        print(f"\n{'=' * 60}")
        print(f"SYNC COMPLETE")
        print(f"  Imported: {inserted}")
        print(f"  Skipped: {skipped}")
        if errors:
            print(f"  Errors (first 5):")
            for err in errors:
                print(f"    - {err}")
        print(f"{'=' * 60}\n")

        # Save external_ids to file for inspection
        try:
            with open(r'c:\Users\Owner\Desktop\TJ\.cursor\external_ids_generated.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'total_items': len(all_items),
                    'inserted': inserted,
                    'skipped': skipped,
                    'external_ids': external_ids_generated,
                    'seen_external_ids': list(seen_external_ids),
                    'errors': errors
                }, f, default=str, indent=2)
            print(f"[DEBUG] Saved external_ids analysis to .cursor\\external_ids_generated.json")
        except Exception as e:
            print(f"[DEBUG] Failed to save external_ids: {e}")
        
        # #region agent log
        _debug_log('debug-session', 'run1', 'ALL', 'app.py:sync_bybit_trades', 'SYNC COMPLETE - Summary', {
            'inserted': inserted,
            'skipped': skipped,
            'total_items': len(all_items),
            'errors_count': len(errors),
            'errors': errors[:3],
            'external_ids_generated': len(external_ids_generated),
            'seen_external_ids_count': len(seen_external_ids)
        })
        # #endregion
        
        message = f'Successfully imported {inserted} trade(s) from Bybit ({network}).'
        if skipped > 0:
            message += f' Skipped {skipped} invalid/duplicate trade(s).'

        return jsonify({
            'success': True,
            'message': message,
            'trades_synced': inserted,
            'skipped': skipped,
            'errors': errors if errors else None
        })

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

        if conn:
            conn.rollback()

        return jsonify({
            'success': False,
            'message': f'Sync failed: {str(e)}',
            'trades_synced': 0
        }), 500

    finally:
        if conn:
            conn.close()


@app.route('/api/bulk_fill_bias', methods=['POST'])
def bulk_fill_bias():
    """Bulk fill missing bias values"""
    data = request.json or {}
    weekly_value = (data.get('weekly_bias') or 'neutral').strip().lower()
    daily_value = (data.get('daily_bias') or 'neutral').strip().lower()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE trades SET weekly_bias = ? WHERE weekly_bias IS NULL OR TRIM(weekly_bias) = ''",
        (weekly_value,)
    )
    weekly_updated = cursor.rowcount

    cursor.execute(
        "UPDATE trades SET daily_bias = ? WHERE daily_bias IS NULL OR TRIM(daily_bias) = ''",
        (daily_value,)
    )
    daily_updated = cursor.rowcount

    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'weekly_updated': weekly_updated,
        'daily_updated': daily_updated,
        'weekly_bias': weekly_value,
        'daily_bias': daily_value
    })


# ================== UTILITY ROUTES ==================
@app.route('/api/test_post', methods=['POST'])
def test_post():
    """Test POST endpoint"""
    return jsonify({'status': 'ok', 'message': 'POST received'})


@app.route('/api/ping', methods=['GET'])
def ping():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'pong'})


@app.route('/api/test_bybit_sync', methods=['GET'])
def test_bybit_sync():
    """Test endpoint to check if sync code is loaded"""
    import os
    test_file = r'c:\Users\Owner\Desktop\TJ\.cursor\test_sync_loaded.txt'
    try:
        os.makedirs(os.path.dirname(test_file), exist_ok=True)
        with open(test_file, 'w') as f:
            f.write(f"Sync code loaded at: {datetime.utcnow()}\n")
        return jsonify({
            'status': 'ok',
            'message': 'Sync code is loaded',
            'test_file_created': os.path.exists(test_file)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ================== RUN APPLICATION ==================
if __name__ == '__main__':
    print("=" * 60)
    print("Trading Journal Application Starting...")
    print("=" * 60)
    print(f"Database: trading_journal.db")
    print(f"Server: http://localhost:5000")
    print("=" * 60)

    app.run(debug=True, port=5000, host='0.0.0.0')