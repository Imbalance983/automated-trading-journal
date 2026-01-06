from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
import os
import json

try:
    from pybit.unified_trading import HTTP as BybitHTTP
except Exception:
    try:
        from pybit import HTTP as BybitHTTP
    except Exception:
        BybitHTTP = None

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
CORS(app)


# ================== DATABASE INITIALIZATION ==================
def init_db():
    """Initialize database with all required tables"""
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    # Trades table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset TEXT NOT NULL,
        side TEXT NOT NULL,
        entry_price REAL NOT NULL,
        exit_price REAL,
        quantity REAL NOT NULL,
        entry_time TEXT NOT NULL,
        exit_time TEXT,
        pnl REAL,
        key_level TEXT,
        key_level_type TEXT,
        confirmation TEXT,
        model TEXT,
        weekly_bias TEXT DEFAULT 'neutral',
        daily_bias TEXT DEFAULT 'neutral',
        notes TEXT,
        screenshot_url TEXT,
        external_id TEXT,
        status TEXT DEFAULT 'open',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(external_id)
    )
    ''')

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
    """Get trades with statistics"""
    period = request.args.get('period', 'all')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status', 'closed')

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM trades WHERE status = ?"
    params = [status]

    if start_date and end_date:
        query += " AND DATE(entry_time) BETWEEN ? AND ?"
        params.extend([start_date, end_date])
    elif period == 'today':
        query += " AND DATE(entry_time) = DATE('now')"
    elif period == 'week':
        query += " AND entry_time >= DATE('now', '-7 days')"
    elif period == 'month':
        query += " AND strftime('%Y-%m', entry_time) = strftime('%Y-%m', 'now')"

    query += " ORDER BY entry_time DESC"
    cursor.execute(query, params)

    trades = [dict(row) for row in cursor.fetchall()]

    # Ensure bias fields
    for t in trades:
        t['weekly_bias'] = t.get('weekly_bias') or 'neutral'
        t['daily_bias'] = t.get('daily_bias') or 'neutral'

    # Calculate statistics only for closed trades
    if status == 'closed':
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if (t.get('pnl') or 0) > 0)
        losing_trades = sum(1 for t in trades if (t.get('pnl') or 0) < 0)
        total_pnl = sum(t.get('pnl') or 0 for t in trades)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        wins = [t['pnl'] for t in trades if (t.get('pnl') or 0) > 0]
        losses = [t['pnl'] for t in trades if (t.get('pnl') or 0) < 0]
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 0

        total_wins = sum(wins) if wins else 0
        total_losses = abs(sum(losses)) if losses else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0

        statistics = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'total_pnl': total_pnl,
            'win_rate': round(win_rate, 1),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2)
        }
    else:
        statistics = {}

    conn.close()

    return jsonify({
        'trades': trades,
        'statistics': statistics
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
                confirmation = ?, model = ?, weekly_bias = ?, daily_bias = ?, 
                notes = ?, screenshot_url = ?, status = ?
            WHERE id = ?
        ''', (
            data['asset'], data['side'], data['entry_price'], data.get('exit_price'),
            data['quantity'], data['entry_time'], data.get('exit_time'), data.get('pnl'),
            data.get('key_level'), data.get('key_level_type'), data.get('confirmation'),
            data.get('model'), data.get('weekly_bias', 'neutral'), 
            data.get('daily_bias', 'neutral'), data.get('notes'), 
            data.get('screenshot_url'), data.get('status', 'closed'), trade_id
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

    # Calculate P&L if trade is closed
    pnl = None
    status = data.get('status', 'closed')
    
    if status == 'closed' and data.get('exit_price'):
        if data['side'] == 'long':
            pnl = (float(data['exit_price']) - float(data['entry_price'])) * float(data['quantity'])
        else:
            pnl = (float(data['entry_price']) - float(data['exit_price'])) * float(data['quantity'])

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO trades (asset, side, entry_price, exit_price, quantity, entry_time, 
                          exit_time, pnl, key_level, key_level_type, confirmation, model, 
                          weekly_bias, daily_bias, notes, screenshot_url, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['asset'], data['side'], data['entry_price'], data.get('exit_price'),
        data['quantity'], data['entry_time'], data.get('exit_time'), pnl,
        data.get('key_level'), data.get('key_level_type'), data.get('confirmation'),
        data.get('model'), data.get('weekly_bias', 'neutral'), 
        data.get('daily_bias', 'neutral'), data.get('notes'), 
        data.get('screenshot_url'), status
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
        WHERE status = 'closed' AND pnl IS NOT NULL
        GROUP BY DATE(entry_time)
        ORDER BY trade_date
    ''')

    rows = cursor.fetchall()
    conn.close()

    events = []
    for row in rows:
        win_rate = (row['winning_trades'] / row['trade_count'] * 100) if row['trade_count'] > 0 else 0
        color = '#4CAF50' if row['daily_pnl'] > 0 else '#f44336' if row['daily_pnl'] < 0 else '#9E9E9E'

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
        WHERE DATE(entry_time) = ? AND status = 'closed'
        ORDER BY entry_time DESC
    ''', (date_str,))

    trades = [dict(row) for row in cursor.fetchall()]

    total_pnl = sum(t.get('pnl') or 0 for t in trades)
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if (t.get('pnl') or 0) > 0)
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


