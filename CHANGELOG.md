# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-09

### 🎉 Initial Release - Production Ready

### Added
- **Bybit API Integration**
  - Real-time trade synchronization
  - Account balance tracking (USDT equity)
  - Position and open order monitoring
  - Secure credential storage with SQLite
  - Connection persistence across sessions

- **Position Size Calculator**
  - Double-width card for better UX
  - Risk-based position sizing
  - Support for USDT or percentage risk
  - Real-time calculation updates
  - Responsive input fields (120px width)

- **Advanced Analytics Dashboard**
  - Total P&L tracking
  - Win rate with visual chart
  - Profit factor and expectancy metrics
  - Average win/loss analysis
  - Risk/reward ratio tracking
  - Max drawdown calculation
  - Win/loss streak monitoring

- **Calendar View**
  - Interactive FullCalendar integration
  - Daily P&L visualization
  - Color-coded performance days
  - Trade count per day
  - Win rate statistics
  - Quick access to daily trades

- **Time Analytics**
  - Performance by hour of day
  - Performance by day of week
  - Heatmap visualizations
  - Identify optimal trading times

- **Trade Management**
  - Manual trade entry form
  - Screenshot upload support
  - Trade editing and deletion
  - Strategy metadata (model, bias, confirmations)
  - Bulk trade import from Bybit

- **Multi-User Support**
  - User creation and switching
  - Per-user trade isolation
  - Per-user API credentials

- **Database Schema**
  - Users table
  - Trades table with full metadata
  - API credentials table
  - Account balances history
  - Positions tracking
  - Open orders tracking

### Fixed
- JavaScript syntax errors in render functions
- Function ordering issues (renderConnected/renderDisconnected)
- Null-safety checks on all DOM elements
- Balance endpoint returning 500 instead of 200
- Loading state timeout fail-safe (5 seconds)
- USDT equity calculation (now shows correct ~$395 instead of $199k)

### Security
- Encrypted API credential storage
- Session management
- CORS configuration
- SQL injection prevention with parameterized queries

### Performance
- Async data fetching
- Optimized database queries
- Client-side caching
- Efficient grid layouts with CSS Grid

## [0.9.0] - 2026-01-09

### Changed
- Balance calculation switched from all-coin equity to USDT-only equity
- Position calculator UI improved (double-width, larger inputs)
- Render functions moved before DOMContentLoaded (fix undefined errors)

### Fixed
- Loading state stuck bug
- Missing clearLoading() calls in all code paths
- showConnectedState function undefined error

## [0.8.0] - 2026-01-09

### Added
- 5-second timeout fail-safe for loading state
- Comprehensive null-safety checks
- Enhanced error logging in console

### Fixed
- Multiple JavaScript syntax errors
- Missing loadRiskMetrics() function
- Incomplete fetchAccountBalance() function
- Duplicate variable declarations

## [0.7.0] - 2026-01-08

### Added
- Bybit Unified Trading Account support
- Extended data sync (balances, positions, orders)
- Account balance snapshot history

### Fixed
- API credential persistence
- Network selection (mainnet/testnet)

---

## Upcoming Features

### [1.1.0] - Planned
- [ ] Multi-exchange support (Binance, OKX)
- [ ] Advanced charting with TradingView
- [ ] Export to Excel/CSV
- [ ] Dark/Light theme toggle
- [ ] Mobile app (React Native)

### [1.2.0] - Planned
- [ ] Strategy backtesting
- [ ] AI-powered trade analysis
- [ ] Risk management alerts
- [ ] Multi-language support
- [ ] Telegram notifications

### [2.0.0] - Future
- [ ] Social trading features
- [ ] Copy trading integration
- [ ] Advanced portfolio analytics
- [ ] Paper trading mode

---

## Release Notes

### Version 1.0.0 Highlights

This is the first production-ready release of Automated Trading Journal. The application is fully functional with:

✅ **Zero known bugs**
✅ **Clean F12 console** (no errors)
✅ **Persistent connections** (survives refresh/restart)
✅ **Accurate balance** (USDT equity)
✅ **Professional UI/UX**
✅ **Comprehensive documentation**

The system has been thoroughly tested and is ready for daily use by cryptocurrency traders.

---

[1.0.0]: https://github.com/Imbalance983/automated-trading-journal/releases/tag/v1.0.0
[0.9.0]: https://github.com/Imbalance983/automated-trading-journal/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/Imbalance983/automated-trading-journal/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/Imbalance983/automated-trading-journal/releases/tag/v0.7.0
