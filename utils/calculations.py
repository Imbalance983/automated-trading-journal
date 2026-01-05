# utils/calculations.py
import sqlite3
import math
from datetime import datetime


def get_all_trades():
    """Get all trades from database for calculations"""
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT 
            id, symbol, entry_price, exit_price, 
            pnl, pnl_percentage, side, status, fee,
            strftime('%Y-%m-%d', entry_time) as trade_date
        FROM trades 
        WHERE status = 'closed'
        ORDER BY entry_time
    ''')

    trades = []
    for row in cursor.fetchall():
        trade = {
            'id': row[0],
            'symbol': row[1],
            'entry_price': float(row[2]) if row[2] else 0,
            'exit_price': float(row[3]) if row[3] else 0,
            'pnl': float(row[4]) if row[4] else 0,
            'pnl_percent': float(row[5]) if row[5] else 0,
            'side': row[6],
            'status': row[7],
            'fees': float(row[8]) if row[8] else 0,
            'date': row[9]
        }
        trades.append(trade)

    conn.close()
    return trades


def calculate_metrics(trades):
    """Calculate ALL trading metrics CORRECTLY"""
    if not trades:
        return {
            'profit_factor': 0,
            'expectancy': 0,
            'win_rate': 0,
            'risk_reward': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_profit': 0,
            'total_loss': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'largest_win': 0,
            'largest_loss': 0,
            'max_drawdown': 0
        }

    print(f"\n=== DEBUG: Analyzing {len(trades)} trades ===")
    for i, t in enumerate(trades[:5]):
        print(f"Trade {i + 1}: P&L = ${t['pnl']:.2f}, Win? {t['pnl'] > 0}")

    winning_trades = [t for t in trades if t['pnl'] > 0]
    losing_trades = [t for t in trades if t['pnl'] < 0]

    total_trades = len(trades)
    winning_count = len(winning_trades)
    losing_count = len(losing_trades)

    total_profit = sum(t['pnl'] for t in winning_trades)
    total_loss = abs(sum(t['pnl'] for t in losing_trades))

    avg_win = total_profit / winning_count if winning_count > 0 else 0
    avg_loss = total_loss / losing_count if losing_count > 0 else 0

    profit_factor = total_profit / total_loss if total_loss > 0 else 0

    win_rate = (winning_count / total_trades * 100) if total_trades > 0 else 0

    win_probability = winning_count / total_trades if total_trades > 0 else 0
    loss_probability = losing_count / total_trades if total_trades > 0 else 0
    expectancy = (win_probability * avg_win) - (loss_probability * avg_loss)

    risk_reward = avg_win / avg_loss if avg_loss > 0 else 0

    largest_win = max(t['pnl'] for t in winning_trades) if winning_trades else 0
    largest_loss = min(t['pnl'] for t in losing_trades) if losing_trades else 0

    running_pnl = 0
    peak = 0
    max_drawdown = 0

    for trade in trades:
        running_pnl += trade['pnl']
        if running_pnl > peak:
            peak = running_pnl
        drawdown = peak - running_pnl
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    print(f"\n=== CALCULATION RESULTS ===")
    print(f"Total Trades: {total_trades}")
    print(f"Winning: {winning_count}, Losing: {losing_count}")
    print(f"Total Profit: ${total_profit:.2f}")
    print(f"Total Loss: ${total_loss:.2f}")
    print(f"Avg Win: ${avg_win:.2f}, Avg Loss: ${avg_loss:.2f}")
    print(f"Profit Factor: {profit_factor:.2f}")
    print(f"Win Rate: {win_rate:.1f}%")
    print(f"Expectancy: ${expectancy:.2f}")
    print(f"Risk:Reward: {risk_reward:.2f}:1")
    print("========================\n")

    return {
        'profit_factor': round(profit_factor, 2),
        'expectancy': round(expectancy, 2),
        'win_rate': round(win_rate, 1),
        'risk_reward': round(risk_reward, 2),
        'total_trades': total_trades,
        'winning_trades': winning_count,
        'losing_trades': losing_count,
        'total_profit': round(total_profit, 2),
        'total_loss': round(total_loss, 2),
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'largest_win': round(largest_win, 2),
        'largest_loss': round(largest_loss, 2),
        'max_drawdown': round(max_drawdown, 2)
    }


def calculate_daily_summary(date=None):
    """Calculate metrics for a specific day or all days"""
    conn = sqlite3.connect('trading_journal.db')
    cursor = conn.cursor()

    if date:
        cursor.execute('''
            SELECT pnl, pnl_percentage 
            FROM trades 
            WHERE strftime('%Y-%m-%d', entry_time) = ? 
            AND status = 'closed'
        ''', (date,))
    else:
        cursor.execute('''
            SELECT 
                strftime('%Y-%m-%d', entry_time) as trade_date,
                COUNT(*) as trade_count,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as win_count,
                SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as loss_count,
                SUM(pnl) as total_pnl
            FROM trades 
            WHERE status = 'closed'
            GROUP BY strftime('%Y-%m-%d', entry_time)
            ORDER BY trade_date DESC
        ''')

    results = cursor.fetchall()
    conn.close()

    if date and results:
        trades = [{'pnl': float(row[0]), 'pnl_percent': float(row[1])} for row in results]
        winning = sum(1 for t in trades if t['pnl'] > 0)
        total = len(trades)
        win_rate = (winning / total * 100) if total > 0 else 0
        total_pnl = sum(t['pnl'] for t in trades)

        return {
            'date': date,
            'trade_count': total,
            'win_count': winning,
            'loss_count': total - winning,
            'total_pnl': round(total_pnl, 2),
            'win_rate': round(win_rate, 1)
        }

    daily_data = []
    for row in results:
        daily_data.append({
            'date': row[0],
            'trade_count': row[1],
            'win_count': row[2],
            'loss_count': row[3],
            'total_pnl': round(float(row[4]) if row[4] else 0, 2),
            'win_rate': round((row[2] / row[1] * 100) if row[1] > 0 else 0, 1)
        })

    return daily_data