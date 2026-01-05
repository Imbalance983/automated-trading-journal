📊 Professional Trading Journal
A modern, web-based trading journal for serious traders. Track your trades, analyze performance, and improve your strategy with beautiful visualizations and powerful analytics.

https://img.shields.io/badge/version-1.0.0-green https://img.shields.io/badge/python-3.8+-blue https://img.shields.io/badge/flask-2.3.3-lightgrey https://img.shields.io/badge/license-MIT-orange

✨ Features
📅 Calendar View
Visualize trading days with color-coded P&L (Green = Profit, Red = Loss)

Click any day to view trades for that specific day

Monthly/weekly performance overview

📈 Advanced Statistics
Key Levels Analysis: Track Support/Resistance performance

Confirmation Metrics: Analyze which confirmation methods work best

Model Performance: Evaluate different trading models

Filter by: Asset (BTC/ETH/SOL) and Trade Type

Period Filters: Day/Week/Month/All time views

💼 Trade Management
Add, edit, delete trades with full details

Capture screenshots with automatic URL management

Detailed notes and analysis for each trade

Categorize trades by Key Level, Confirmation, and Model

🔄 Bybit Integration
Auto-sync trades directly from Bybit exchange

Support for both mainnet and testnet

Secure API key management

Real-time trade synchronization

🎨 Professional UI
Dark theme optimized for traders

Responsive design works on all devices

Intuitive drag-and-drop calendar

Real-time statistics updates

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
├── static/               # CSS, JavaScript, images
│   ├── css/
│   ├── js/
│   └── images/
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

Optional: Add screenshot URL and notes

Click "Save Trade"

Using Bybit Integration
Get API keys from Bybit

Go to "Bybit Sync" section

Enter API Key and Secret

Select network (Mainnet/Testnet)

Click "Save Credentials"

Click "Sync Trades" to import automatically

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
