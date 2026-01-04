# Automated Trading Journal

## Progress

### Day 1: Manual Journal
- File: day1_manual_journal.py
- Trade class with JSON save/load

### Day 2: SQLite Database
- File: day2_sqlite_journal.py
- SQLite CRUD operations

### Day 3: Pandas Analysis
- File: day3_pandas_analysis.py
- Data analysis and charts

### Day 4: Bybit API
- File: day4_test.py
- Bybit Testnet API connection
- Security: .env excluded

### Day 5: Database Integration [COMPLETE]
**Files created:**
- database/trade_db.py
- utils/bybit_client.py
- utils/data_fetcher.py
- day5_final_working.py

**Accomplished:**
- Connected Bybit API to SQLite database
- Automatic trade fetching and saving
- 10+ trades saved to database
- Total volume: ,070.90
- Ready for Day 6 dashboard

### Day 6: Streamlit Dashboard [COMPLETE]
**File:** day6_basic_dashboard.py

**Features:**
- ✅ **Metrics Display**: Total P&L, Win Rate, Avg Win/Loss, Profit Factor
- ✅ **Filterable Trade Table**: Filter by symbol, type, status, P&L range
- ✅ **P&L Charts**: Cumulative P&L, trade distribution, symbol performance
- ✅ **Interactive Interface**: Sidebar filters, color-coded tables, tabs
- ✅ **Sample Data**: 5 sample trades with realistic crypto symbols

**How to Run:**
```bash
streamlit run day6_basic_dashboard.py
