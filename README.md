# 📊 Automated Trading Journal

> A professional-grade trading journal web application with real-time Bybit API integration, performance analytics, and position sizing calculator.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)]()

![Trading Journal Dashboard](https://via.placeholder.com/800x400/0a0a0a/10b981?text=Trading+Journal+Dashboard)

## 🎯 Overview

A comprehensive trading journal application designed for cryptocurrency traders to track, analyze, and optimize their trading performance. Features real-time integration with Bybit exchange, advanced analytics, and risk management tools.

### ✨ Key Features

#### 📈 **Real-Time Bybit Integration**
- Automatic trade synchronization from Bybit API
- Live account balance tracking (USDT equity)
- Position and order monitoring
- Secure credential storage with SQLite

#### 📊 **Advanced Analytics**
- Interactive performance charts (Chart.js)
- Win rate and profit factor metrics
- Risk/reward ratio analysis
- Drawdown tracking
- Time-based performance heatmaps

#### 🎯 **Position Size Calculator**
- Real-time position sizing based on risk parameters
- Support for percentage or USDT-based risk
- Stop loss percentage calculator
- Visual double-width card for easy access

#### 📅 **Calendar View**
- Daily P&L visualization
- Trade count and win rate per day
- Interactive FullCalendar integration
- Quick access to historical trades

#### 🔒 **Security & Persistence**
- Encrypted API credentials
- Session management
- SQLite database for data persistence
- Credentials survive server restarts

## 🚀 Quick Start

### Prerequisites

```bash
Python 3.8+
pip (Python package manager)
Bybit API credentials (optional for manual entry)
```

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Imbalance983/automated-trading-journal.git
cd automated-trading-journal
```

2. **Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables** (optional)
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**
```bash
python app.py
# Database will auto-initialize on first run
```

6. **Run the application**
```bash
python app.py
```

7. **Access the application**
```
Open browser: http://localhost:5000
```

## 🎨 Screenshots

### Dashboard Overview
Comprehensive metrics dashboard with real-time data:
- Account balance
- Total P&L
- Win rate with visual chart
- Profit factor and expectancy

### Position Calculator
Double-width calculator for easy position sizing:
- Risk amount input (USDT or %)
- Stop loss percentage
- Automatic position size calculation

### Calendar View
Interactive calendar showing daily trading performance:
- Color-coded P&L days
- Trade count per day
- Win rate statistics

## 🏗️ Architecture

### Tech Stack

**Backend:**
- Flask 3.0+ (Python web framework)
- SQLite (Database)
- pybit (Bybit API client)
- CORS support

**Frontend:**
- Vanilla JavaScript (ES6+)
- Chart.js (Analytics visualization)
- FullCalendar (Calendar view)
- Responsive CSS Grid layout

**API Integration:**
- Bybit Unified Trading Account API
- RESTful endpoints
- Async data fetching

### Project Structure

```
automated-trading-journal/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in repo)
├── .gitignore             # Git ignore rules
├── trading_journal.db     # SQLite database (auto-generated)
├── templates/
│   └── single_page.html   # Main SPA template
├── screenshots/           # User-uploaded trade screenshots
└── README.md             # This file
```

### Database Schema

#### `users` Table
- Multi-user support
- User identification and session management

#### `trades` Table
- Comprehensive trade data
- Entry/exit prices, P&L, timestamps
- Strategy metadata (bias, model, confirmations)
- Screenshot attachments

#### `api_credentials` Table
- Encrypted Bybit API credentials
- Network selection (mainnet/testnet)
- Remember me functionality

#### `account_balances` Table
- Historical balance snapshots
- Per-coin equity tracking
- Sync timestamps

#### `positions` Table
- Current position tracking
- Symbol, side, size, entry price
- Unrealized P&L
- Leverage information

#### `open_orders` Table
- Active order monitoring
- Order type, price, quantity
- Status tracking

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-here

# Bybit API (optional - can be set in UI)
BYBIT_API_KEY=your-api-key
BYBIT_API_SECRET=your-api-secret
BYBIT_NETWORK=mainnet  # or testnet

# Database
DATABASE_PATH=trading_journal.db
```

### Bybit API Permissions Required

When creating your Bybit API key, enable:
- ✅ Read position
- ✅ Read trade
- ✅ Read wallet balance
- ❌ Trade (not required)
- ❌ Withdraw (not required)

## 📖 Usage Guide

### 1. Connect Bybit Account

1. Navigate to http://localhost:5000
2. Enter your Bybit API credentials
3. Click "Save"
4. Credentials are automatically persisted

