# day3_pandas_analysis.py
# DAY 3: Pandas Data Analysis on Trading Database

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import sqlite3

print("📊 DAY 3: Pandas Trading Analysis Started!")
print("=" * 60)


class TradeAnalyzer:
    """Analyzes trading data using Pandas"""

    def __init__(self, db_path="trading_journal.db"):
        self.db_path = db_path
        self.df = None
        self.load_data()
        print(f"✅ Loaded {len(self.df)} trades from database")

    def load_data(self):
        """Load trades from SQLite database into Pandas DataFrame"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT * FROM trades ORDER BY entry_time"
            self.df = pd.read_sql_query(query, conn)

            if 'entry_time' in self.df.columns:
                self.df['entry_time'] = pd.to_datetime(self.df['entry_time'])

            conn.close()

            if self.df.empty:
                print("⚠️  No trades found in database")
            else:
                print(f"📈 Data loaded: {len(self.df)} trades")

        except Exception as e:
            print(f"❌ Error loading data: {e}")
            self.df = pd.DataFrame()

    def calculate_basic_stats(self):
        """Calculate basic trading statistics"""
        if self.df.empty:
            return {"error": "No data available"}

        print("\n" + "=" * 50)
        print("📊 BASIC TRADING STATISTICS")
        print("=" * 50)

        stats = {
            'total_trades': len(self.df),
            'winning_trades': len(self.df[self.df['pnl'] > 0]),
            'losing_trades': len(self.df[self.df['pnl'] < 0]),
            'total_pnl': self.df['pnl'].sum(),
            'avg_pnl': self.df['pnl'].mean(),
            'best_trade': self.df['pnl'].max(),
            'worst_trade': self.df['pnl'].min(),
        }

        if stats['total_trades'] > 0:
            stats['win_rate'] = (stats['winning_trades'] / stats['total_trades']) * 100
        else:
            stats['win_rate'] = 0

        print(f"Total Trades: {stats['total_trades']}")
        print(f"Win Rate: {stats['win_rate']:.1f}%")
        print(f"Total P&L: ${stats['total_pnl']:.2f}")
        print(f"Average P&L: ${stats['avg_pnl']:.2f}")
        print(f"Best Trade: ${stats['best_trade']:.2f}")
        print(f"Worst Trade: ${stats['worst_trade']:.2f}")

        return stats

    def analyze_by_symbol(self):
        """Analyze performance by trading symbol"""
        if self.df.empty:
            print("No data to analyze")
            return

        print("\n" + "=" * 50)
        print("📈 PERFORMANCE BY SYMBOL")
        print("=" * 50)

        symbol_stats = self.df.groupby('symbol').agg({
            'pnl': ['count', 'sum', 'mean']
        }).round(2)

        symbol_stats.columns = ['trades', 'total_pnl', 'avg_pnl']
        symbol_stats = symbol_stats.sort_values('total_pnl', ascending=False)

        print(symbol_stats)
        return symbol_stats

    def create_simple_chart(self):
        """Create a simple P&L chart"""
        if self.df.empty:
            print("No data for chart")
            return

        plt.figure(figsize=(10, 5))

        # Cumulative P&L
        self.df = self.df.sort_values('entry_time')
        self.df['cumulative_pnl'] = self.df['pnl'].cumsum()

        plt.plot(self.df['entry_time'], self.df['cumulative_pnl'],
                 color='blue', linewidth=2)
        plt.title('Cumulative P&L Over Time')
        plt.xlabel('Date')
        plt.ylabel('Cumulative P&L ($)')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        plt.savefig('simple_pnl_chart.png', dpi=100)
        plt.show()
        print("💾 Saved chart as 'simple_pnl_chart.png'")


def main():
    """Test the Pandas analysis system"""
    print("\n🧪 TESTING PANDAS TRADING ANALYSIS")
    print("=" * 50)

    analyzer = TradeAnalyzer("trading_journal.db")

    print("\n1. Basic statistics:")
    analyzer.calculate_basic_stats()

    print("\n2. Symbol analysis:")
    analyzer.analyze_by_symbol()

    print("\n3. Creating chart...")
    analyzer.create_simple_chart()

    print("\n" + "=" * 50)
    print("✅ DAY 3 COMPLETE!")
    print("=" * 50)


if __name__ == "__main__":
    main()