# ================== BYBIT INTEGRATION ==================
def _get_saved_bybit_credentials():
    """Retrieve saved Bybit credentials"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM api_credentials LIMIT 1')
    creds = cursor.fetchone()
    conn.close()
    return dict(creds) if creds else None


def _create_bybit_client(api_key, api_secret, network):
    """Create Bybit API client"""
    if BybitHTTP is None:
        raise RuntimeError('pybit is not installed')

    is_testnet = str(network or 'mainnet').strip().lower() == 'testnet'

    try:
        return BybitHTTP(testnet=is_testnet, api_key=api_key, api_secret=api_secret)
    except TypeError:
        endpoint = 'https://api-testnet.bybit.com' if is_testnet else 'https://api.bybit.com'
        return BybitHTTP(endpoint=endpoint, api_key=api_key, api_secret=api_secret)


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

    cursor.execute('DELETE FROM api_credentials')
    cursor.execute(
        'INSERT INTO api_credentials (exchange, api_key, api_secret, network, remember_me) VALUES (?, ?, ?, ?, ?)',
        ('bybit', api_key, api_secret, network, 1 if remember_me else 0)
    )

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Credentials saved'})


@app.route('/api/get_bybit_credentials', methods=['GET'])
def get_bybit_credentials():
    """Get saved Bybit credentials"""
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
            'network': creds.get('network', 'mainnet'),
            'remember_me': bool(creds['remember_me'])
        })
    return jsonify({'connected': False})


@app.route('/api/sync_bybit_trades', methods=['POST'])
def sync_bybit_trades():
    """Sync closed trades from Bybit"""
    print("\n" + "=" * 60)
    print("BYBIT SYNC STARTED")
    print("=" * 60)

    conn = None
    try:
        creds = _get_saved_bybit_credentials()
        if not creds or not creds.get('api_key'):
            return jsonify({
                'success': False,
                'message': 'Please save your Bybit API credentials first.',
                'trades_synced': 0
            }), 400

        network = (creds.get('network') or 'mainnet').strip().lower()
        
        # Create client
        client = _create_bybit_client(creds['api_key'], creds['api_secret'], network)
        print(f"Connected to Bybit ({network})")

        # Fetch closed positions
        all_items = []
        categories = ['linear', 'inverse']

        for category in categories:
            cursor_val = None
            pages = 0
            max_pages = 20

            while pages < max_pages:
                pages += 1
                try:
                    kwargs = {'category': category, 'limit': 100}
                    if cursor_val:
                        kwargs['cursor'] = cursor_val

                    resp = client.get_closed_pnl(**kwargs)
                    if not resp:
                        break

                    result = resp.get('result', {})
                    items = result.get('list', [])

                    if not items:
                        break

                    print(f"  {category} page {pages}: {len(items)} items")
                    all_items.extend(items)

                    next_cursor = result.get('nextPageCursor') or result.get('cursor')
                    if not next_cursor or next_cursor == cursor_val:
                        break
                    cursor_val = next_cursor

                except Exception as e:
                    print(f"  Error on page {pages}: {e}")
                    break

        print(f"\nTotal items fetched: {len(all_items)}")

        if not all_items:
            return jsonify({
                'success': True,
                'message': 'No closed positions found on Bybit.',
                'trades_synced': 0
            })

        # Process trades
        conn = get_db_connection()
        cursor = conn.cursor()

        inserted = 0
        skipped = 0

        for item in all_items:
            try:
                # Generate unique external_id
                external_id = (
                    item.get('orderId') or 
                    item.get('execId') or 
                    f"{item.get('symbol')}_{item.get('side')}_{item.get('createdTime')}"
                )

                # Check if already exists
                cursor.execute('SELECT 1 FROM trades WHERE external_id = ? LIMIT 1', (external_id,))
                if cursor.fetchone():
                    skipped += 1
                    continue

                # Extract data
                symbol = item.get('symbol', '').upper()
                side = 'long' if item.get('side', '').lower() == 'buy' else 'short'
                qty = float(item.get('qty') or item.get('size') or 0)
                entry_price = float(item.get('avgEntryPrice') or item.get('entryPrice') or 0)
                exit_price = float(item.get('avgExitPrice') or item.get('exitPrice') or 0)
                pnl = float(item.get('closedPnl') or item.get('pnl') or 0)

                if not symbol or qty <= 0 or entry_price <= 0 or exit_price <= 0:
                    skipped += 1
                    continue

                # Parse timestamps
                entry_time = datetime.utcfromtimestamp(
                    int(item.get('createdTime', 0)) / 1000
                ).strftime('%Y-%m-%d %H:%M:%S')
                
                exit_time = datetime.utcfromtimestamp(
                    int(item.get('updatedTime', 0)) / 1000
                ).strftime('%Y-%m-%d %H:%M:%S')

                # Insert trade
                cursor.execute('''
                    INSERT INTO trades (
                        asset, side, entry_price, exit_price, quantity,
                        entry_time, exit_time, pnl, weekly_bias, daily_bias,
                        notes, status, external_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol, side, entry_price, exit_price, qty,
                    entry_time, exit_time, pnl, 'neutral', 'neutral',
                    f'Imported from Bybit ({network})', 'closed', external_id
                ))

                inserted += 1

            except Exception as e:
                print(f"Error processing item: {e}")
                skipped += 1
                continue

        conn.commit()

        print(f"\n{'=' * 60}")
        print(f"SYNC COMPLETE")
        print(f"  Imported: {inserted}")
        print(f"  Skipped: {skipped}")
        print(f"{'=' * 60}\n")

        message = f'Successfully imported {inserted} trade(s) from Bybit ({network}).'
        if skipped > 0:
            message += f' Skipped {skipped} invalid/duplicate trade(s).'

        return jsonify({
            'success': True,
            'message': message,
            'trades_synced': inserted,
            'skipped': skipped
        })

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
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
        "UPDATE trades SET weekly_bias = ? WHERE weekly_bias IS NULL OR TRIM(weekly_bias) = '' OR weekly_bias = 'None'",
        (weekly_value,)
    )
    weekly_updated = cursor.rowcount

    cursor.execute(
        "UPDATE trades SET daily_bias = ? WHERE daily_bias IS NULL OR TRIM(daily_bias) = '' OR daily_bias = 'None'",
        (daily_value,)
    )
    daily_updated = cursor.rowcount

    conn.commit()
    conn.close()

    return jsonify({
        'success': True,
        'weekly_updated': weekly_updated,
        'daily_updated': daily_updated
    })


# ================== RUN APPLICATION ==================
if __name__ == '__main__':
    print("=" * 60)
    print("Trading Journal Application Starting...")
    print("=" * 60)
    print(f"Server: http://localhost:5000")
    print("=" * 60)

    app.run(debug=True, port=5000, host='0.0.0.0')