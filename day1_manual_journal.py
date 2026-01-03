import json
from datetime import datetime

print("Day 1: Manual Trading Journal Started!")
print("=" * 50)

class Trade:
    def __init__(self, symbol, side, entry_price, exit_price, quantity):
        self.symbol = symbol
        self.side = side
        self.entry_price = float(entry_price)
        self.exit_price = float(exit_price)
        self.quantity = float(quantity)
        self.entry_time = datetime.now()

        print(f"Created trade : {symbol} {side} {quantity} units")

    def calculate_pnl(self):
        if self.side == 'buy':
            # For buy trades: (sell - buy) × quantity
            profit = (self.exit_price - self.entry_price) * self.quantity
        else:
            # For sell trades: (sell - buy) × quantity (reversed)
            profit = (self.entry_price - self.exit_price) * self.quantity

        return profit

    def to_dict(self):
        return {
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "quantity": self.quantity,
            "pml" : self.calculate_pnl(),
            "entry_time" : self.entry_time.strftime("%Y-%m-%d %H:%M:%S")
        }


# Step 3: Create a Trading Journal to manage multiple trades
class TradingJournal:
    # Initialize with empty list of trades
    def __init__(self):
        self.trades = []  # Empty list to store trades
        print("📒 Trading Journal created (0 trades)")

    # Add a trade to the journal
    def add_trade(self, trade):
        self.trades.append(trade)  # Add to end of list
        print(f"➕ Added trade to journal. Total: {len(self.trades)} trades")

    # Save all trades to a JSON file
    def save_to_file(self, filename='trades.json'):
        # Convert all trades to dictionaries
        trade_data = [trade.to_dict() for trade in self.trades]

        # Open file and save JSON data
        with open(filename, 'w') as file:
            json.dump(trade_data, file, indent=2)  # indent=2 makes it pretty

        print(f"💾 Saved {len(self.trades)} trades to '{filename}'")

    # Load trades from a JSON file
    def load_from_file(self, filename='trades.json'):
        try:
            # Try to open and read the file
            with open(filename, 'r') as file:
                data = json.load(file)  # Load JSON data

            # Convert dictionaries back to Trade objects
            self.trades = []
            for trade_dict in data:
                # Create Trade object from dictionary
                trade = Trade(
                    symbol=trade_dict['symbol'],
                    side=trade_dict['side'],
                    entry_price=trade_dict['entry_price'],
                    exit_price=trade_dict['exit_price'],
                    quantity=trade_dict['quantity']
                )
                self.trades.append(trade)

            print(f"📂 Loaded {len(self.trades)} trades from '{filename}'")

        except FileNotFoundError:
            # If file doesn't exist, start fresh
            print("⚠️  No existing journal found. Starting fresh.")


if __name__ == "__main__":
    print("\n🧪 Testing the trading journal...")
    print("-" * 40)

    my_journal = TradingJournal()

    print("\n1. Creating test trades...")
    trade1 = Trade("BTCUSD", "buy", 50000, 51000, 0.1)
    trade2 = Trade("ETHUSD", "sell", 3000, 2900, 2)

    my_journal.add_trade(trade1)
    my_journal.add_trade(trade2)

    print(f"\n2. Profit/Loss Calculations:")
    print(f"   BTCUSD trade: ${trade1.calculate_pnl():.2f}")
    print(f"   ETHUSD trade: ${trade2.calculate_pnl():.2f}")

    print(f"\n3. Saving to file...")
    my_journal.save_to_file()

    print(f"\n4. Testing file loading...")
    new_journal = TradingJournal()
    new_journal.load_from_file()

    print("\n✅ Day 1 Complete! Ready for Day 2.")
    print("=" * 50)








