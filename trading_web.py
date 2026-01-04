# trading_web.py - SIMPLE FIXED VERSION
import sqlite3
from flask import Flask
import os
from datetime import datetime

app = Flask(__name__)


@app.route('/')
def dashboard():
    """Simple working dashboard"""
    try:
        # Connect to database
        conn = sqlite3.connect('trading_journal.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all trades
        cursor.execute("SELECT * FROM trades ORDER BY entry_time DESC")
        trades = cursor.fetchall()

        # Calculate statistics
        total_trades = len(trades)

        if total_trades > 0:
            # Calculate basic stats
            winning_trades = [t for t in trades if t['pnl'] > 0]
            losing_trades = [t for t in trades if t['pnl'] <= 0]

            win_count = len(winning_trades)
            loss_count = len(losing_trades)
            win_rate = (win_count / total_trades) * 100
            total_pnl = sum(t['pnl'] for t in trades)
            avg_win = sum(t['pnl'] for t in winning_trades) / win_count if win_count > 0 else 0
            avg_loss = sum(t['pnl'] for t in losing_trades) / loss_count if loss_count > 0 else 0

            # Find best trade
            best_trade = max(trades, key=lambda x: x['pnl'])
            best_symbol = best_trade['symbol']
            best_pnl = best_trade['pnl']
        else:
            win_count = loss_count = win_rate = total_pnl = avg_win = avg_loss = 0
            best_symbol = "N/A"
            best_pnl = 0

        conn.close()

        # Generate HTML
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Trading Journal Dashboard</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 15px;
                    padding: 30px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                }}
                h1 {{
                    color: #2d3748;
                    font-size: 2.5em;
                    margin-bottom: 10px;
                }}
                .stats {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 40px;
                }}
                .stat-card {{
                    background: #f8fafc;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                }}
                .stat-number {{
                    font-size: 2em;
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
                .positive {{ color: #10b981; }}
                .negative {{ color: #ef4444; }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #e2e8f0;
                }}
                th {{
                    background: #f1f5f9;
                }}
                .buy {{ color: green; font-weight: bold; }}
                .sell {{ color: red; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Trading Journal Dashboard</h1>
                    <p>Professional Trading Analytics</p>
                </div>

                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number">{total_trades}</div>
                        <div>Total Trades</div>
                        <small>{win_count} wins • {loss_count} losses</small>
                    </div>

                    <div class="stat-card">
                        <div class="stat-number positive">{win_rate:.1f}%</div>
                        <div>Win Rate</div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-number {'positive' if total_pnl >= 0 else 'negative'}">${total_pnl:,.2f}</div>
                        <div>Total P&L</div>
                    </div>

                    <div class="stat-card">
                        <div class="stat-number positive">${best_pnl:,.2f}</div>
                        <div>Best Trade</div>
                        <small>{best_symbol}</small>
                    </div>
                </div>

                <h2>Trade History ({total_trades} trades)</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>Side</th>
                            <th>Entry</th>
                            <th>Exit</th>
                            <th>P&L</th>
                            <th>Time</th>
                        </tr>
                    </thead>
                    <tbody>
        '''

        # Add trade rows
        for trade in trades:
            symbol = trade['symbol']
            side = trade['side']
            entry = trade['entry_price']
            exit_price = trade['exit_price']
            pnl = trade['pnl']
            entry_time = trade['entry_time'][:19] if trade['entry_time'] else 'N/A'

            pnl_class = "positive" if pnl > 0 else "negative"
            side_class = "buy" if side.lower() == 'buy' else "sell"

            html += f'''
                        <tr>
                            <td><strong>{symbol}</strong></td>
                            <td class="{side_class}">{side.upper()}</td>
                            <td>${entry:,.2f}</td>
                            <td>${exit_price:,.2f}</td>
                            <td class="{pnl_class}">${pnl:,.2f}</td>
                            <td>{entry_time}</td>
                        </tr>
            '''

        html += f'''
                    </tbody>
                </table>

                <div style="margin-top: 40px; padding: 20px; background: #f1f5f9; border-radius: 10px;">
                    <h3>📈 Performance Summary</h3>
                    <p>Average Win: <span class="positive">${avg_win:,.2f}</span></p>
                    <p>Average Loss: <span class="negative">${avg_loss:,.2f}</span></p>
                    <p>Profit Factor: <strong>{abs(avg_win / avg_loss):.2f}x</strong> (if avg_loss != 0)</p>
                </div>

                <div style="text-align: center; margin-top: 30px; color: #64748b; font-size: 0.9em;">
                    <p>Trading Journal • {datetime.now().strftime('%Y-%m-%d %H:%M')} • {total_trades} trades</p>
                </div>
            </div>
        </body>
        </html>
        '''

        return html

    except Exception as e:
        return f'''
        <!DOCTYPE html>
        <html>
        <body style="padding: 50px; font-family: Arial;">
            <h1 style="color: red;">Error</h1>
            <p><strong>{str(e)}</strong></p>
            <p>Database: trading_journal.db</p>
            <p><a href="/">Refresh</a></p>
        </body>
        </html>
        '''


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 TRADING JOURNAL WEB APP - SIMPLE & WORKING")
    print("=" * 60)
    print("🌐 Open: http://127.0.0.1:5010")
    print("=" * 60)
    app.run(debug=True, port=5010, host='127.0.0.1')