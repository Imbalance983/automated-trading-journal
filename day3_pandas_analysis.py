# day3_pandas_analysis.py
# DAY 3: Pandas Data Analysis on Trading Database

import pandas as pd
<<<<<<< HEAD
import matplotlib.pyplot as plt
=======
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
>>>>>>> 0216392294e50f5a67b75e79afec4748e8586cdc
import sqlite3

print("📊 DAY 3: Pandas Trading Analysis Started!")
print("=" * 60)


class TradeAnalyzer:
<<<<<<< HEAD
=======
    """Analyzes trading data using Pandas"""

>>>>>>> 0216392294e50f5a67b75e79afec4748e8586cdc
    def __init__(self, db_path="trading_journal.db"):
        self.db_path = db_path
        self.df = None
        self.load_data()
<<<<<<< HEAD

    def load_data(self):
=======
        print(f"✅ Loaded {len(self.df)} trades from database")

    def load_data(self):
        """Load trades from SQLite database into Pandas DataFrame"""
>>>>>>> 0216392294e50f5a67b75e79afec4748e8586cdc
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT * FROM trades ORDER BY entry_time"
            self.df = pd.read_sql_query(query, conn)
<<<<<<< HEAD
            conn.close()

            if self.df.empty:
                print("❌ Error loading data: No trades found")
            else:
                print(f"✅ Loaded {len(self.df)} trades from database")
=======

            if 'entry_time' in self.df.columns:
                self.df['entry_time'] = pd.to_datetime(self.df['entry_time'])

            conn.close()

            if self.df.empty:
                print("⚠️  No trades found in database")
            else:
                print(f"📈 Data loaded: {len(self.df)} trades")

>>>>>>> 0216392294e50f5a67b75e79afec4748e8586cdc
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            self.df = pd.DataFrame()

    def calculate_basic_stats(self):
<<<<<<< HEAD
        if self.df.empty:
            print("No data available")
            return
=======
        """Calculate basic trading statistics"""
        if self.df.empty:
            return {"error": "No data available"}
>>>>>>> 0216392294e50f5a67b75e79afec4748e8586cdc

        print("\n" + "=" * 50)
        print("📊 BASIC TRADING STATISTICS")
        print("=" * 50)

<<<<<<< HEAD
        total_trades = len(self.df)
        winning_trades = len(self.df[self.df['pnl'] > 0])
        total_pnl = self.df['pnl'].sum()

        print(f"Total Trades: {total_trades}")
        print(f"Win Rate: {(winning_trades / total_trades) * 100:.1f}%")
        print(f"Total P&L: ${total_pnl:.2f}")
        print(f"Average P&L: ${self.df['pnl'].mean():.2f}")
        print(f"Best Trade: ${self.df['pnl'].max():.2f}")
        print(f"Worst Trade: ${self.df['pnl'].min():.2f}")

    def analyze_by_symbol(self):
=======
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
>>>>>>> 0216392294e50f5a67b75e79afec4748e8586cdc
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
<<<<<<< HEAD
        print(symbol_stats)

    def create_simple_chart(self):
=======
        symbol_stats = symbol_stats.sort_values('total_pnl', ascending=False)

        print(symbol_stats)
        return symbol_stats

    def create_simple_chart(self):
        """Create a simple P&L chart"""
>>>>>>> 0216392294e50f5a67b75e79afec4748e8586cdc
        if self.df.empty:
            print("No data for chart")
            return

<<<<<<< HEAD
        try:
            plt.figure(figsize=(10, 5))
            self.df = self.df.sort_values('entry_time')
            self.df['cumulative_pnl'] = self.df['pnl'].cumsum()

            trade_numbers = range(1, len(self.df) + 1)

            plt.plot(trade_numbers, self.df['cumulative_pnl'],
                     color='blue', linewidth=2, marker='o')

            plt.title('Cumulative P&L Over Trades', fontweight='bold')
            plt.xlabel('Trade Number')
            plt.ylabel('Cumulative P&L ($)')
            plt.grid(True, alpha=0.3)
            plt.axhline(y=0, color='red', linestyle='--', alpha=0.5)

            plt.tight_layout()
            plt.savefig('simple_pnl_chart.png', dpi=100)
            plt.show()
            print("💾 Saved chart as 'simple_pnl_chart.png'")

        except Exception as e:
            print(f"❌ Chart error: {e}")


def main():
=======
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
>>>>>>> 0216392294e50f5a67b75e79afec4748e8586cdc
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
<<<<<<< HEAD
    main()
=======
    main()

>>>>>>> 0216392294e50f5a67b75e79afec4748e8586cdc
