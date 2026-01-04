# database/trade_db.py
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
import hashlib
import schedule
import threading
import time
from typing import List, Dict, Optional


class TradeDatabase:
    """PROFESSIONAL Trade Database with Auto-import"""

    def __init__(self):
        # Create data folder if it doesn't exist
        os.makedirs('data', exist_ok=True)
        self.db_path = 'data/trading_journal.db'
        self._create_tables()
        self._create_key_levels_table()  # NEW: Enhanced key levels table
        self._create_trade_levels_table()  # NEW: Trade-level associations

    def _create_tables(self):
        """Create enhanced trades table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # ENHANCED trades table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT UNIQUE,
                    symbol TEXT,
                    side TEXT,
                    qty REAL,
                    entry_price REAL,
                    exit_price REAL,
                    pnl REAL,
                    pnl_percent REAL,
                    fees REAL,
                    entry_time TIMESTAMP,
                    exit_time TIMESTAMP,
                    duration_minutes INTEGER,
                    strategy TEXT,
                    timeframe TEXT,
                    tags TEXT,
                    notes TEXT,
                    imported_from TEXT,
                    import_hash TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            print("✅ Professional database ready!")

    def _create_key_levels_table(self):
        """NEW: Create smart key levels table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS key_levels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level_name TEXT,
                    normalized_name TEXT UNIQUE,
                    value REAL,
                    category TEXT,
                    strength INTEGER DEFAULT 3,
                    instrument TEXT DEFAULT 'ALL',
                    timeframe TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create index for faster lookups
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_normalized_name ON key_levels(normalized_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_instrument ON key_levels(instrument)')
            conn.commit()

    def _create_trade_levels_table(self):
        """NEW: Create trade-level associations table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trade_levels (
                    trade_id INTEGER,
                    level_id INTEGER,
                    relevance_score INTEGER DEFAULT 3,
                    FOREIGN KEY (trade_id) REFERENCES trades (id),
                    FOREIGN KEY (level_id) REFERENCES key_levels (id),
                    PRIMARY KEY (trade_id, level_id)
                )
            ''')
            conn.commit()

    # ========== ENHANCED TRADE METHODS ==========

    def save_trade(self, trade):
        """Enhanced save trade with more fields"""
        try:
            # Calculate additional metrics
            entry_price = trade.get('entry_price', trade.get('price', 0))
            exit_price = trade.get('exit_price', entry_price)
            qty = trade.get('qty', 0)
            pnl = trade.get('pnl', 0)

            # Calculate PnL percentage
            pnl_percent = 0
            if entry_price > 0 and qty > 0:
                pnl_percent = (pnl / (entry_price * qty)) * 100

            # Calculate duration
            duration = 0
            entry_time = trade.get('entry_time', trade.get('timestamp'))
            exit_time = trade.get('exit_time', entry_time)

            if entry_time and exit_time:
                if isinstance(entry_time, str):
                    entry_time = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
                if isinstance(exit_time, str):
                    exit_time = datetime.fromisoformat(exit_time.replace('Z', '+00:00'))
                duration = int((exit_time - entry_time).total_seconds() / 60)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT OR IGNORE INTO trades 
                    (trade_id, symbol, side, qty, entry_price, exit_price, 
                     pnl, pnl_percent, fees, entry_time, exit_time, duration_minutes,
                     strategy, timeframe, tags, notes, imported_from, import_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade.get('id'),
                    trade.get('symbol'),
                    trade.get('side'),
                    qty,
                    entry_price,
                    exit_price,
                    pnl,
                    pnl_percent,
                    trade.get('fees', 0),
                    entry_time,
                    exit_time,
                    duration,
                    trade.get('strategy', ''),
                    trade.get('timeframe', ''),
                    trade.get('tags', ''),
                    trade.get('notes', ''),
                    trade.get('imported_from', 'manual'),
                    trade.get('import_hash', '')
                ))

                trade_id = cursor.lastrowid
                conn.commit()

                # NEW: Auto-match with key levels
                if entry_price > 0:
                    self._auto_match_key_levels(trade_id, entry_price, exit_price, trade.get('symbol'))

                print(f"✅ Saved trade: {trade.get('symbol')} (PnL: ${pnl:.2f})")
                return True

        except Exception as e:
            print(f"❌ Error saving trade: {e}")
            return False

    # ========== AUTO-IMPORT SYSTEM ==========

    def import_from_bybit(self, hours_back=24, api_key=None, api_secret=None):
        """NEW: Auto-import trades from Bybit API"""
        try:
            # Import your existing Bybit code
            from day5_final_working import BybitTradeImporter

            # Initialize importer
            importer = BybitTradeImporter(api_key, api_secret)

            # Calculate time range
            end_time = int(datetime.now().timestamp() * 1000)
            start_time = int((datetime.now() - timedelta(hours=hours_back)).timestamp() * 1000)

            # Fetch trades
            print(f"📥 Fetching trades from Bybit (last {hours_back} hours)...")
            trades = importer.get_trade_history(start_time, end_time)

            imported_count = 0
            for trade in trades:
                # Calculate import hash to prevent duplicates
                import_hash = self._calculate_import_hash(trade)

                # Check if already imported
                if self._is_trade_imported(import_hash):
                    continue

                # Prepare trade data
                trade_data = {
                    'id': trade.get('order_id'),
                    'symbol': trade.get('symbol'),
                    'side': trade.get('side'),
                    'qty': float(trade.get('exec_qty', 0)),
                    'entry_price': float(trade.get('avg_entry_price', 0)),
                    'exit_price': float(trade.get('avg_exit_price', 0)),
                    'pnl': float(trade.get('closed_pnl', 0)),
                    'fees': float(trade.get('exec_fee', 0)),
                    'entry_time': datetime.fromtimestamp(int(trade.get('created_at', 0)) / 1000),
                    'exit_time': datetime.fromtimestamp(int(trade.get('updated_at', 0)) / 1000),
                    'strategy': trade.get('order_type', 'Unknown'),
                    'imported_from': 'Bybit',
                    'import_hash': import_hash
                }

                # Save trade
                if self.save_trade(trade_data):
                    imported_count += 1

            print(f"✅ Imported {imported_count} new trades from Bybit")
            return imported_count

        except ImportError:
            print("❌ day5_final_working.py not found")
            return 0
        except Exception as e:
            print(f"❌ Import error: {e}")
            return 0

    def _calculate_import_hash(self, trade_data):
        """Create unique hash for duplicate detection"""
        hash_string = f"{trade_data.get('order_id')}_{trade_data.get('symbol')}_{trade_data.get('created_at')}"
        return hashlib.md5(hash_string.encode()).hexdigest()

    def _is_trade_imported(self, import_hash):
        """Check if trade already imported"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM trades WHERE import_hash = ?', (import_hash,))
            return cursor.fetchone() is not None

    def start_auto_import_scheduler(self, interval_minutes=15, hours_back=2):
        """NEW: Start scheduled auto-imports"""

        def import_job():
            print(f"\n🔄 Scheduled import at {datetime.now().strftime('%H:%M:%S')}")
            self.import_from_bybit(hours_back=hours_back)

        # Schedule the job
        schedule.every(interval_minutes).minutes.do(import_job)

        # Run in background thread
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)

        thread = threading.Thread(target=run_scheduler, daemon=True)
        thread.start()
        print(f"✅ Auto-import scheduler started (every {interval_minutes} minutes)")
        return thread

    # ========== SMART KEY LEVELS METHODS ==========

    def add_key_level(self, name, value, category='Custom', instrument='ALL', strength=3, notes=''):
        """NEW: Add smart key level (case-insensitive)"""
        normalized_name = name.strip().lower()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT OR IGNORE INTO key_levels 
                    (level_name, normalized_name, value, category, instrument, strength, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (name, normalized_name, value, category, instrument, strength, notes))

                level_id = cursor.lastrowid
                conn.commit()

                # Auto-match with existing trades
                self._retroactive_match_level(level_id, value, instrument)

                print(f"✅ Added key level: {name} at {value} ({category})")
                return level_id

        except sqlite3.IntegrityError:
            print(f"⚠️ Key level '{name}' already exists (case-insensitive)")
            return None

    def _auto_match_key_levels(self, trade_id, entry_price, exit_price, symbol):
        """NEW: Auto-match trade with nearby key levels"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get relevant key levels
            cursor.execute('''
                SELECT id, value FROM key_levels 
                WHERE instrument IN (?, 'ALL')
            ''', (symbol,))

            levels = cursor.fetchall()

            matched = 0
            for level_id, level_value in levels:
                # Check if trade touched this level (within 0.5%)
                threshold = level_value * 0.005

                if (abs(entry_price - level_value) <= threshold or
                        abs(exit_price - level_value) <= threshold):
                    # Calculate relevance score (1-5)
                    entry_dist = abs(entry_price - level_value)
                    exit_dist = abs(exit_price - level_value)
                    min_dist = min(entry_dist, exit_dist)
                    relevance = max(1, min(5, int(5 - (min_dist / threshold) * 4)))

                    cursor.execute('''
                        INSERT OR IGNORE INTO trade_levels 
                        (trade_id, level_id, relevance_score)
                        VALUES (?, ?, ?)
                    ''', (trade_id, level_id, relevance))

                    matched += 1

            conn.commit()
            if matched > 0:
                print(f"   ↳ Matched with {matched} key levels")

    def _retroactive_match_level(self, level_id, value, instrument):
        """NEW: Match new level with existing trades"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Find existing trades for this instrument
            cursor.execute('''
                SELECT id, entry_price, exit_price FROM trades 
                WHERE symbol = ? OR ? = 'ALL'
            ''', (instrument, instrument))

            trades = cursor.fetchall()

            matched = 0
            threshold = value * 0.005

            for trade_id, entry_price, exit_price in trades:
                if (abs(entry_price - value) <= threshold or
                        abs(exit_price - value) <= threshold):
                    entry_dist = abs(entry_price - value)
                    exit_dist = abs(exit_price - value)
                    min_dist = min(entry_dist, exit_dist)
                    relevance = max(1, min(5, int(5 - (min_dist / threshold) * 4)))

                    cursor.execute('''
                        INSERT OR IGNORE INTO trade_levels 
                        (trade_id, level_id, relevance_score)
                        VALUES (?, ?, ?)
                    ''', (trade_id, level_id, relevance))

                    matched += 1

            conn.commit()
            if matched:
                print(f"   ↳ Retroactively matched with {matched} trades")

    # ========== ENHANCED GET METHODS ==========

    def get_trades(self, symbol=None, limit=None):
        """Enhanced: Get trades with filtering"""
        query = 'SELECT * FROM trades'
        params = []

        if symbol:
            query += ' WHERE symbol = ?'
            params.append(symbol)

        query += ' ORDER BY entry_time DESC'

        if limit:
            query += ' LIMIT ?'
            params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn, params=params)
            return df

    def get_trades_with_levels(self):
        """NEW: Get trades with their associated key levels"""
        query = '''
            SELECT t.*, 
                   GROUP_CONCAT(kl.level_name) as key_levels,
                   GROUP_CONCAT(tl.relevance_score) as relevance_scores
            FROM trades t
            LEFT JOIN trade_levels tl ON t.id = tl.trade_id
            LEFT JOIN key_levels kl ON tl.level_id = kl.id
            GROUP BY t.id
            ORDER BY t.entry_time DESC
        '''

        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn)
            return df

    def get_key_levels(self, instrument=None, category=None):
        """NEW: Get key levels with filtering"""
        query = 'SELECT * FROM key_levels WHERE 1=1'
        params = []

        if instrument:
            query += ' AND instrument IN (?, "ALL")'
            params.append(instrument)

        if category:
            query += ' AND category = ?'
            params.append(category)

        query += ' ORDER BY value DESC'

        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn, params=params)
            return df

    # ========== ENHANCED STATISTICS ==========

    def get_stats(self, symbol=None):
        """Enhanced statistics with more metrics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Build WHERE clause
            where_clause = 'WHERE 1=1'
            params = []
            if symbol:
                where_clause += ' AND symbol = ?'
                params.append(symbol)

            # Total trades
            cursor.execute(f'SELECT COUNT(*) FROM trades {where_clause}', params)
            total = cursor.fetchone()[0]

            if total == 0:
                return {'total_trades': 0, 'total_pnl': 0, 'win_rate': 0}

            # Enhanced stats
            cursor.execute(f'''
                SELECT 
                    COUNT(*) as total,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl,
                    AVG(pnl_percent) as avg_pnl_percent,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losses,
                    MAX(pnl) as best_trade,
                    MIN(pnl) as worst_trade,
                    AVG(duration_minutes) as avg_duration
                FROM trades {where_clause}
            ''', params)

            row = cursor.fetchone()

            win_rate = (row[4] / total) * 100 if total > 0 else 0

            return {
                'total_trades': total,
                'total_pnl': round(row[1] or 0, 2),
                'avg_pnl': round(row[2] or 0, 2),
                'avg_pnl_percent': round(row[3] or 0, 2),
                'win_rate': round(win_rate, 2),
                'wins': row[4],
                'losses': row[5],
                'best_trade': round(row[6] or 0, 2),
                'worst_trade': round(row[7] or 0, 2),
                'avg_duration': round(row[8] or 0, 2)
            }

    def get_level_statistics(self, level_name=None, instrument=None):
        """NEW: Statistics per key level"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            query = '''
                SELECT 
                    kl.level_name,
                    kl.category,
                    COUNT(DISTINCT t.id) as trade_count,
                    COUNT(DISTINCT t.symbol) as instrument_count,
                    SUM(CASE WHEN t.pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    AVG(t.pnl) as avg_pnl,
                    SUM(t.pnl) as total_pnl
                FROM key_levels kl
                JOIN trade_levels tl ON kl.id = tl.level_id
                JOIN trades t ON tl.trade_id = t.id
                WHERE 1=1
            '''

            params = []

            if level_name:
                query += ' AND kl.normalized_name = ?'
                params.append(level_name.lower())

            if instrument:
                query += ' AND t.symbol = ?'
                params.append(instrument)

            query += ' GROUP BY kl.id ORDER BY trade_count DESC'

            cursor.execute(query, params)
            results = cursor.fetchall()

            stats = []
            for row in results:
                level_name, category, trade_count, instr_count, wins, avg_pnl, total_pnl = row
                win_rate = (wins / trade_count * 100) if trade_count > 0 else 0

                stats.append({
                    'level': level_name,
                    'category': category,
                    'trade_count': trade_count,
                    'instruments': instr_count,
                    'win_rate': round(win_rate, 2),
                    'avg_pnl': round(avg_pnl or 0, 2),
                    'total_pnl': round(total_pnl or 0, 2)
                })

            return stats

    # ========== EXPORT METHODS ==========

    def export_trades_csv(self, filename='trades_export.csv'):
        """NEW: Export trades to CSV"""
        df = self.get_trades()
        df.to_csv(filename, index=False)
        print(f"✅ Exported {len(df)} trades to {filename}")
        return filename

    def export_key_levels_csv(self, filename='key_levels_export.csv'):
        """NEW: Export key levels to CSV"""
        df = self.get_key_levels()
        df.to_csv(filename, index=False)
        print(f"✅ Exported {len(df)} key levels to {filename}")
        return filename

    # ========== MAINTENANCE ==========

    def cleanup_duplicates(self):
        """NEW: Remove duplicate trades"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Find duplicates by import_hash
            cursor.execute('''
                DELETE FROM trades 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM trades 
                    WHERE import_hash IS NOT NULL AND import_hash != ''
                    GROUP BY import_hash
                ) AND import_hash IS NOT NULL AND import_hash != ''
            ''')

            deleted = cursor.rowcount
            conn.commit()

            if deleted > 0:
                print(f"✅ Removed {deleted} duplicate trades")

            return deleted

    def backup_database(self, backup_name=None):
        """NEW: Create database backup"""
        if backup_name is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f'data/trading_journal_backup_{timestamp}.db'

        import shutil
        shutil.copy2(self.db_path, backup_name)
        print(f"✅ Database backed up to {backup_name}")
        return backup_name


# ========== QUICK TEST ==========
if __name__ == "__main__":
    print("🧪 Testing enhanced TradeDatabase...")

    db = TradeDatabase()

    # Test basic functionality
    trades = db.get_trades()
    stats = db.get_stats()

    print(f"📊 Current stats: {stats}")
    print(f"📈 Total trades: {len(trades)}")

    # Test key levels
    print("\n🔧 Adding sample key levels...")
    db.add_key_level(".618", 45000, "Fibonacci", "BTCUSDT")
    db.add_key_level(".382", 47000, "Fibonacci", "BTCUSDT")
    db.add_key_level("Daily Pivot", 46000, "Pivot", "BTCUSDT")

    # Show key levels
    levels = db.get_key_levels()
    print(f"🎯 Key levels: {len(levels)} levels defined")

    print("\n✅ Enhanced TradeDatabase ready for Day 11!")