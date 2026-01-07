import sys
import io

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

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

    # Account balances table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS account_balances (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        sync_timestamp      TEXT NOT NULL,           -- ISO datetime when this snapshot was taken
        account_type        TEXT,                     -- 'UNIFIED', 'CONTRACT', 'SPOT', etc.
        coin                TEXT NOT NULL,
        wallet_balance      REAL,
        available_balance   REAL,
        equity              REAL,                     -- especially useful for unified
        unrealised_pnl      REAL,
        -- audit fields
        sync_id             INTEGER,                  -- optional: link to sync batch
        created_at          TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Positions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS positions (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        sync_timestamp      TEXT NOT NULL,
        symbol              TEXT NOT NULL,
        category            TEXT,                     -- linear, inverse, spot, option...
        side                TEXT,                     -- Buy / Sell
        size                REAL,
        avg_entry_price     REAL,
        mark_price          REAL,
        liq_price           REAL,
        unrealised_pnl      REAL,
        leverage            REAL,
        position_value      REAL,
        -- audit / reference
        sync_id             INTEGER,
        created_at          TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(sync_timestamp, symbol, category)      -- prevent exact same snapshot duplicate
    )
    ''')

    # Open orders table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS open_orders (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        sync_timestamp      TEXT NOT NULL,
        symbol              TEXT,
        category            TEXT,
        order_id            TEXT,
        order_link_id       TEXT,
        side                TEXT,
        order_type          TEXT,
        qty                 REAL,
        price               REAL,
        trigger_price       REAL,
        status              TEXT,
        created_time        TEXT,
        updated_time        TEXT,
        sync_id             INTEGER,
        created_at          TEXT DEFAULT CURRENT_TIMESTAMP
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


# ================== EXTENDED DATA SYNC ==================
@app.route('/api/sync_extended_data', methods=['POST'])
def sync_extended_data():
    """Comprehensive full account snapshot from Bybit"""
    print("\n" + "=" * 60)
    print("FULL ACCOUNT SNAPSHOT STARTED")
    print("=" * 60)

    conn = None
    try:
        creds = _get_saved_bybit_credentials()
        if not creds or not creds.get('api_key'):
            return jsonify({
                'success': False,
                'message': 'Please save your Bybit API credentials first.'
            }), 400

        network = (creds.get('network') or 'mainnet').strip().lower()
        
        # Create client
        client = _create_bybit_client(creds['api_key'], creds['api_secret'], network)
        print(f"Connected to Bybit ({network})")

        conn = get_db_connection()
        cursor = conn.cursor()

        now_iso = datetime.now().isoformat()
        sync_id = int(datetime.now().timestamp())
        
        # 1. WALLET BALANCES (most important)
        print("  Fetching wallet balances...")
        try:
            bal_resp = client.get_wallet_balance(accountType="UNIFIED")
            if bal_resp and bal_resp.get('retCode') == 0 and bal_resp.get('result'):
                account_list = bal_resp['result']['list']
                balances_saved = 0
                
                for account in account_list:
                    account_type = account.get('accountType', 'UNIFIED')
                    coin_list = account.get('coin', [])
                    
                    for coin_data in coin_list:
                        if coin_data.get('coin'):
                            cursor.execute('''
                                INSERT OR REPLACE INTO account_balances 
                                (sync_timestamp, account_type, coin, wallet_balance, available_balance, equity, unrealised_pnl, sync_id)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                now_iso, account_type, coin_data['coin'],
                                float(coin_data.get('walletBalance', 0)),
                                float(coin_data.get('availableToWithdraw', 0)),
                                float(coin_data.get('equity', 0)),
                                float(coin_data.get('unrealisedPnl', 0)),
                                sync_id
                            ))
                            balances_saved += 1
                
                print(f"  [OK] Saved {balances_saved} balance records from {len(account_list)} accounts")
            else:
                print(f"  [ERROR] Balance fetch failed: {bal_resp.get('retMsg', 'Unknown error')}")

        except Exception as e:
            print(f"  [ERROR] Balance fetch error: {e}")

        # 2. CURRENT POSITIONS (critical for trading view)
        print("  Fetching positions...")
        try:
            categories = ['linear', 'inverse']  # Add 'spot' if needed
            positions_saved = 0
            
            for category in categories:
                pos_resp = client.get_positions(category=category)
                if pos_resp and pos_resp.get('retCode') == 0 and pos_resp.get('result'):
                    position_list = pos_resp['result']['list']

                    for p in position_list:
                        if float(p.get('size', 0)) == 0:
                            continue  # Skip empty positions

                        cursor.execute('''
                            INSERT OR REPLACE INTO positions
                            (sync_timestamp, symbol, category, side, size, avg_entry_price, mark_price,
                             liq_price, unrealised_pnl, leverage, position_value, sync_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            now_iso, p.get('symbol', ''), category,
                            p.get('side', ''), float(p.get('size', 0)),
                            float(p.get('avgPrice', 0)), float(p.get('markPrice', 0)),
                            float(p.get('liqPrice', 0)), float(p.get('unrealisedPnl', 0)),
                            float(p.get('leverage', 0)), float(p.get('positionValue', 0)),
                            sync_id
                        ))
                        positions_saved += 1

                    print(f"  [OK] Saved {positions_saved} {category} positions")
                else:
                    print(f"  [ERROR] {category} positions fetch failed: {pos_resp.get('retMsg', 'Unknown error')}")

        except Exception as e:
            print(f"  [ERROR] Positions fetch error: {e}")

        # 3. OPEN ORDERS (optional but useful)
        print("  Fetching open orders...")
        try:
            orders_resp = client.get_open_orders(category="linear", limit=100)
            if orders_resp and orders_resp.get('retCode') == 0 and orders_resp.get('result'):
                order_list = orders_resp['result']['list']
                orders_saved = 0
                
                for order in order_list:
                    if order.get('orderId'):
                        cursor.execute('''
                            INSERT OR REPLACE INTO open_orders 
                            (sync_timestamp, symbol, category, order_id, order_link_id, side, order_type,
                             qty, price, trigger_price, status, created_time, updated_time, sync_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            now_iso, order.get('symbol', ''), 'linear',
                            order.get('orderId', ''), order.get('orderLinkId', ''),
                            order.get('side', ''), order.get('orderType', ''),
                            float(order.get('qty', 0)), float(order.get('price', 0)),
                            float(order.get('triggerPrice', 0)), order.get('status', ''),
                            order.get('createdTime', ''), order.get('updatedTime', ''),
                            sync_id
                        ))
                        orders_saved += 1
                
                print(f"  [OK] Saved {orders_saved} open orders")
            else:
                print(f"  [ERROR] Orders fetch failed: {orders_resp.get('retMsg', 'Unknown error')}")

        except Exception as e:
            print(f"  [ERROR] Orders fetch error: {e}")

        conn.commit()

        print(f"\n{'=' * 60}")
        print(f"FULL SNAPSHOT COMPLETE")
        print(f"  Timestamp: {now_iso}")
        print(f"  Sync ID: {sync_id}")
        print(f"  Balances: {balances_saved if 'balances_saved' in locals() else 0}")
        print(f"  Positions: {positions_saved if 'positions_saved' in locals() else 0}")
        print(f"  Orders: {orders_saved if 'orders_saved' in locals() else 0}")
        print(f"{'=' * 60}\n")

        return jsonify({
            'success': True,
            'message': f'Full account snapshot saved successfully',
            'timestamp': now_iso,
            'sync_id': sync_id,
            'balances_saved': balances_saved,
            'positions_saved': positions_saved,
            'orders_saved': orders_saved
        })

    except Exception as e:
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        print(f"\nFATAL ERROR: {error_msg}")
        if conn:
            conn.rollback()

        return jsonify({
            'success': False,
            'message': f'Full snapshot failed: {error_msg}'
        }), 500

    finally:
        if conn:
            conn.close()


