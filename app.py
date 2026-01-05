from flask import Flask, render_template, jsonify, request
import sqlite3
import json
from datetime import datetime, timedelta
import random
import os
import base64

app = Flask(__name__)


# ==================== DATABASE ====================
def get_db():
    conn = sqlite3.connect('trading_journal.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            asset TEXT,
            side TEXT,
            entry_price REAL,
            exit_price REAL,
            quantity REAL,
            entry_time TEXT,
            exit_time TEXT,
            pnl REAL,
            pnl_percentage REAL,
            status TEXT DEFAULT 'closed',
            key_level TEXT,
            key_level_type TEXT,
            confirmation TEXT,
            model TEXT,
            notes TEXT,
            screenshot TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


# ==================== SAMPLE DATA ====================
def add_sample_data():
    conn = get_db()
    cursor = conn.execute('SELECT COUNT(*) FROM trades')
    if cursor.fetchone()[0] > 10:
        conn.close()
        return

    print("➕ Adding 30 sample trades for December 2025...")

    for i in range(30):
        day = (i % 31) + 1
        try:
            exit_date = datetime(2025, 12, day, random.randint(9, 17), random.randint(0, 59))
            entry_date = exit_date - timedelta(hours=random.randint(1, 6))
        except:
            exit_date = datetime(2025, 12, 28, 14, 30)
            entry_date = exit_date - timedelta(hours=2)

        asset = ['BTC', 'ETH', 'SOL'][i % 3]
        symbol = f'{asset}USDT'
        side = 'buy' if i % 2 == 0 else 'sell'

        if asset == 'BTC':
            entry_price = random.uniform(58000, 68000)
            key_levels = [('60k Resistance', 'resistance'), ('58k Support', 'support'),
                          ('65k Resistance', 'resistance'), ('55k Support', 'support')]
        elif asset == 'ETH':
            entry_price = random.uniform(3500, 4200)
            key_levels = [('4k Resistance', 'resistance'), ('3.8k Support', 'support'),
                          ('4.2k Resistance', 'resistance'), ('3.5k Support', 'support')]
        else:
            entry_price = random.uniform(80, 150)
            key_levels = [('100 Resistance', 'resistance'), ('90 Support', 'support'),
                          ('110 Resistance', 'resistance'), ('85 Support', 'support')]

        pnl_percent = random.uniform(-10, 15)
        exit_price = entry_price * (1 + pnl_percent / 100)
        quantity = random.uniform(0.1, 2.0)
        pnl = (exit_price - entry_price) * quantity

        key_level, key_level_type = random.choice(key_levels)
        confirmations = ['Volume Spike', 'Order Book', 'RSI Divergence', 'Trend Break']
        models = ['Breakout', 'Pullback', 'Reversal', 'Trend Following']

        conn.execute('''
            INSERT INTO trades (symbol, asset, side, entry_price, exit_price, quantity,
                              entry_time, exit_time, pnl, pnl_percentage,
                              key_level, key_level_type, confirmation, model)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            symbol, asset, side, round(entry_price, 2), round(exit_price, 2), round(quantity, 3),
            entry_date.strftime('%Y-%m-%d %H:%M:%S'), exit_date.strftime('%Y-%m-%d %H:%M:%S'),
            round(pnl, 2), round(pnl_percent, 2),
            key_level, key_level_type,
            random.choice(confirmations), random.choice(models)
        ))

    conn.commit()
    conn.close()
    print("✅ Added 30 sample trades")


# ==================== STATS ====================
def calculate_stats(trades, category):
    stats = {}
    for trade in trades:
        value = trade.get(category)
        if not value:
            continue
        if value not in stats:
            stats[value] = {'total': 0, 'wins': 0, 'win_rate': 0}
        stats[value]['total'] += 1
        if trade.get('pnl', 0) > 0:
            stats[value]['wins'] += 1
        stats[value]['win_rate'] = round((stats[value]['wins'] / stats[value]['total']) * 100, 1)
    return dict(sorted(stats.items(), key=lambda x: x[1]['total'], reverse=True))


def calculate_period_stats(trades, period='all'):
    """Calculate stats for day/week/month/all"""
    now = datetime.now()
    filtered_trades = []

    for trade in trades:
        if trade.get('exit_time'):
            try:
                if 'T' in trade['exit_time']:
                    trade_date = datetime.fromisoformat(trade['exit_time'].replace('Z', '+00:00'))
                else:
                    trade_date = datetime.strptime(trade['exit_time'], '%Y-%m-%d %H:%M:%S')

                if period == 'day':
                    if trade_date.date() == now.date():
                        filtered_trades.append(trade)
                elif period == 'week':
                    week_ago = now - timedelta(days=7)
                    if trade_date >= week_ago:
                        filtered_trades.append(trade)
                elif period == 'month':
                    month_ago = now - timedelta(days=30)
                    if trade_date >= month_ago:
                        filtered_trades.append(trade)
                else:  # 'all'
                    filtered_trades.append(trade)
            except:
                pass

    total = len(filtered_trades)
    winning = sum(1 for t in filtered_trades if t.get('pnl', 0) > 0)
    total_pnl = sum(t.get('pnl', 0) for t in filtered_trades)
    win_rate = round((winning / total * 100), 1) if total > 0 else 0

    return {
        'total_trades': total,
        'winning_trades': winning,
        'total_pnl': round(total_pnl, 2),
        'win_rate': win_rate
    }


# ==================== MAIN PAGE ====================
@app.route('/')
def dashboard():
    conn = get_db()
    cursor = conn.execute('SELECT * FROM trades WHERE status = "closed" ORDER BY exit_time DESC')
    trades = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # If no trades, add sample data
    if len(trades) < 5:
        add_sample_data()
        return dashboard()  # Reload

    # ========== CALENDAR DATA ==========
    trades_by_date = {}
    for trade in trades:
        if trade.get('exit_time'):
            try:
                exit_time_str = str(trade['exit_time'])
                if 'T' in exit_time_str:
                    date = exit_time_str.split('T')[0]
                else:
                    date = exit_time_str.split(' ')[0]

                if len(date) == 10 and date[4] == '-' and date[7] == '-':
                    if date not in trades_by_date:
                        trades_by_date[date] = {
                            'total_trades': 0,
                            'total_pnl': 0.0,
                            'wins': 0,
                            'losses': 0,
                            'trades': []
                        }

                    trades_by_date[date]['total_trades'] += 1
                    trades_by_date[date]['total_pnl'] += float(trade.get('pnl', 0))

                    if float(trade.get('pnl', 0)) > 0:
                        trades_by_date[date]['wins'] += 1
                    else:
                        trades_by_date[date]['losses'] += 1

                    # Store trade ID for quick access
                    trades_by_date[date]['trades'].append(trade['id'])

            except Exception as e:
                print(f"Error processing date: {e}")

    # Convert to JSON safely
    try:
        trades_by_date_json = json.dumps(trades_by_date)
    except:
        trades_by_date_json = '{}'

    # ========== PERIOD STATS ==========
    all_stats = calculate_period_stats(trades, 'all')
    day_stats = calculate_period_stats(trades, 'day')
    week_stats = calculate_period_stats(trades, 'week')
    month_stats = calculate_period_stats(trades, 'month')

    # ========== CATEGORY STATS ==========
    key_levels_stats = calculate_stats(trades, 'key_level')
    confirmations_stats = calculate_stats(trades, 'confirmation')
    models_stats = calculate_stats(trades, 'model')

    # ========== ASSETS ==========
    assets = sorted(set(t.get('asset', 'Unknown') for t in trades))

    # Recent trades (5 only)
    recent_trades = trades[:5]

    return render_template(
        'single_page.html',
        trades=recent_trades,
        all_stats=all_stats,
        day_stats=day_stats,
        week_stats=week_stats,
        month_stats=month_stats,
        trades_by_date=trades_by_date_json,
        key_levels_stats=key_levels_stats,
        confirmations_stats=confirmations_stats,
        models_stats=models_stats,
        assets=assets,
        total_trades=all_stats['total_trades']  # For compatibility
    )


# ==================== API ROUTES ====================
@app.route('/api/day_trades/<date>')
def day_trades(date):
    conn = get_db()
    cursor = conn.execute('SELECT * FROM trades WHERE exit_time LIKE ?', (f'{date}%',))
    trades = [dict(row) for row in cursor.fetchall()]
    conn.close()

    daily_pnl = sum(t.get('pnl', 0) for t in trades)
    wins = sum(1 for t in trades if t.get('pnl', 0) > 0)

    return jsonify({
        'trades': trades,
        'stats': {
            'date': date,
            'total_trades': len(trades),
            'winning_trades': wins,
            'daily_pnl': round(daily_pnl, 2),
            'daily_win_rate': round((wins / len(trades)) * 100, 1) if trades else 0
        }
    })


@app.route('/api/get_trade/<int:trade_id>')
def get_trade(trade_id):
    conn = get_db()
    cursor = conn.execute('SELECT * FROM trades WHERE id = ?', (trade_id,))
    trade = cursor.fetchone()
    conn.close()

    if trade:
        return jsonify({'success': True, 'trade': dict(trade)})
    return jsonify({'success': False, 'error': 'Trade not found'})


@app.route('/api/update_trade/<int:trade_id>', methods=['POST'])
def update_trade(trade_id):
    data = request.json
    conn = get_db()

    updates = []
    values = []
    for field in ['key_level', 'key_level_type', 'confirmation', 'model', 'notes', 'screenshot']:
        if field in data:
            updates.append(f"{field} = ?")
            values.append(data[field])

    if updates:
        values.append(trade_id)
        conn.execute(f"UPDATE trades SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()

    conn.close()
    return jsonify({'success': True})


@app.route('/api/delete_trade/<int:trade_id>', methods=['DELETE'])
def delete_trade(trade_id):
    conn = get_db()
    conn.execute('DELETE FROM trades WHERE id = ?', (trade_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/add_trade', methods=['POST'])
def add_trade():
    data = request.json
    conn = get_db()

    # Calculate P&L
    pnl = (data['exit_price'] - data['entry_price']) * data['quantity']
    if data['side'] == 'sell':
        pnl = -pnl
    pnl_percent = ((data['exit_price'] - data['entry_price']) / data['entry_price']) * 100

    conn.execute('''
        INSERT INTO trades (asset, side, entry_price, exit_price, quantity,
                          entry_time, exit_time, pnl, pnl_percentage,
                          key_level, key_level_type, confirmation, model, screenshot, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['asset'], data['side'], data['entry_price'], data['exit_price'],
        data['quantity'], data.get('entry_time', datetime.now().isoformat()),
        data.get('exit_time', datetime.now().isoformat()), pnl, pnl_percent,
        data.get('key_level', ''), data.get('key_level_type', ''),
        data.get('confirmation', ''), data.get('model', ''),
        data.get('screenshot', ''), 'closed'
    ))

    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/get_categories')
def get_categories():
    conn = get_db()
    categories = {
        'key_levels': [r[0] for r in conn.execute(
            'SELECT DISTINCT key_level FROM trades WHERE key_level IS NOT NULL AND key_level != ""').fetchall()],
        'confirmations': [r[0] for r in conn.execute(
            'SELECT DISTINCT confirmation FROM trades WHERE confirmation IS NOT NULL AND confirmation != ""').fetchall()],
        'models': [r[0] for r in
                   conn.execute('SELECT DISTINCT model FROM trades WHERE model IS NOT NULL AND model != ""').fetchall()]
    }
    conn.close()
    return jsonify(categories)


@app.route('/api/update_category', methods=['POST'])
def update_category():
    data = request.json
    conn = get_db()
    conn.execute(f"UPDATE trades SET {data['type']} = ? WHERE {data['type']} = ?",
                 (data['new_name'], data['old_name']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/delete_category', methods=['POST'])
def delete_category():
    data = request.json
    conn = get_db()
    conn.execute(f"UPDATE trades SET {data['type']} = NULL WHERE {data['type']} = ?", (data['name'],))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ==================== START ====================
if __name__ == '__main__':
    init_db()
    add_sample_data()

    print("=" * 60)
    print("🚀 TRADING JOURNAL - FINAL VERSION")
    print("=" * 60)
    print("✅ Calendar with clickable dates")
    print("✅ Add trade with ALL fields")
    print("✅ Period filters (Day/Week/Month/All)")
    print("✅ Better color coding")
    print("✅ 5 recent trades only")
    print("✅ Complete category management")
    print("=" * 60)
    print("=" * 60)

    app.run(debug=True, port=5000)