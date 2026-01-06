📊 Professional Trading Journal
A modern, web-based trading journal for serious traders. Track your trades, analyze performance, and improve your strategy with beautiful visualizations and powerful analytics.

https://img.shields.io/badge/version-1.2.0-green https://img.shields.io/badge/python-3.8+-blue https://img.shields.io/badge/flask-2.3.3-lightgrey https://img.shields.io/badge/license-MIT-orange

✨ Features
📅 Calendar View
Visualize trading days with color-coded P&L (Green = Profit, Red = Loss)

Click any day to view trades for that specific day

Monthly/weekly performance overview

Clean dark calendar with white weekday headers and minimal navigation

📈 Advanced Statistics
Key Levels Analysis: Track Support/Resistance performance

Confirmation Metrics: Analyze which confirmation methods work best

Model Performance: Evaluate different trading models

Filter by: Asset (BTC/ETH/SOL) and Trade Type

Period Filters: Day/Week/Month/All time views + **Custom date range**

💼 Trade Management
Add, edit, delete trades with full details

Capture screenshots with automatic URL management

Detailed notes and analysis for each trade

Categorize trades by Key Level, Confirmation, and Model

Track Weekly and Daily Bias per trade (Bullish/Bearish/Neutral)

🔄 Bybit Integration
✅ **FULLY WORKING** - Auto-sync trades directly from Bybit exchange

Support for both mainnet and testnet networks

Secure API key management with local storage only

Real-time trade synchronization with duplicate prevention

Automatic trade validation and normalization

Handles USDT linear and inverse perpetual contracts

Import history with proper timestamp conversion

🎨 Professional UI
Dark theme optimized for traders with neon P&L indicators

Responsive design works on all devices

Intuitive drag-and-drop calendar

Real-time statistics updates

Readable dark panels across metrics, calendar, trades list, and stats

**New in v1.2:**
- ✅ **Bybit sync fully implemented and tested**
- Automatic trade import from Bybit API
- Duplicate prevention and validation
- Support for USDT linear/inverse contracts
- Comprehensive error handling and logging
- Debug tools for troubleshooting

**Previous v1.1 features:**
- Custom timeframe selector for key metrics and P&L chart
- Thin dashed white zero-line on cumulative P&L chart (no fill)
- Distinct accent colors for Key Levels / Confirmations / Models stats boxes
- Clean calendar styling: white weekday headers, no button rectangles
- Slightly more compact metrics dashboard

🚀 Quick Start
Prerequisites
Python 3.8 or higher

Git

Installation
Clone the repository

bash
git clone https://github.com/Imbalance983/automated-trading-journal.git
cd automated-trading-journal
Install dependencies

bash
pip install -r requirements.txt
Run the application

bash
python app.py
Open in browser

text
http://127.0.0.1:5000
📁 Project Structure
text
automated-trading-journal/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This documentation
├── .gitignore            # Git ignore rules
├── templates/
│   └── single_page.html  # Complete web interface
└── trading_journal.db    # SQLite database (auto-created)
🛠️ Usage Guide
Adding Trades Manually
Click the "➕ Add Trade" button

Fill in trade details:

Asset (BTC, ETH, SOL)

Side (Long/Short)

Entry/Exit prices

Quantity

Date and Time

Add analysis:

Key Level (Support/Resistance)

Confirmation method

Trading model

Weekly Bias (Bullish/Bearish/Neutral)

Daily Bias (Bullish/Bearish/Neutral)

Optional: Add screenshot URL and notes

Click "Save Trade"

Using Bybit Integration
✅ **Fully Tested and Working**

1. Get API keys from Bybit:
   - Go to Bybit → API Management
   - Create API key with "Read" permissions
   - Copy API Key and Secret

2. Configure in app:
   - Go to "Bybit Sync" section
   - Enter API Key and Secret
   - Select network (Mainnet/Testnet)
   - Click "Save Credentials"

3. Sync trades:
   - Click "Sync Trades" to import automatically
   - App will fetch closed PnL positions
   - Validates and normalizes all trade data
   - Prevents duplicates automatically

4. Features:
   - Supports USDT linear & inverse contracts
   - Automatic timestamp conversion
   - Error handling with detailed logging
   - Trade validation before import

Analyzing Performance
Calendar: Click any day to see daily trades

Statistics: Filter by period (Day/Week/Month/All)

Key Levels: See which S/R levels are most profitable

Confirmations: Track which confirmation methods work best

Models: Analyze performance of different trading strategies

🔧 Configuration
Environment Variables
Create a .env file (optional):

env
FLASK_SECRET_KEY=your_secret_key_here
DEBUG=False
Database
The SQLite database is auto-created on first run. To reset:

bash
# Delete the database file
rm trading_journal.db
# Restart the app to create fresh database
python app.py
📊 Features in Detail
Calendar System
Color-coded days based on daily P&L

Click to view detailed trades

Monthly navigation

Profit/loss summary for each day

Trade Analysis
Win rate calculation

Average profit/loss per trade

Best/worst performing assets

Risk-reward ratios

Category Management
Customize Key Levels (Support/Resistance types)

Add/remove Confirmation methods

Manage Trading Models

Real-time category performance tracking

Data Export
Export trades to CSV

Print-friendly views

Screenshot gallery

🔐 Security Notes
API keys are stored locally only

No data is sent to external servers

Database is local to your machine

HTTPS recommended for production use

🤝 Contributing
Contributions are welcome! Please follow these steps:

Fork the repository

Create a feature branch (git checkout -b feature/AmazingFeature)

Commit your changes (git commit -m 'Add some AmazingFeature')

Push to the branch (git push origin feature/AmazingFeature)

Open a Pull Request

📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

⚠️ Disclaimer
This is a trading journal tool, not financial advice.

Past performance does not guarantee future results

Trading carries risk of loss

Always do your own research

Never trade with money you cannot afford to lose

🙏 Acknowledgments
Built with Flask

UI with Bootstrap

Icons from Font Awesome

Charts with Chart.js

Trading integration with Bybit API

📞 Support
For issues, questions, or feature requests:

Check the Issues page

Create a new issue if needed

Happy Trading! 📈💼
