import sys
import io

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from flask import Flask, render_template, request, jsonify, session, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import sqlite3
from datetime import datetime, timedelta
import os
import json
import uuid

try:
    from pybit.unified_trading import HTTP as BybitHTTP
    # Enforce unified trading usage
    if 'unified_trading' not in BybitHTTP.__module__:
        raise RuntimeError('Unified Trading client not available - please upgrade pybit')
except Exception:
    try:
        from pybit import HTTP as BybitHTTP
        raise RuntimeError('Old pybit version detected - please upgrade: pip install --upgrade pybit')
    except Exception:
        BybitHTTP = None

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here-change-in-production')
CORS(app)

# Screenshot upload configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'screenshots')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create screenshots folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ================== DATABASE INITIALIZATION ==================
def init_db():
    """Initialize database with all required tables"""
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    # Users table for multi-user support
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Trades table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        asset TEXT NOT NULL,
        side TEXT NOT NULL,
        entry_price REAL NOT NULL,
        exit_price REAL,
        stop_loss REAL,
        take_profit REAL,
        quantity REAL NOT NULL,
        entry_time TEXT NOT NULL,
        exit_time TEXT,
        pnl REAL,
        risk_reward_ratio REAL,
        position_size_pct REAL,
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
        UNIQUE(user_id, external_id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # API credentials table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS api_credentials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        exchange TEXT NOT NULL,
        api_key TEXT,
        api_secret TEXT,
        network TEXT DEFAULT 'mainnet',
        remember_me INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # Create default user if doesn't exist
    cursor.execute('INSERT OR IGNORE INTO users (id, name) VALUES (1, "default")')
    conn.commit()

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

    # Add new columns if they don't exist (migration)
    try:
        cursor.execute("ALTER TABLE trades ADD COLUMN pnl_percentage REAL DEFAULT 0")
        print("✅ Added pnl_percentage column")
    except:
        print("⚠️ pnl_percentage column already exists or migration failed")
    
    try:
        cursor.execute("ALTER TABLE trades ADD COLUMN entry_type TEXT")
        print("✅ Added entry_type column")
    except:
        print("⚠️ entry_type column already exists or migration failed")
    try:
        cursor.execute("ALTER TABLE trades ADD COLUMN take_profit REAL")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE trades ADD COLUMN stop_loss REAL")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE trades ADD COLUMN risk_reward_ratio REAL")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE trades ADD COLUMN position_size_pct REAL")
    except:
        pass

    # Add user_id column to api_credentials if it doesn't exist
    try:
        cursor.execute("ALTER TABLE api_credentials ADD COLUMN user_id INTEGER DEFAULT 1")
    except:
        pass

    # Add entry column to trades table
    try:
        cursor.execute("ALTER TABLE trades ADD COLUMN entry TEXT")
    except:
        pass

    # Create child tables with UNIQUE constraints
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trade_key_levels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_id INTEGER NOT NULL,
        level TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trade_id) REFERENCES trades(id) ON DELETE CASCADE,
        UNIQUE(trade_id, level)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trade_confirmations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_id INTEGER NOT NULL,
        confirmation TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trade_id) REFERENCES trades(id) ON DELETE CASCADE,
        UNIQUE(trade_id, confirmation)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trade_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_id INTEGER NOT NULL,
        entry TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trade_id) REFERENCES trades(id) ON DELETE CASCADE,
        UNIQUE(trade_id, entry)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trade_models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_id INTEGER NOT NULL,
        model TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trade_id) REFERENCES trades(id) ON DELETE CASCADE,
        UNIQUE(trade_id, model)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS trade_screenshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_id INTEGER NOT NULL,
        screenshot_url TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (trade_id) REFERENCES trades(id) ON DELETE CASCADE
    )
    ''')

    conn.commit()
    conn.close()


init_db()


def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect('trading_journal.db')
    conn.row_factory = sqlite3.Row

    # Ensure api_credentials table exists (migration for old databases)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS api_credentials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        exchange TEXT NOT NULL,
        api_key TEXT,
        api_secret TEXT,
        network TEXT DEFAULT 'mainnet',
        remember_me INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    conn.commit()

    return conn


def get_current_user_id():
    """Get current user ID from session, default to 1"""
    return session.get('user_id', 1)


def set_current_user(user_id):
    """Set current user in session"""
    session['user_id'] = user_id


def calculate_risk_reward_ratio(entry_price, stop_loss, take_profit, side):
    """Calculate risk/reward ratio for a trade"""
    if not entry_price or not stop_loss or not take_profit:
        return None

    entry_price = float(entry_price)
    stop_loss = float(stop_loss)
    take_profit = float(take_profit)

    if side.lower() == 'long':
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
    else:  # short
        risk = stop_loss - entry_price
        reward = entry_price - take_profit

    if risk <= 0:
        return None

    rr_ratio = reward / risk
    return round(rr_ratio, 2)


# ================== TRADE DETAILS HELPER FUNCTIONS ==================
def get_trade_details(trade_id):
    """Get all related details for a trade (key levels, confirmations, entries, models, screenshots)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    details = {
        'key_levels': [],
        'confirmations': [],
        'entries': [],
        'models': [],
        'screenshots': []
    }

    # Get key levels
    cursor.execute('SELECT level FROM trade_key_levels WHERE trade_id = ? ORDER BY created_at', (trade_id,))
    details['key_levels'] = [row['level'] for row in cursor.fetchall()]

    # Get confirmations
    cursor.execute('SELECT confirmation FROM trade_confirmations WHERE trade_id = ? ORDER BY created_at', (trade_id,))
    details['confirmations'] = [row['confirmation'] for row in cursor.fetchall()]

    # Get entries
    cursor.execute('SELECT entry FROM trade_entries WHERE trade_id = ? ORDER BY created_at', (trade_id,))
    details['entries'] = [row['entry'] for row in cursor.fetchall()]

    # Get models
    cursor.execute('SELECT model FROM trade_models WHERE trade_id = ? ORDER BY created_at', (trade_id,))
    details['models'] = [row['model'] for row in cursor.fetchall()]

    # Get screenshots
    cursor.execute('SELECT screenshot_url FROM trade_screenshots WHERE trade_id = ? ORDER BY created_at', (trade_id,))
    details['screenshots'] = [row['screenshot_url'] for row in cursor.fetchall()]

    conn.close()
    return details


def save_trade_details(trade_id, key_levels=None, confirmations=None, entries=None, models=None, screenshots=None):
    """Save trade details (replaces existing data)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Clear existing data
        cursor.execute('DELETE FROM trade_key_levels WHERE trade_id = ?', (trade_id,))
        cursor.execute('DELETE FROM trade_confirmations WHERE trade_id = ?', (trade_id,))
        cursor.execute('DELETE FROM trade_entries WHERE trade_id = ?', (trade_id,))
        cursor.execute('DELETE FROM trade_models WHERE trade_id = ?', (trade_id,))
        cursor.execute('DELETE FROM trade_screenshots WHERE trade_id = ?', (trade_id,))

        # Insert new data
        if key_levels:
            for level in key_levels:
                if level and level.strip():
                    cursor.execute(
                        'INSERT INTO trade_key_levels (trade_id, level) VALUES (?, ?)',
                        (trade_id, level.strip())
                    )

        if confirmations:
            for confirmation in confirmations:
                if confirmation and confirmation.strip():
                    cursor.execute(
                        'INSERT INTO trade_confirmations (trade_id, confirmation) VALUES (?, ?)',
                        (trade_id, confirmation.strip())
                    )

        if entries:
            for entry in entries:
                if entry and entry.strip():
                    cursor.execute(
                        'INSERT INTO trade_entries (trade_id, entry) VALUES (?, ?)',
                        (trade_id, entry.strip())
                    )

        if models:
            for model in models:
                if model and model.strip():
                    cursor.execute(
                        'INSERT INTO trade_models (trade_id, model) VALUES (?, ?)',
                        (trade_id, model.strip())
                    )

        if screenshots:
            for screenshot in screenshots:
                if screenshot and screenshot.strip():
                    cursor.execute(
                        'INSERT INTO trade_screenshots (trade_id, screenshot_url) VALUES (?, ?)',
                        (trade_id, screenshot.strip())
                    )

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.rollback()
        conn.close()
        raise e


# ================== USER MANAGEMENT ==================
@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, created_at FROM users ORDER BY id')
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()

    current_user_id = get_current_user_id()
    return jsonify({'users': users, 'current_user_id': current_user_id})


@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user"""
    data = request.json
    name = data.get('name')

    if not name:
        return jsonify({'success': False, 'error': 'Name required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('INSERT INTO users (name) VALUES (?)', (name,))
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Automatically switch to new user
        set_current_user(user_id)

        return jsonify({'success': True, 'user_id': user_id, 'name': name})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'error': 'Name already exists'}), 400


@app.route('/api/switch_user/<int:user_id>', methods=['POST'])
def switch_user(user_id):
    """Switch to a different user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404

    set_current_user(user_id)
    return jsonify({'success': True, 'user_id': user_id, 'name': user['name']})


# ================== BASIC ROUTES ==================
@app.route('/test')
def test():
    """Test route"""
    return "Working!"

@app.route('/')
def index():
    """Render main application page"""
    return render_template('single_page.html')


# ================== BYBIT INTEGRATION ==================
def _get_saved_bybit_credentials():
    """Retrieve saved Bybit credentials for current user"""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM api_credentials WHERE user_id = ? AND exchange = ? LIMIT 1', (user_id, 'bybit'))
    creds = cursor.fetchone()
    conn.close()
    return dict(creds) if creds else None


def _create_bybit_client(api_key, api_secret, network):
    """Create Bybit API client"""
    if BybitHTTP is None:
        raise RuntimeError('pybit is not installed')

    # Harden network detection
    network = str(network or '').lower()
    is_testnet = 'test' in network

    try:
        return BybitHTTP(
            testnet=is_testnet, 
            api_key=api_key, 
            api_secret=api_secret,
            recv_window=5000
        )
    except TypeError:
        endpoint = 'https://api-testnet.bybit.com' if is_testnet else 'https://api.bybit.com'
        return BybitHTTP(
            endpoint=endpoint, 
            api_key=api_key, 
            api_secret=api_secret,
            recv_window=5000
        )


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
        
        # Initialize counters to prevent UnboundLocalError
        balances_saved = positions_saved = orders_saved = 0
        
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
            orders_resp = client.get_open_orders(category="linear", limit=100, accountType='UNIFIED')
            if orders_resp and orders_resp.get('retCode') == 0 and orders_resp.get('result'):
                order_list = orders_resp['result']['list']
                orders_saved = 0
                
                for order in order_list:
                    if order.get('orderId'):
                        cursor.execute('''
                            INSERT OR REPLACE INTO open_orders 
                            (sync_timestamp, symbol, category, order_id, order_link_id, side, order_type,
                             qty, price, trigger_price, status, created_time, updated_time, sync_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        WHERE sync_id = (
            SELECT MAX(sync_id) FROM positions
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
        WHERE sync_id = (
            SELECT MAX(sync_id) FROM open_orders
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
    user_id = get_current_user_id()

    # Write to both terminal AND file for debugging
    log_file = open('sync_debug.txt', 'w', encoding='utf-8')

    def log(msg):
        print(msg)
        log_file.write(msg + '\n')
        log_file.flush()

    log("\n" + "=" * 60)
    log(f"BYBIT SYNC STARTED (User ID: {user_id})")
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

                # Check if already exists for this user (including deleted trades to prevent re-import)
                # IMPORTANT: Do NOT check is_deleted = 0 here - we want to prevent re-importing deleted trades
                cursor.execute('SELECT 1 FROM trades WHERE user_id = ? AND external_id = ? LIMIT 1', (user_id, external_id))
                if cursor.fetchone():
                    log(f"  Skipping duplicate: {external_id}")
                    skipped += 1
                    continue

                # Extract data - be flexible with field names
                asset = item.get('symbol', '').upper()
                side = 'long' if item.get('side', '').lower() == 'buy' else 'short'
                qty = float(item.get('qty') or item.get('size') or item.get('closedSize') or 0)

                # Try multiple field names for prices
                entry_price = float(item.get('avgEntryPrice') or item.get('entryPrice') or item.get('avgPrice') or 0)
                exit_price = float(item.get('avgExitPrice') or item.get('exitPrice') or item.get('avgPrice') or 0)
                pnl = float(item.get('closedPnl') or item.get('pnl') or 0)

                log(f"\n  Processing: {asset} | side={side} | qty={qty} | entry={entry_price} | exit={exit_price} | pnl={pnl}")

                # Less strict validation - only require asset and pnl
                if not asset or pnl == 0:
                    log(f"  REJECTED: asset={asset!r} pnl={pnl}")
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

                log(f"  Attempting database insert with asset={asset}, pnl%={pnl_percentage:.2f}")

                # Get current timestamp
                created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Insert trade - include ALL required NOT NULL columns
                cursor.execute('''
                    INSERT INTO trades (
                        user_id, asset, side, entry_price, exit_price, quantity,
                        entry_time, exit_time, pnl, pnl_percentage, weekly_bias, daily_bias,
                        notes, status, external_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, asset, side, entry_price, exit_price, qty,
                    entry_time, exit_time, pnl, pnl_percentage, 'neutral', 'neutral',
                    '', 'closed', external_id, created_at
                ))

                inserted += 1
                log(f"  Successfully inserted trade!")
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
    """Save Bybit API credentials - preserves existing credentials"""
    try:
        user_id = get_current_user_id()
        data = request.json
        api_key = data.get('api_key')
        api_secret = data.get('api_secret')
        network = (data.get('network') or 'mainnet').strip().lower()
        remember_me = data.get('remember_me', True)  # Default to True

        conn = get_db_connection()
        cursor = conn.cursor()

        # Update existing credentials instead of deleting them
        cursor.execute('''
            INSERT OR REPLACE INTO api_credentials 
            (user_id, exchange, api_key, api_secret, network, remember_me) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, 'bybit', api_key, api_secret, network, 1 if remember_me else 0))
        
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Credentials saved and will be remembered'})
    except Exception as e:
        print(f"Error saving credentials: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/get_bybit_credentials', methods=['GET'])
def get_bybit_credentials():
    """Get saved Bybit credentials for current user"""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM api_credentials WHERE user_id = ? AND exchange = ? ORDER BY created_at DESC LIMIT 1', (user_id, 'bybit'))
    creds = cursor.fetchone()
    conn.close()

    if creds and creds['api_key']:
        # Convert Row to dict to use .get() method
        creds_dict = dict(creds)
        return jsonify({
            'connected': True,
            'api_key_last4': creds_dict['api_key'][:4],
            'network': creds_dict.get('network', 'mainnet'),
            'remember_me': bool(creds_dict.get('remember_me', 0))
        })
    return jsonify({'connected': False})


@app.route('/api/bybit/balance', methods=['GET'])
def get_bybit_balance():
    """Get Bybit account balance"""
    try:
        creds = _get_saved_bybit_credentials()
        if not creds or not creds.get('api_key'):
            return jsonify({
                'success': False,
                'balance': 0,
                'error': 'BYBIT_API_ERROR',
                'details': 'No credentials'
            }), 200

        network = (creds.get('network') or 'mainnet').strip().lower()
        
        # Debug logging to identify credential issues
        print(f"DEBUG: Using Bybit key: {creds['api_key'][:6]}... network: {network}")
        print(f"DEBUG: pybit module: {BybitHTTP.__module__}")
        
        client = _create_bybit_client(creds['api_key'], creds['api_secret'], network)

        # Get wallet balance for Unified Trading Account
        response = client.get_wallet_balance(accountType='UNIFIED')

        if response and response.get('retCode') == 0:
            result = response.get('result', {})
            account_list = result.get('list', [])

            # USDT Equity Only (matches trader expectations)
            total_balance = 0.0
            if account_list:
                for account in account_list:
                    coins = account.get('coin', [])
                    for coin in coins:
                        if coin.get('coin') == 'USDT':
                            usdt_equity = float(coin.get('equity', 0))
                            total_balance += usdt_equity
                            print(f"DEBUG: USDT Equity: {usdt_equity}")

            # Add warning for zero balance
            if total_balance == 0:
                print("WARNING: Balance computed as 0 — check permissions or account type")
                return jsonify({
                    'success': True,
                    'balance': total_balance,
                    'warning': 'Zero balance detected'
                })

            return jsonify({
                'success': True,
                'balance': total_balance
            })
        else:
            return jsonify({
                'success': False,
                'balance': 0,
                'message': response.get('retMsg', 'API error')
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'balance': 0,
            'error': 'BYBIT_API_ERROR',
            'details': str(e)
        }), 200


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
            resp = client.get_executions(category='linear', limit=10, accountType='UNIFIED')
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
            resp = client.get_order_history(category='linear', limit=10, accountType='UNIFIED')
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
    user_id = get_current_user_id()
    
    # Check if user is logged in
    if not user_id:
        return jsonify({
            'error': 'not_logged_in',
            'message': ' Please log in to view your calendar data'
        }), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            DATE(entry_time) as trade_date,
            SUM(pnl) as daily_pnl,
            COUNT(*) as trade_count,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades
        FROM trades
        WHERE user_id = ? AND status = 'closed' AND pnl IS NOT NULL AND is_deleted = 0
        GROUP BY DATE(entry_time)
        ORDER BY trade_date
    ''', (user_id,))

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
    user_id = get_current_user_id()
    date_str = request.args.get('date')
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM trades
        WHERE user_id = ? AND DATE(entry_time) = ? AND status = 'closed' AND is_deleted = 0
        ORDER BY entry_time DESC
    ''', (user_id, date_str))

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
    user_id = get_current_user_id()

    period = request.args.get('period', 'all')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status', 'closed')

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM trades WHERE user_id = ? AND status = ? AND is_deleted = 0"
    params = [user_id, status]

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

        if not trade:
            return ('', 404)

        # Convert to dict and add related details
        trade_dict = dict(trade)
        trade_dict.update(get_trade_details(trade_id))

        return jsonify(trade_dict)

    elif request.method == 'PUT':
        data = request.json
        print(f"DEBUG: PUT data received: {data}")  # Debug output

        # Update only core trade fields
        cursor.execute('''
            UPDATE trades SET
                asset = ?, side = ?, entry_price = ?, exit_price = ?, quantity = ?,
                entry_time = ?, exit_time = ?, pnl = ?,
                weekly_bias = ?, daily_bias = ?,
                notes = ?, status = ?,
                stop_loss = ?, take_profit = ?, risk_reward_ratio = ?, position_size_pct = ?
            WHERE id = ?
        ''', (
            data['asset'], data['side'], data['entry_price'], data.get('exit_price'),
            data['quantity'], data['entry_time'], data.get('exit_time'), data.get('pnl'),
            data.get('weekly_bias', 'neutral'),
            data.get('daily_bias', 'neutral'), data.get('notes', ''),
            data.get('status', 'closed'),
            data.get('stop_loss'), data.get('take_profit'),
            data.get('risk_reward_ratio'), data.get('position_size_pct'),
            trade_id
        ))

        conn.commit()
        conn.close()
        return jsonify({'success': True})

    elif request.method == 'DELETE':
        # Soft delete - set is_deleted = 1 instead of actual deletion
        cursor.execute('UPDATE trades SET is_deleted = 1 WHERE id = ?', (trade_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})


@app.route('/api/trades/<int:trade_id>/entry_type', methods=['POST'])
def set_entry_type(trade_id):
    """Set entry type for a trade"""
    data = request.json
    entry_type = data.get('entry_type')

    if not entry_type:
        return jsonify({'success': False, 'error': 'entry_type required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('UPDATE trades SET entry_type = ? WHERE id = ?', (entry_type, trade_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trades/<int:trade_id>/details', methods=['GET', 'POST'])
def manage_trade_details(trade_id):
    """Get or update trade details (key levels, confirmations, entries, models, screenshots)"""
    if request.method == 'GET':
        details = get_trade_details(trade_id)
        return jsonify(details)

    elif request.method == 'POST':
        data = request.json

        # Validate that trade is closed before allowing stats to be saved
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM trades WHERE id = ?', (trade_id,))
        trade = cursor.fetchone()
        conn.close()

        if not trade or trade['status'] != 'closed':
            return jsonify({'success': False, 'error': 'Stats can only be saved for closed trades'}), 400

        try:
            save_trade_details(
                trade_id,
                key_levels=data.get('key_levels', []),
                confirmations=data.get('confirmations', []),
                entries=data.get('entries', []),
                models=data.get('models', []),
                screenshots=data.get('screenshots', [])
            )
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trades', methods=['POST'])
def create_trade():
    """Create a new trade"""
    data = request.json
    user_id = get_current_user_id()

    # Calculate P&L if trade is closed
    pnl = None
    pnl_percentage = None
    status = data.get('status', 'closed')

    if status == 'closed' and data.get('exit_price'):
        if data['side'] == 'long':
            pnl = (float(data['exit_price']) - float(data['entry_price'])) * float(data['quantity'])
        else:
            pnl = (float(data['entry_price']) - float(data['exit_price'])) * float(data['quantity'])

        # Calculate PnL percentage
        entry_value = float(data['entry_price']) * float(data['quantity'])
        if entry_value > 0:
            pnl_percentage = (pnl / entry_value) * 100

    # Calculate R:R ratio
    rr_ratio = calculate_risk_reward_ratio(
        data.get('entry_price'),
        data.get('stop_loss'),
        data.get('take_profit'),
        data['side']
    )

    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert basic trade info (no deprecated fields)
    cursor.execute('''
        INSERT INTO trades (user_id, asset, side, entry_price, exit_price, stop_loss, take_profit,
                          quantity, entry_time, exit_time, pnl, pnl_percentage, risk_reward_ratio,
                          position_size_pct, weekly_bias, daily_bias, notes, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, data['asset'], data['side'], data['entry_price'], data.get('exit_price'),
        data.get('stop_loss'), data.get('take_profit'),
        data['quantity'], data['entry_time'], data.get('exit_time'), pnl, pnl_percentage,
        rr_ratio, data.get('position_size_pct'),
        data.get('weekly_bias', 'neutral'), data.get('daily_bias', 'neutral'),
        data.get('notes', ''), status
    ))

    trade_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Save related details (arrays)
    save_trade_details(
        trade_id,
        key_levels=data.get('key_levels', []),
        confirmations=data.get('confirmations', []),
        entries=data.get('entries', []),
        models=data.get('models', []),
        screenshots=data.get('screenshots', [])
    )

    return jsonify({'success': True, 'id': trade_id})


@app.route('/api/risk_metrics', methods=['GET'])
def get_risk_metrics():
    """Calculate advanced risk metrics"""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT pnl, entry_time, risk_reward_ratio
        FROM trades
        WHERE user_id = ? AND status = 'closed' AND pnl IS NOT NULL AND is_deleted = 0
        ORDER BY entry_time ASC
    ''', (user_id,))

    trades = cursor.fetchall()
    conn.close()

    if not trades:
        return jsonify({
            'max_drawdown': 0,
            'max_drawdown_pct': 0,
            'expectancy': 0,
            'avg_rr_ratio': 0,
            'consecutive_wins': 0,
            'consecutive_losses': 0,
            'largest_win': 0,
            'largest_loss': 0
        })

    # Calculate cumulative P&L and max drawdown
    cumulative_pnl = 0
    peak = 0
    max_drawdown = 0
    max_drawdown_pct = 0

    for trade in trades:
        cumulative_pnl += trade['pnl']
        if cumulative_pnl > peak:
            peak = cumulative_pnl
        drawdown = peak - cumulative_pnl
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            max_drawdown_pct = (drawdown / peak * 100) if peak > 0 else 0

    # Calculate expectancy
    wins = [t['pnl'] for t in trades if t['pnl'] > 0]
    losses = [t['pnl'] for t in trades if t['pnl'] < 0]

    total_trades = len(trades)
    win_rate = len(wins) / total_trades if total_trades > 0 else 0
    avg_win = sum(wins) / len(wins) if wins else 0
    avg_loss = abs(sum(losses) / len(losses)) if losses else 0

    expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

    # Calculate avg R:R ratio
    rr_ratios = [t['risk_reward_ratio'] for t in trades if t['risk_reward_ratio']]
    avg_rr_ratio = sum(rr_ratios) / len(rr_ratios) if rr_ratios else 0

    # Calculate consecutive wins/losses
    current_streak = 0
    max_win_streak = 0
    max_loss_streak = 0

    for trade in trades:
        if trade['pnl'] > 0:
            if current_streak >= 0:
                current_streak += 1
            else:
                current_streak = 1
            max_win_streak = max(max_win_streak, current_streak)
        else:
            if current_streak <= 0:
                current_streak -= 1
            else:
                current_streak = -1
            max_loss_streak = max(max_loss_streak, abs(current_streak))

    # Largest win/loss
    largest_win = max(wins) if wins else 0
    largest_loss = min(losses) if losses else 0

    return jsonify({
        'max_drawdown': round(max_drawdown, 2),
        'max_drawdown_pct': round(max_drawdown_pct, 2),
        'expectancy': round(expectancy, 2),
        'avg_rr_ratio': round(avg_rr_ratio, 2),
        'consecutive_wins': max_win_streak,
        'consecutive_losses': max_loss_streak,
        'largest_win': round(largest_win, 2),
        'largest_loss': round(largest_loss, 2)
    })


@app.route('/api/analytics/by_model', methods=['GET'])
def get_analytics_by_model():
    """Get performance analytics aggregated by trading model"""
    user_id = get_current_user_id()

    # Get filter parameters
    asset = request.args.get('asset', 'all')
    weekly_bias = request.args.get('weekly_bias', 'all')
    daily_bias = request.args.get('daily_bias', 'all')
    side = request.args.get('side', 'all')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Build dynamic WHERE clause
    where_conditions = ['t.user_id = ?', 't.status = ?', 't.pnl IS NOT NULL', 't.is_deleted = 0']
    params = [user_id, 'closed']

    if asset != 'all':
        where_conditions.append('t.asset = ?')
        params.append(asset)
    if weekly_bias != 'all':
        where_conditions.append('t.weekly_bias = ?')
        params.append(weekly_bias)
    if daily_bias != 'all':
        where_conditions.append('t.daily_bias = ?')
        params.append(daily_bias)
    if side != 'all':
        where_conditions.append('t.side = ?')
        params.append(side)

    where_clause = ' AND '.join(where_conditions)

    cursor.execute(f'''
        SELECT
            tm.model,
            COUNT(DISTINCT t.id) as trade_count,
            SUM(t.pnl) as total_pnl,
            AVG(t.pnl) as avg_pnl,
            COUNT(DISTINCT CASE WHEN t.pnl > 0 THEN t.id END) as wins,
            COUNT(DISTINCT CASE WHEN t.pnl < 0 THEN t.id END) as losses
        FROM trades t
        JOIN trade_models tm ON t.id = tm.trade_id
        WHERE {where_clause}
        GROUP BY tm.model
        ORDER BY total_pnl DESC
    ''', params)

    models = cursor.fetchall()
    conn.close()

    results = []
    for row in models:
        trade_count = row['trade_count']
        win_rate = (row['wins'] / trade_count * 100) if trade_count > 0 else 0
        results.append({
            'model': row['model'],
            'trade_count': trade_count,
            'total_pnl': round(row['total_pnl'], 2),
            'avg_pnl': round(row['avg_pnl'], 2),
            'wins': row['wins'],
            'losses': row['losses'],
            'win_rate': round(win_rate, 1)
        })

    return jsonify({'models': results})


@app.route('/api/analytics/by_confirmation', methods=['GET'])
def get_analytics_by_confirmation():
    """Get performance analytics aggregated by confirmation type"""
    user_id = get_current_user_id()

    # Get filter parameters
    asset = request.args.get('asset', 'all')
    weekly_bias = request.args.get('weekly_bias', 'all')
    daily_bias = request.args.get('daily_bias', 'all')
    side = request.args.get('side', 'all')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Build dynamic WHERE clause
    where_conditions = ['t.user_id = ?', 't.status = ?', 't.pnl IS NOT NULL', 't.is_deleted = 0']
    params = [user_id, 'closed']

    if asset != 'all':
        where_conditions.append('t.asset = ?')
        params.append(asset)
    if weekly_bias != 'all':
        where_conditions.append('t.weekly_bias = ?')
        params.append(weekly_bias)
    if daily_bias != 'all':
        where_conditions.append('t.daily_bias = ?')
        params.append(daily_bias)
    if side != 'all':
        where_conditions.append('t.side = ?')
        params.append(side)

    where_clause = ' AND '.join(where_conditions)

    cursor.execute(f'''
        SELECT
            tc.confirmation,
            COUNT(DISTINCT t.id) as trade_count,
            SUM(t.pnl) as total_pnl,
            AVG(t.pnl) as avg_pnl,
            COUNT(DISTINCT CASE WHEN t.pnl > 0 THEN t.id END) as wins,
            COUNT(DISTINCT CASE WHEN t.pnl < 0 THEN t.id END) as losses
        FROM trades t
        JOIN trade_confirmations tc ON t.id = tc.trade_id
        WHERE {where_clause}
        GROUP BY tc.confirmation
        ORDER BY total_pnl DESC
    ''', params)

    confirmations = cursor.fetchall()
    conn.close()

    results = []
    for row in confirmations:
        trade_count = row['trade_count']
        win_rate = (row['wins'] / trade_count * 100) if trade_count > 0 else 0
        results.append({
            'confirmation': row['confirmation'],
            'trade_count': trade_count,
            'total_pnl': round(row['total_pnl'], 2),
            'avg_pnl': round(row['avg_pnl'], 2),
            'wins': row['wins'],
            'losses': row['losses'],
            'win_rate': round(win_rate, 1)
        })

    return jsonify({'confirmations': results})


@app.route('/api/analytics/by_entry', methods=['GET'])
def get_analytics_by_entry():
    """Get performance analytics aggregated by entry type"""
    user_id = get_current_user_id()

    # Get filter parameters
    asset = request.args.get('asset', 'all')
    weekly_bias = request.args.get('weekly_bias', 'all')
    daily_bias = request.args.get('daily_bias', 'all')
    side = request.args.get('side', 'all')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Build dynamic WHERE clause
    where_conditions = ['t.user_id = ?', 't.status = ?', 't.pnl IS NOT NULL', 't.is_deleted = 0']
    params = [user_id, 'closed']

    if asset != 'all':
        where_conditions.append('t.asset = ?')
        params.append(asset)
    if weekly_bias != 'all':
        where_conditions.append('t.weekly_bias = ?')
        params.append(weekly_bias)
    if daily_bias != 'all':
        where_conditions.append('t.daily_bias = ?')
        params.append(daily_bias)
    if side != 'all':
        where_conditions.append('t.side = ?')
        params.append(side)

    where_clause = ' AND '.join(where_conditions)

    cursor.execute(f'''
        SELECT
            te.entry,
            COUNT(DISTINCT t.id) as trade_count,
            SUM(t.pnl) as total_pnl,
            AVG(t.pnl) as avg_pnl,
            COUNT(DISTINCT CASE WHEN t.pnl > 0 THEN t.id END) as wins,
            COUNT(DISTINCT CASE WHEN t.pnl < 0 THEN t.id END) as losses
        FROM trades t
        JOIN trade_entries te ON t.id = te.trade_id
        WHERE {where_clause}
        GROUP BY te.entry
        ORDER BY total_pnl DESC
    ''', params)

    entries = cursor.fetchall()
    conn.close()

    results = []
    for row in entries:
        trade_count = row['trade_count']
        win_rate = (row['wins'] / trade_count * 100) if trade_count > 0 else 0
        results.append({
            'entry': row['entry'],
            'trade_count': trade_count,
            'total_pnl': round(row['total_pnl'], 2),
            'avg_pnl': round(row['avg_pnl'], 2),
            'wins': row['wins'],
            'losses': row['losses'],
            'win_rate': round(win_rate, 1)
        })

    return jsonify({'entries': results})


@app.route('/api/analytics/by_key_level', methods=['GET'])
def get_analytics_by_key_level():
    """Get performance analytics aggregated by key level"""
    user_id = get_current_user_id()

    # Get filter parameters
    asset = request.args.get('asset', 'all')
    weekly_bias = request.args.get('weekly_bias', 'all')
    daily_bias = request.args.get('daily_bias', 'all')
    side = request.args.get('side', 'all')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Build dynamic WHERE clause
    where_conditions = ['t.user_id = ?', 't.status = ?', 't.pnl IS NOT NULL', 't.is_deleted = 0']
    params = [user_id, 'closed']

    if asset != 'all':
        where_conditions.append('t.asset = ?')
        params.append(asset)
    if weekly_bias != 'all':
        where_conditions.append('t.weekly_bias = ?')
        params.append(weekly_bias)
    if daily_bias != 'all':
        where_conditions.append('t.daily_bias = ?')
        params.append(daily_bias)
    if side != 'all':
        where_conditions.append('t.side = ?')
        params.append(side)

    where_clause = ' AND '.join(where_conditions)

    cursor.execute(f'''
        SELECT
            tkl.level,
            COUNT(DISTINCT t.id) as trade_count,
            SUM(t.pnl) as total_pnl,
            AVG(t.pnl) as avg_pnl,
            COUNT(DISTINCT CASE WHEN t.pnl > 0 THEN t.id END) as wins,
            COUNT(DISTINCT CASE WHEN t.pnl < 0 THEN t.id END) as losses
        FROM trades t
        JOIN trade_key_levels tkl ON t.id = tkl.trade_id
        WHERE {where_clause}
        GROUP BY tkl.level
        ORDER BY total_pnl DESC
    ''', params)

    key_levels = cursor.fetchall()
    conn.close()

    results = []
    for row in key_levels:
        trade_count = row['trade_count']
        win_rate = (row['wins'] / trade_count * 100) if trade_count > 0 else 0
        results.append({
            'level': row['level'],
            'trade_count': trade_count,
            'total_pnl': round(row['total_pnl'], 2),
            'avg_pnl': round(row['avg_pnl'], 2),
            'wins': row['wins'],
            'losses': row['losses'],
            'win_rate': round(win_rate, 1)
        })

    return jsonify({'key_levels': results})


@app.route('/api/time_analytics', methods=['GET'])
def get_time_analytics():
    """Get performance by hour and day of week"""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT entry_time, pnl
        FROM trades
        WHERE user_id = ? AND status = 'closed' AND pnl IS NOT NULL AND is_deleted = 0
    ''', (user_id,))

    trades = cursor.fetchall()
    conn.close()

    # Initialize hour and day stats
    hour_stats = {str(i): {'total_pnl': 0, 'count': 0, 'wins': 0} for i in range(24)}
    day_stats = {str(i): {'total_pnl': 0, 'count': 0, 'wins': 0} for i in range(7)}  # 0=Monday, 6=Sunday

    for trade in trades:
        try:
            dt = datetime.fromisoformat(trade['entry_time'].replace('Z', '+00:00'))
            hour = str(dt.hour)
            day = str(dt.weekday())

            pnl = trade['pnl']

            # Hour stats
            hour_stats[hour]['total_pnl'] += pnl
            hour_stats[hour]['count'] += 1
            if pnl > 0:
                hour_stats[hour]['wins'] += 1

            # Day stats
            day_stats[day]['total_pnl'] += pnl
            day_stats[day]['count'] += 1
            if pnl > 0:
                day_stats[day]['wins'] += 1
        except:
            continue

    # Calculate win rates and averages
    for hour in hour_stats:
        if hour_stats[hour]['count'] > 0:
            hour_stats[hour]['avg_pnl'] = round(hour_stats[hour]['total_pnl'] / hour_stats[hour]['count'], 2)
            hour_stats[hour]['win_rate'] = round(hour_stats[hour]['wins'] / hour_stats[hour]['count'] * 100, 1)
        else:
            hour_stats[hour]['avg_pnl'] = 0
            hour_stats[hour]['win_rate'] = 0

    for day in day_stats:
        if day_stats[day]['count'] > 0:
            day_stats[day]['avg_pnl'] = round(day_stats[day]['total_pnl'] / day_stats[day]['count'], 2)
            day_stats[day]['win_rate'] = round(day_stats[day]['wins'] / day_stats[day]['count'] * 100, 1)
        else:
            day_stats[day]['avg_pnl'] = 0
            day_stats[day]['win_rate'] = 0

    return jsonify({
        'by_hour': hour_stats,
        'by_day': day_stats
    })


@app.route('/api/upload_screenshot', methods=['POST'])
def upload_screenshot():
    """Upload a screenshot for a trade"""
    if 'screenshot' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['screenshot']

    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if file and allowed_file(file.filename):
        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Save file
        file.save(filepath)

        # Return the URL path
        screenshot_url = f"/screenshots/{filename}"
        return jsonify({'success': True, 'url': screenshot_url})

    return jsonify({'success': False, 'error': 'Invalid file type'}), 400


@app.route('/api/trades/<int:trade_id>/screenshots/url', methods=['POST'])
def add_screenshot_url(trade_id):
    """Add a screenshot URL for a trade"""
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'success': False, 'error': 'URL required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO trade_screenshots (trade_id, screenshot_url)
        VALUES (?, ?)
    ''', (trade_id, url))

    conn.commit()
    conn.close()

    return jsonify({'success': True})


@app.route('/screenshots/<filename>')
def serve_screenshot(filename):
    """Serve uploaded screenshots"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ================== RUN APPLICATION ==================
if __name__ == '__main__':
    print("=" * 60)
    print("Trading Journal Application Starting...")
    print("=" * 60)
    print(f"Server: http://localhost:5000")
    print("=" * 60)

    app.run(debug=False, port=5000, host='0.0.0.0')
