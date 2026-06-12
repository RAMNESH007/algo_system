from config import ALPACA_API_KEY, ALPACA_SECRET, ALPACA_BASE_URL
from brokers.alpaca import AlpacaBroker

alpaca = AlpacaBroker(ALPACA_API_KEY, ALPACA_SECRET, ALPACA_BASE_URL)

# Check balance
balance = alpaca.get_balance()
print(f"💰 Paper Balance: ${balance}")

# Get market data
data = alpaca.get_data('AAPL')
print(data.tail())