# ================== API ENDPOINTS FOR EXTENDED DATA ==================
@app.route('/api/account_balances', methods=['GET'])
def get_account_balances():
    """Get account balances"""
    # Check if Bybit is connected
    creds = _get_saved_bybit_credentials()
    if not creds or not creds.get('api_key'):
        return jsonify({
            'balances': [],
            'message': 'No Bybit connection - please connect your API first'
        })
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM account_balances 
        ORDER BY sync_timestamp DESC, coin
    ''')
    
    balances = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'balances': balances})


@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Get current positions"""
    # Check if Bybit is connected
    creds = _get_saved_bybit_credentials()
    if not creds or not creds.get('api_key'):
        return jsonify({
            'positions': [],
            'message': 'No Bybit connection - please connect your API first'
        })
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM positions 
        WHERE sync_timestamp = (
            SELECT MAX(sync_timestamp) FROM positions
        )
        ORDER BY symbol
    ''')
    
    positions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'positions': positions})


@app.route('/api/open_orders', methods=['GET'])
def get_open_orders():
    """Get open orders"""
    # Check if Bybit is connected
    creds = _get_saved_bybit_credentials()
    if not creds or not creds.get('api_key'):
        return jsonify({
            'orders': [],
            'message': 'No Bybit connection - please connect your API first'
        })
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM open_orders 
        WHERE sync_timestamp = (
            SELECT MAX(sync_timestamp) FROM open_orders
        )
        ORDER BY created_time DESC
    ''')
    
    orders = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'orders': orders})


# ================== ORIGINAL TRADES SYNC ==================
@app.route('/api/sync_bybit_trades', methods=['POST'])
@app.route('/api/sync/bybit', methods=['POST'])
def sync_bybit_trades():
    """Sync closed trades from Bybit"""
    # Write to both terminal AND file for debugging
    log_file = open('sync_debug.txt', 'w', encoding='utf-8')

    def log(msg):
        print(msg)
        log_file.write(msg + '\n')
        log_file.flush()

    log("\n" + "=" * 60)
    log("BYBIT SYNC STARTED")
    log("=" * 60)
    sys.stdout.flush()

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

        # Fetch closed positions from last 90 days in 7-day chunks (Bybit limitation)
        all_items = []
        categories = ['linear', 'inverse']

        # Calculate time ranges: Split 90 days into 7-day chunks
        now = datetime.now()
        days_back = 90
        chunk_days = 6  # Use 6 days to be safe (7 day limit)

        log(f"Fetching trades from last {days_back} days in {chunk_days}-day chunks...")

        for category in categories:
            log(f"\nFetching {category} trades...")

            # Loop through time chunks
            for chunk in range(0, days_back, chunk_days):
                chunk_end = now - timedelta(days=chunk)
                chunk_start = now - timedelta(days=min(chunk + chunk_days, days_back))

                end_time = int(chunk_end.timestamp() * 1000)
                start_time = int(chunk_start.timestamp() * 1000)

                log(f"  Time range: {chunk_start.strftime('%Y-%m-%d')} to {chunk_end.strftime('%Y-%m-%d')}")

                cursor_val = None
                pages = 0
                max_pages = 10

                while pages < max_pages:
                    pages += 1
                    try:
                        kwargs = {
                            'category': category,
                            'limit': 100,
                            'startTime': start_time,
                            'endTime': end_time
                        }
                        if cursor_val:
                            kwargs['cursor'] = cursor_val

                        # CRITICAL: Must specify accountType for Unified Trading Account
                        kwargs['accountType'] = 'UNIFIED'
                        resp = client.get_closed_pnl(**kwargs)
                        if not resp:
                            log(f"    {category}: No response from API")
                            break

                        if resp.get('retCode') != 0:
                            log(f"    {category} error: {resp.get('retMsg')}")
                            break

                        result = resp.get('result', {})
                        items = result.get('list', [])

                        if not items:
                            if pages == 1:
                                log(f"    No items in this time range")
                            break

                        log(f"    Page {pages}: {len(items)} items found")
                        all_items.extend(items)

                        next_cursor = result.get('nextPageCursor') or result.get('cursor')
                        if not next_cursor or next_cursor == cursor_val:
                            break
                        cursor_val = next_cursor

                    except Exception as e:
                        log(f"    Error on page {pages}: {e}")
                        break

        log(f"\nTotal items fetched: {len(all_items)}")

        if all_items:
            log(f"\nSample item structure:")
            log(json.dumps(all_items[0], indent=2))

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
                    log(f"  Skipping duplicate: {external_id}")
                    skipped += 1
                    continue

                # Extract data - be flexible with field names
                symbol = item.get('symbol', '').upper()
                side = 'long' if item.get('side', '').lower() == 'buy' else 'short'
                qty = float(item.get('qty') or item.get('size') or item.get('closedSize') or 0)

                # Try multiple field names for prices
                entry_price = float(item.get('avgEntryPrice') or item.get('entryPrice') or item.get('avgPrice') or 0)
                exit_price = float(item.get('avgExitPrice') or item.get('exitPrice') or item.get('avgPrice') or 0)
                pnl = float(item.get('closedPnl') or item.get('pnl') or 0)

                log(f"\n  Processing: {symbol} | side={side} | qty={qty} | entry={entry_price} | exit={exit_price} | pnl={pnl}")

                # Less strict validation - only require symbol and pnl
                if not symbol or pnl == 0:
                    log(f"  REJECTED: symbol={symbol!r} pnl={pnl}")
                    skipped += 1
                    continue

                # Calculate exit price from P&L if missing
                if exit_price == 0 and entry_price > 0 and qty > 0:
                    if side == 'long':
                        exit_price = entry_price + (pnl / qty)
                    else:
                        exit_price = entry_price - (pnl / qty)

                # Parse timestamps
                entry_time = datetime.utcfromtimestamp(
                    int(item.get('createdTime', 0)) / 1000
                ).strftime('%Y-%m-%d %H:%M:%S')

                exit_time = datetime.utcfromtimestamp(
                    int(item.get('updatedTime', 0)) / 1000
                ).strftime('%Y-%m-%d %H:%M:%S')

                log(f"  Timestamps: entry={entry_time}, exit={exit_time}")

                # Calculate pnl_percentage
                pnl_percentage = (pnl / (entry_price * qty) * 100) if (entry_price > 0 and qty > 0) else 0

                log(f"  Attempting database insert with symbol={symbol}, pnl%={pnl_percentage:.2f}")

                # Get current timestamp
                created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Insert trade - include ALL required NOT NULL columns
                cursor.execute('''
                    INSERT INTO trades (
                        symbol, asset, side, entry_price, exit_price, quantity,
                        entry_time, exit_time, pnl, pnl_percentage, weekly_bias, daily_bias,
                        notes, status, external_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol, symbol, side, entry_price, exit_price, qty,
                    entry_time, exit_time, pnl, pnl_percentage, 'neutral', 'neutral',
                    f'Imported from Bybit ({network})', 'closed', external_id, created_at
                ))

                inserted += 1
                log(f"  ✓ Successfully inserted trade!")

            except Exception as e:
                log(f"  ERROR processing item: {e}")
                skipped += 1
                continue

        conn.commit()

        print(f"\n{'=' * 60}")
        print(f"EXTENDED SYNC COMPLETE")
        print(f"  Imported: {inserted}")
        print(f"  Skipped: {skipped}")

        return jsonify({
            'success': True,
            'message': f'Successfully imported {inserted} trade(s) from Bybit ({network}).',
            'trades_synced': inserted,
            'skipped': skipped
        })

    except Exception as e:
        error_msg = str(e).encode('ascii', 'replace').decode('ascii')
        print(f"\nFATAL ERROR: {error_msg}")
        if conn:
            conn.rollback()

        return jsonify({
            'success': False,
            'message': f'Extended sync failed: {error_msg}'
        }), 500

    finally:
        if conn:
            conn.close()


