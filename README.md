# ImbLedger - Professional Trading Journal & Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-F7DF1E?style=flat&logo=javascript&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> A full-stack web application for cryptocurrency traders to track, analyze, and optimize their trading performance with real-time exchange integration and advanced analytics.

![ImbLedger Dashboard](https://via.placeholder.com/800x400?text=ImbLedger+Dashboard)

## 🎯 Project Overview

**ImbLedger** is a comprehensive trading journal and analytics platform built to solve the challenge of tracking and analyzing cryptocurrency trades across multiple exchanges. The application provides traders with professional-grade tools for performance analysis, risk management, and strategy optimization.

**Built with:** Python, Flask, SQLite, JavaScript, Chart.js, FullCalendar.js

## ✨ Key Features

### 📊 Advanced Performance Analytics
- **GitHub-style Performance Heatmaps** - Visualize trading patterns by hour and day of week with intensity-based color coding
- **Real-time Metrics Dashboard** - 18 key performance indicators organized into Account Overview, Win/Loss Analysis, and Risk & Strategy sections
- **Dynamic P&L Chart** - Interactive cumulative profit/loss visualization with period filters (All Time, Month, Week, Today, Custom)
- **Win Rate Arch Visualization** - Centered, visually appealing semi-circular gauge for quick performance assessment

### 🔄 Exchange Integration (Bybit V5 API)
- **Automated Trade Import** - Real-time synchronization with Bybit exchange (mainnet/testnet)
- **90-Day Rolling Sync** - Automatic historical trade fetching with 6-day chunking for API rate limit optimization
- **Duplicate Prevention** - UNIQUE constraint enforcement with external_id tracking
- **Multi-contract Support** - Handles USDT linear and inverse perpetual contracts
- **Secure Credential Storage** - Local-only API key storage with session-based authentication

### 📅 Interactive Calendar System
- **FullCalendar Integration** - Monthly view with trade density visualization
- **Moon Phase Tracking** - Full/New moon indicators for correlation analysis (Dublin Time UTC+0/+1)
- **Day-level Metrics** - Trade count, P&L, and win rate displayed on each calendar day
- **Smart Color Coding** - P&L-based text coloring without intrusive background highlights
- **Direct DOM Manipulation** - Efficient updates without calendar re-initialization to preserve navigation

### 👥 Multi-User Architecture
- **Session-based User Switching** - Dropdown-based user selection for quick account changes
- **User-isolated Data** - Database-level separation via `user_id` foreign keys
- **Dynamic User Creation** - Add new trading accounts on-the-fly
- **API Independence** - User data persists regardless of API credential changes

### 💼 Trade Management
- **Comprehensive Trade Entry** - Capture entry/exit prices, quantity, timestamps, stop-loss, take-profit, R:R ratios
- **Performance Categorization** - Track by Key Level (Support/Resistance), Confirmation method, and Trading Model
- **Market Bias Tracking** - Record Weekly and Daily bias (Bullish/Bearish/Neutral) for context
- **Rich Notes & Screenshots** - Detailed trade journals with image URL support
- **Open Position Tracking** - Separate view for active trades vs. closed trades

## 🛠️ Technical Stack

### Backend
- **Flask 2.3.3** - Lightweight web framework with RESTful API design
- **SQLite** - Embedded relational database with migration system
- **Python 3.8+** - Core application logic and API integrations
- **Bybit V5 API** - Exchange data integration with HMAC-SHA256 authentication

### Frontend
- **Vanilla JavaScript (ES6+)** - No framework dependencies, direct DOM manipulation
- **Chart.js** - Data visualization for P&L charts and win rate gauges
- **FullCalendar.js 6.1.8** - Professional calendar UI with custom rendering
- **Responsive CSS Grid/Flexbox** - Modern layout system with 2:1 ratio optimization

### Database Schema
```sql
-- Users table for multi-account support
users (id, username, created_at)

-- Trades table with comprehensive tracking
trades (
  id, user_id, asset, side, entry_price, exit_price, quantity,
  pnl, pnl_percentage, entry_time, exit_time, notes, screenshot,
  key_level, confirmation, model, weekly_bias, daily_bias,
  stop_loss, take_profit, risk_reward_ratio, position_size_pct,
  external_id [UNIQUE], created_at
)

-- API credentials with secure storage
api_credentials (
  id, user_id, exchange, api_key, api_secret, network, remember_me
)
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git

### Quick Start

```bash
# Clone the repository
git clone https://github.com/Imbalance983/automated-trading-journal.git
cd automated-trading-journal

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py

# Access the application
# Open http://127.0.0.1:5000 in your browser
```

### Environment Configuration (Optional)

```bash
# Create .env file for custom settings
FLASK_SECRET_KEY=your_secret_key_here
DEBUG=False
PORT=5000
```

## 📁 Project Structure

```
ImbLedger/
├── app.py                      # Flask application & API endpoints
├── templates/
│   └── single_page.html        # Complete SPA frontend
├── trading_journal.db          # SQLite database (auto-created)
├── requirements.txt            # Python dependencies
├── .gitignore                 # Git exclusions (*.db, *.zip, .env)
└── README.md                  # Project documentation
```

## 💡 Usage Guide

### 1. Manual Trade Entry
1. Click **"Add Trade"** button
2. Fill in trade details (asset, side, prices, quantity, timestamps)
3. Add analysis categories (Key Level, Confirmation, Model)
4. Set biases (Weekly/Daily)
5. Optional: Add screenshot URL and notes
6. Click **"Save Trade"**

### 2. Bybit Integration
1. Generate API keys from [Bybit API Management](https://www.bybit.com/app/user/api-management)
   - Enable **Read** permissions
   - Set IP restrictions for security
2. Enter API Key and Secret in the API section
3. Select network (Mainnet for live trading)
4. Click **"Save"** to store credentials
5. Click **"Sync"** to import trades (fetches last 90 days)

### 3. Performance Analysis
- **Metrics Dashboard** - View 18 key statistics organized by category
- **P&L Chart** - Switch between time periods (All Time, Month, Week, Today, Custom)
- **Heatmaps** - Analyze performance by hour (0-23 UTC) and day of week (Mon-Sun)
- **Calendar** - Click any day to view detailed trades
- **Best Performers** - Track top Key Levels, Models, and Confirmations

## 🎨 UI/UX Design Highlights

- **Dark Theme** - Optimized for extended trading sessions with reduced eye strain
- **GitHub-inspired Heatmaps** - Familiar visualization pattern for pattern recognition
- **Centered Win Rate Arch** - Prominent placement of critical performance metric
- **Compact Period Filters** - Small, unobtrusive buttons (padding: 4px 10px, font-size: 0.75em)
- **2:1 Layout Ratio** - PNL chart (66% width) + Time Analytics (33% width) for optimal information density
- **Responsive Grid System** - 6-column metrics dashboard (repeat(6, 1fr)) for consistent spacing

## 🔧 Technical Achievements

### Database Optimization
- **Migration System** - Automatic schema updates with try/except ALTER TABLE blocks
- **Indexed Queries** - External_id UNIQUE constraint for O(1) duplicate detection
- **User-scoped Queries** - All data access filtered by session user_id

### API Integration Challenges
- **Rate Limit Handling** - 6-day chunking strategy for 90-day historical sync
- **Time Range Management** - Unix millisecond timestamp conversion with proper UTC handling
- **Error Recovery** - Comprehensive try/except with detailed logging to sync_debug.txt
- **Data Normalization** - Bybit response mapping to internal schema (avgEntryPrice → entry_price)

### Frontend Performance
- **Minimal Re-renders** - Direct DOM manipulation instead of framework virtual DOM
- **Event Delegation** - Efficient click handling for dynamic trade cards
- **Lazy Loading** - Calendar data fetched on-demand, not on initial page load
- **CSS-only Animations** - Smooth transitions without JavaScript overhead

## 📊 Analytics & Insights

The platform calculates and displays:

- **Win Rate** - Percentage of profitable trades
- **Profit Factor** - Ratio of gross profit to gross loss
- **Expectancy** - Average expected return per trade
- **Average R:R Ratio** - Mean risk-reward across all trades
- **Max Drawdown** - Largest peak-to-trough decline
- **Streaks** - Longest consecutive win/loss sequences
- **Hold Period** - Average trade duration
- **Best Performers** - Top Key Level, Model, and Confirmation by P&L

## 🔐 Security Considerations

- ✅ **Local-only Data** - No external servers, all data stored on localhost
- ✅ **API Key Encryption** - Credentials never exposed in client-side code
- ✅ **Session-based Auth** - Server-side user tracking via Flask sessions
- ✅ **.gitignore Protection** - Database and API configs excluded from version control
- ⚠️ **Production Recommendations**:
  - Use environment variables for sensitive data
  - Implement HTTPS with SSL certificates
  - Add rate limiting to API endpoints
  - Enable CORS protection for production deployment

## 🚀 Future Enhancements

- [ ] Export to CSV/Excel functionality
- [ ] Multi-exchange support (Binance, OKX, etc.)
- [ ] Email/password authentication system
- [ ] Cloud database integration (PostgreSQL)
- [ ] Mobile app (React Native)
- [ ] Strategy backtesting engine
- [ ] Real-time WebSocket price feeds
- [ ] Risk management alerts (daily loss limits, position sizing)

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**This software is for educational and informational purposes only.**

- Not financial advice
- Past performance ≠ future results
- Trading involves risk of loss
- Never trade with money you cannot afford to lose
- Always do your own research (DYOR)

## 🙏 Acknowledgments

- **Flask** - Web framework by Pallets
- **Chart.js** - Open-source charting library
- **FullCalendar** - Premium calendar component
- **Bybit** - V5 API documentation and support
- **SQLite** - Public domain database engine

## 📞 Contact & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/Imbalance983/automated-trading-journal/issues)
- **Email**: Available upon request
- **Documentation**: This README and inline code comments

---

**Built with ❤️ for traders, by traders.**

*Last Updated: January 2026*
