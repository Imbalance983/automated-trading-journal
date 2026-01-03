# day3_pandas_analysis.py
# DAY 3: Pandas Data Analysis on Trading Database

import pandas as pd
import matplotlib.pyplot as plt
import sqlite3

print("📊 DAY 3: Pandas Trading Analysis Started!")
print("=" * 60)


class TradeAnalyzer:
    def __init__(self, db_path="trading_journal.db"):
        self.db_path = db_path
        self.df = None
        self.load_data()

    def load_data(self):
        try:
            conn = sqlite3.connect(self.db_path)
            query = "SELECT * FROM trades ORDER BY entry_time"
            self.df = pd.read_sql_query(query, conn)
            conn.close()
            print(f"✅ Loaded {len(self.df)} trades from database")
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            self.df = pd.DataFrame()

    def calculate_basic_stats(self):
        if self.df.empty:
            return

        print("\n" + "=" * 50)
        print("📊 BASIC TRADING STATISTICS")
        print("=" * 50)

        total = len(self.df)
        wins = len(self.df[self.df['pnl'] > 0])
        total_pnl = self.df['pnl'].sum()

        print(f"Total Trades: {total}")
        print(f"Win Rate: {(wins / total) * 100:.1f}%")
        print(f"Total P&L: ${total_pnl:.2f}")
        print(f"Average P&L: ${self.df['pnl'].mean():.2f}")
        print(f"Best Trade: ${self.df['pnl'].max():.2f}")
        print(f"Worst Trade: ${self.df['pnl'].min():.2f}")

    def analyze_by_symbol(self):
        if self.df.empty:
            return

        print("\n" + "=" * 50)
        print("📈 PERFORMANCE BY SYMBOL")
        print("=" * 50)

        stats = self.df.groupby('symbol').agg({
            'pnl': ['count', 'sum', 'mean']
        }).round(2)
        stats.columns = ['trades', 'total_pnl', 'avg_pnl']
        print(stats)

    def create_simple_chart(self):
        if self.df.empty:
            return

        try:
            plt.figure(figsize=(10, 5))
            self.df = self.df.sort_values('entry_time')
            self.df['cumulative_pnl'] = self.df['pnl'].cumsum()

            plt.plot(range(1, len(self.df) + 1), self.df['cumulative_pnl'],
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