# ================== API ENDPOINTS FOR ORIGINAL TRADES ==================
@app.route('/api/save_bybit_credentials', methods=['POST'])
def save_bybit_credentials():
    """Save Bybit API credentials - always remembers credentials"""
    data = request.json
    api_key = data.get('api_key')
    api_secret = data.get('api_secret')
    network = (data.get('network') or 'mainnet').strip().lower()
    remember_me = data.get('remember_me', True)  # Default to True

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM api_credentials')
    cursor.execute(
        'INSERT INTO api_credentials (exchange, api_key, api_secret, network, remember_me) VALUES (?, ?, ?, ?, ?)',
        ('bybit', api_key, api_secret, network, 1 if remember_me else 0)
    )

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Credentials saved and will be remembered'})


@app.route('/api/get_bybit_credentials', methods=['GET'])
def get_bybit_credentials():
    """Get saved Bybit credentials"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM api_credentials ORDER BY created_at DESC LIMIT 1')
    creds = cursor.fetchone()
    conn.close()

    if creds and creds['api_key']:
        # Convert Row to dict to use .get() method
        creds_dict = dict(creds)
        return jsonify({
            'connected': True,
            'api_key': creds_dict['api_key'],
            'api_secret': creds_dict['api_secret'],
            'network': creds_dict.get('network', 'mainnet'),
            'remember_me': bool(creds_dict.get('remember_me', 0))
        })
    return jsonify({'connected': False})


# ================== DEBUG ENDPOINT ==================
@app.route('/api/test_output', methods=['GET'])
def test_output():
    """Simple test to verify stdout works"""
    print("\n" + "=" * 60)
    print("TEST OUTPUT - If you see this, stdout is working!")
    print("=" * 60)
    sys.stdout.flush()
    return jsonify({'message': 'Check terminal for output'})


@app.route('/api/debug_sync', methods=['GET'])
def debug_sync():
    """Debug endpoint to test ALL possible data sources"""
    try:
        creds = _get_saved_bybit_credentials()
        if not creds or not creds.get('api_key'):
            return jsonify({'error': 'No credentials saved'})

        network = (creds.get('network') or 'mainnet').strip().lower()
        client = _create_bybit_client(creds['api_key'], creds['api_secret'], network)

        results = {}

        # 1. Try get_closed_pnl (what we're currently using)
        try:
            resp = client.get_closed_pnl(category='linear', limit=10, accountType='UNIFIED')
            results['closed_pnl_linear'] = {
                'retCode': resp.get('retCode'),
                'retMsg': resp.get('retMsg'),
                'count': len(resp.get('result', {}).get('list', [])),
                'sample': resp.get('result', {}).get('list', [])[:1] if resp.get('result', {}).get('list') else []
            }
        except Exception as e:
            results['closed_pnl_linear'] = {'error': str(e)}

        # 2. Try get_executions (actual trade fills)
        try:
            resp = client.get_executions(category='linear', limit=10)
            results['executions_linear'] = {
                'retCode': resp.get('retCode'),
                'retMsg': resp.get('retMsg'),
                'count': len(resp.get('result', {}).get('list', [])),
                'sample': resp.get('result', {}).get('list', [])[:1] if resp.get('result', {}).get('list') else []
            }
        except Exception as e:
            results['executions_linear'] = {'error': str(e)}

        # 3. Try order history
        try:
            resp = client.get_order_history(category='linear', limit=10)
            results['order_history_linear'] = {
                'retCode': resp.get('retCode'),
                'retMsg': resp.get('retMsg'),
                'count': len(resp.get('result', {}).get('list', [])),
                'sample': resp.get('result', {}).get('list', [])[:1] if resp.get('result', {}).get('list') else []
            }
        except Exception as e:
            results['order_history_linear'] = {'error': str(e)}

        # 4. Try current positions
        try:
            resp = client.get_positions(category='linear')
            results['positions_linear'] = {
                'retCode': resp.get('retCode'),
                'retMsg': resp.get('retMsg'),
                'count': len(resp.get('result', {}).get('list', [])),
                'sample': resp.get('result', {}).get('list', [])[:1] if resp.get('result', {}).get('list') else []
            }
        except Exception as e:
            results['positions_linear'] = {'error': str(e)}

        return jsonify({
            'network': network,
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)})


# ================== CALENDAR & ANALYTICS ==================
@app.route('/api/calendar_data', methods=['GET'])
def get_calendar_data():
    """Get calendar data with daily P&L"""
    # Check if Bybit is connected
    creds = _get_saved_bybit_credentials()
    if not creds or not creds.get('api_key'):
        return jsonify([])
    
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


# ================== TRADE MANAGEMENT ==================
@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Get trades with statistics"""
    # Check if Bybit is connected
    creds = _get_saved_bybit_credentials()
    if not creds or not creds.get('api_key'):
        return jsonify({
            'trades': [],
            'statistics': {},
            'message': 'No Bybit connection - please connect your API first'
        })
    
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
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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


# ================== RUN APPLICATION ==================
if __name__ == '__main__':
    print("=" * 60)
    print("Trading Journal Application Starting...")
    print("=" * 60)
    print(f"Server: http://localhost:5000")
    print("=" * 60)

    app.run(debug=True, port=5000, host='0.0.0.0')
