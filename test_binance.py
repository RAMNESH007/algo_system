from config import BINANCE_API_KEY, BINANCE_SECRET
from brokers.binance_broker import BinanceBroker

binance = BinanceBroker(BINANCE_API_KEY, BINANCE_SECRET)

# Check balance
balance = binance.get_balance('USDT')
print(f"💰 USDT Balance: ${balance}")

# Get BTC data
data = binance.get_data('BTCUSDT')
print(data.tail())