### 2. Sync Trades

1. Click the "Sync" button
2. Application fetches closed positions from last 90 days
3. Trades are automatically imported and deduplicated

### 3. Manual Trade Entry

1. Scroll to trade entry form
2. Fill in trade details:
   - Asset, side (long/short)
   - Entry/exit prices
   - Stop loss and take profit
   - Trade metadata (model, bias, confirmations)
3. Upload screenshot (optional)
4. Submit

### 4. Position Calculator

1. Enter risk amount (USDT or %)
2. Enter stop loss percentage
3. Position size automatically calculated
4. Use calculated size for next trade

### 5. Analytics & Reports

- View performance metrics in dashboard
- Check calendar for daily P&L
- Analyze heatmaps for time-based patterns
- Filter trades by asset, bias, or side

## 🛠️ API Endpoints

### Trade Management
- `GET /api/trades` - Fetch trades with filters
- `POST /api/trades` - Create new trade
- `PUT /api/trades/<id>` - Update trade
- `DELETE /api/trades/<id>` - Delete trade

### Bybit Integration
- `GET /api/get_bybit_credentials` - Check connection status
- `POST /api/save_bybit_credentials` - Save API credentials
- `POST /api/sync_bybit_trades` - Sync closed trades
- `POST /api/sync_extended_data` - Full account snapshot
- `GET /api/bybit/balance` - Get USDT equity

### Analytics
- `GET /api/calendar_data` - Daily P&L data
- `GET /api/risk_metrics` - Risk analysis
- `GET /api/time_analytics` - Performance by time

### User Management
- `GET /api/users` - List all users
- `POST /api/users` - Create new user
- `POST /api/switch_user/<id>` - Switch active user

## 🐛 Troubleshooting

### Issue: Balance shows $0
**Solution:** Ensure API key has "Read wallet balance" permission

### Issue: Trades not syncing
**Solution:**
1. Check API credentials are valid
2. Verify network setting (mainnet vs testnet)
3. Check Bybit API status

### Issue: Connection lost after refresh
**Solution:** This shouldn't happen. If it does:
1. Check database file exists
2. Verify `remember_me` is enabled
3. Check browser console for errors

### Issue: JavaScript errors in console
**Solution:** Hard refresh (Ctrl+Shift+R) to clear cache

## 🧪 Testing

### Manual Testing Checklist

- [ ] Connect Bybit API
- [ ] Refresh page - still connected
- [ ] Sync trades successfully
- [ ] Balance displays correctly (~USDT equity)
- [ ] Manual trade entry works
- [ ] Position calculator calculates correctly
- [ ] Calendar shows trades
- [ ] Charts render properly
- [ ] No console errors (F12)

## 🚀 Deployment

### Production Considerations

1. **Change Flask secret key**
```python
app.secret_key = 'your-production-secret-key'
```

2. **Use production WSGI server**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

3. **Enable HTTPS**
- Use reverse proxy (nginx)
- Configure SSL certificates

4. **Database backups**
```bash
# Backup database regularly
cp trading_journal.db backups/trading_journal_$(date +%Y%m%d).db
```

5. **Environment variables**
- Use proper secret management
- Never commit `.env` to git

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Coding Standards
- Follow PEP 8 for Python
- Use ESLint for JavaScript
- Add comments for complex logic
- Write descriptive commit messages

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Your Name**
- GitHub: [@Imbalance983](https://github.com/Imbalance983)

## 🙏 Acknowledgments

- [Bybit API](https://bybit-exchange.github.io/docs/v5/intro) for trading data
- [Chart.js](https://www.chartjs.org/) for beautiful charts
- [FullCalendar](https://fullcalendar.io/) for calendar functionality
- [Flask](https://flask.palletsprojects.com/) for the amazing web framework

## 📊 Project Statistics

- **Lines of Code:** ~3,500+ (Python + JavaScript + HTML/CSS)
- **Database Tables:** 6
- **API Endpoints:** 25+
- **Features:** 15+ major features
- **Status:** Production Ready ✅

## 🔮 Future Enhancements

- [ ] Multi-exchange support (Binance, OKX)
- [ ] Advanced charting with TradingView
- [ ] Strategy backtesting
- [ ] Mobile app (React Native)
- [ ] AI-powered trade analysis
- [ ] Risk management alerts
- [ ] Export to Excel/CSV
- [ ] Dark/Light theme toggle
- [ ] Multi-language support

---

<div align="center">

**⭐ If you find this project useful, please consider giving it a star! ⭐**

Made with ❤️ by a trader, for traders

</div>
