# check_db.py
import sqlite3
import pandas as pd

print("🔍 Checking database contents...")
conn = sqlite3.connect('data/trading_journal.db')

# Show all tables
df_tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
print("📊 Tables in database:")
print(df_tables)

# Show trades table structure
df_schema = pd.read_sql_query("PRAGMA table_info(trades)", conn)
print("\n📋 trades table structure:")
print(df_schema)

# Show all data
df_trades = pd.read_sql_query("SELECT * FROM trades", conn)
print(f"\n📈 Total trades: {len(df_trades)}")
print(df_trades)

conn.close()