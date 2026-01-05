# Trading Journal - Professional Analytics Platform

A Bloomberg-style trading journal with Bybit integration, performance analytics, and interactive calendar.

## ✨ Features

✅ **Professional UI** - Black/white/yellow Bloomberg-style interface  
✅ **Real-time Analytics** - Profit Factor, Expectancy, Win Rate, Risk:Reward  
✅ **Interactive Calendar** - Daily P&L tracking with clickable days  
✅ **Trade Details** - 3-tab layout with screenshots, key levels, confirmations  
✅ **Bybit Integration** - Testnet API for real trade data  
✅ **SQLite Database** - Complete trading history storage  

## 🚀 Quick Start

1. **Clone repository**
\\\ash
git clone <repository-url>
cd TJ
\\\

2. **Install dependencies**
\\\ash
pip install -r requirements.txt
\\\

3. **Configure API (optional)**
\\\ash
copy config\api_config.example.py config\api_config.py
# Edit with your Bybit API keys
\\\

4. **Run application**
\\\ash
python app.py
\\\

5. **Open in browser**
\\\
http://127.0.0.1:5000
\\\

## 📊 Dashboard Features

- **Account Balance**: Real-time calculation
- **Performance Metrics**: Accurate Profit Factor, Expectancy, Win Rate
- **Recent Trades**: Last 10 closed trades with win/loss highlighting
- **Open Positions**: Current active trades
- **Best/Worst Trade**: Identification and statistics
- **Win/Loss Streak**: Consecutive tracking

## 🔧 Technical Stack

- **Backend**: Flask, SQLAlchemy
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **API**: Bybit Testnet

## 🗂️ Clean Project Structure

\\\
TJ/
├── app.py                    # Main Flask application
├── config/                  # Configuration files
├── static/                  # CSS, JS, assets
├── templates/               # HTML templates
├── utils/                   # Utility modules
├── requirements.txt         # Python dependencies
└── README.md               # Documentation
\\\
"@ | Out-File -FilePath "README.md" -Encoding UTF8





# Files to KEEP:
# app.py, trading_journal.db (gitignored), requirements.txt, .gitignore, README.md
# config/, static/, templates/, utils/

# Remove old test/debug/duplicate files
Remove-Item "add_daily_stats.py"
Remove-Item "check_app.py"
Remove-Item "check_datatbase_trades.py"
Remove-Item "check_db.py"
Remove-Item "check_trades.py"
Remove-Item "cleanup_trade_data.py"
Remove-Item "database.py"
Remove-Item "data_fetcher.py"
Remove-Item "day11_main.py"
Remove-Item "day11_pro_journal.py"
Remove-Item "day11_pro_ui.py"
Remove-Item "day1_manual_journal.py"
Remove-Item "day2_sqlite_journal.py"
Remove-Item "day3_pandas_analysis.py"
Remove-Item "day4_test.py"
Remove-Item "day5_final_working.py"
Remove-Item "day6_basic_dashboard.py"
Remove-Item "day7_calendar_view.py"
Remove-Item "day8_trade_modal.py"
Remove-Item "day9_analytics.py"
Remove-Item "fetch_real_trades.py"
Remove-Item "final_data_fix.py"
Remove-Item "final_test.py"
Remove-Item "fix_all_issues.py"
Remove-Item "fix_daily_stats.py"
Remove-Item "fix_database.py"
Remove-Item "fix_env.py"
Remove-Item "fix_recent_trades_display.py"
Remove-Item "fix_trades_matching.py"
Remove-Item "key_levels_export.csv"
Remove-Item "main.py"
Remove-Item "save_trades_simple.py"
Remove-Item "setup_database.py"
Remove-Item "simple_pnl_chart.png"
Remove-Item "test_bybit_simple.py"
Remove-Item "test_fix.py"
Remove-Item "test_imports.py"
Remove-Item "test_jinja.py"
Remove-Item "trades.db"
Remove-Item "trades.json"
Remove-Item "trades_export.csv"
Remove-Item "tradezilla_core.py"
Remove-Item "tradezilla_dashboard.py"
Remove-Item "tradezilla_final.py"
Remove-Item "tradezilla_pro.py"
Remove-Item "tradezilla_simple.py"
Remove-Item "trading_report.csv"
Remove-Item "trading_summary.csv"
Remove-Item "trading_web.py"
Remove-Item "update_app_for_all_trades.py"
Remove-Item "web_ui.py"

# Remove empty directories if they exist
Remove-Item "data" -Recurse -ErrorAction SilentlyContinue
Remove-Item "database" -Recurse -ErrorAction SilentlyContinue
Remove-Item "modules" -Recurse -ErrorAction SilentlyContinue
Remove-Item "tests" -Recurse -ErrorAction SilentlyContinue

# Remove pycache directories
Remove-Item "__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

# Create example API config
@"
# Bybit API Configuration
# Copy this file to api_config.py and fill in your keys

BYBIT_API_KEY = 'your_api_key_here'
BYBIT_API_SECRET = 'your_api_secret_here'
BYBIT_TESTNET = True  # Use testnet for development

# Database configuration
DATABASE_PATH = 'trading_journal.db'

# Flask configuration
SECRET_KEY = 'dev-secret-key-change-in-production'
DEBUG = True
