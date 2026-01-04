# 🚀 Automated Trading Journal

A **complete trading journal system** built in Python over 10 days. Track trades, analyze performance, manage key levels, and generate reports - all in one terminal application.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## 📋 Features

### ✅ **Core Trading Journal**
- Add, view, and manage trades
- Track entry/exit prices, quantities, P&L
- Record emotional state and setup classification
- SQLite database for persistent storage

### 📊 **Performance Dashboard**
- Real-time win rate calculation
- Total P&L tracking
- Average win/loss statistics
- Recent trades overview

### 🎯 **Key Levels System**
- Create and manage support/resistance levels
- Star-based strength rating (1-5 stars)
- Track key level effectiveness
- Calendar view of upcoming tests

### 📈 **Advanced Analytics**
- Win rate by setup type
- P&L by emotional state
- Key level success rates
- Advanced metrics (Sharpe ratio, profit factor, expectancy)
- CSV export functionality

## 🏗️ Project Structure
automated-trading-journal-main/
├── main.py # 🎯 MAIN APPLICATION
├── trading_journal.db # Database (trades + key levels)
├── day1_manual_journal.py # Day 1: Basic journal
├── day2_sqlite_journal.py # Day 2: Database integration
├── day3_pandas_analysis.py # Day 3: Data analysis
├── day4_test.py # Day 4: Testing framework
├── day5_final_working.py # Day 5: Core trading system
├── day6_basic_dashboard.py # Day 6: Dashboard
├── day7_simple_calendar.py # Day 7: Key levels & calendar
├── day8_trade_modal.py # Day 8: Enhanced trade modal
├── day9_analytics.py # Day 9: Advanced analytics
├── database/ # Database operations
├── utils/ # Utility functions
└── README.md # This file


## 🚀 Quick Start

### 1. Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd automated-trading-journal-main

# Install dependencies
pip install pandas

python main.py

==================================================
🚀 AUTOMATED TRADING JOURNAL
==================================================

MAIN MENU:
1. 📝 View Trades
2. ➕ Add Trade
3. 📊 View Dashboard
4. 🎯 View Key Levels
5. 📈 Advanced Analytics
6. 🚪 Exit
==================================================

Enter choice (1-6):

📖 User Guide
Adding a Trade
Select option 2 from main menu

Enter trade details:

Symbol (e.g., BTC-USD)

Entry and exit prices

Quantity

Optional: Setup type and emotional state

System automatically calculates P&L and outcome

Viewing Performance
Option 1: View all trades in clean table format

Option 3: Dashboard with win rate, total P&L, averages

Option 5: Advanced analytics with detailed breakdowns

Managing Key Levels
Select option 4 from main menu

Choose "Add new key level"

Enter:

Key level name (e.g., "Daily Pivot", ".618")

Optional symbol association

Strength rating (1-5 stars)

ANALYTICS
==================================================

📊 PERFORMANCE:
   Total Trades: 12
   Win Rate: 91.7%
   Total P&L: $21,855.00
   Average Win: $1,998.18
   Average Loss: $-125.00

🏆 BEST & WORST TRADES:
   Best:
     BTCUSDT: $+20,000.00
     BTCUSDT: $+500.00
     BTCUSD: $+420.00

Key Metrics Calculated
Win Rate: Percentage of profitable trades

Profit Factor: Gross profit / gross loss

Sharpe Ratio: Risk-adjusted returns

Maximum Drawdown: Largest peak-to-trough decline

System Expectancy: Average profit per trade

📈 Roadmap
Current Features (MVP Complete ✅)
Basic trade journal

Performance dashboard

Key levels management

Advanced analytics

CSV export

Unified main application

Future Enhancements
Web-based interface

PDF report generation

Email notifications

Multi-user support

Advanced chart integration

API for broker integration

🤝 Contributing
Fork the repository

Create a feature branch

Commit your changes

Push to the branch

Open a Pull Request

📄 License
MIT License - see LICENSE file for details

🙏 Acknowledgments
Built over 10 days as a complete project

Designed for traders by traders

Focus on simplicity and usability

All data stored locally for privacy

📞 Support
For issues or questions:

Check existing issues on GitHub

Create a new issue with details

Include error messages and steps to reproduce
