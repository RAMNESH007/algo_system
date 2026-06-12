from config import ALPACA_API_KEY, ALPACA_SECRET, ALPACA_BASE_URL
from brokers.alpaca import AlpacaBroker
from strategies.ema_cross import ema_signal

alpaca = AlpacaBroker(ALPACA_API_KEY, ALPACA_SECRET, ALPACA_BASE_URL)

# Get data
df = alpaca.get_data('AAPL')

# Get signal
signal = ema_signal(df)
print(f"📊 Signal for AAPL: {signal}")