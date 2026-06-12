# monitor.py
import time
from brokers.binance_broker import BinanceBroker
from config import BINANCE_API_KEY, BINANCE_SECRET

binance = BinanceBroker(BINANCE_API_KEY, BINANCE_SECRET)

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = delta.clip(upper=0).abs().rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

while True:
    df = binance.get_data('BTCUSDT', interval='1m', limit=100)
    df['ema_fast'] = df['close'].ewm(span=9).mean()
    df['ema_slow'] = df['close'].ewm(span=21).mean()
    df['rsi'] = compute_rsi(df['close'])
    df['volume_ma'] = df['volume'].rolling(20).mean()

    last = df.iloc[-1]
    prev = df.iloc[-2]

    cross = "🔴 NO" if last['ema_fast'] < last['ema_slow'] else "🟢 YES"
    rsi_ok = "✅" if 30 < last['rsi'] < 70 else "❌"
    vol_ok = "✅" if last['volume'] > last['volume_ma'] else "❌"

    print(f"\n{'─'*40}")
    print(f"BTC Price : ${last['close']:.2f}")
    print(f"EMA Fast  : {last['ema_fast']:.2f}")
    print(f"EMA Slow  : {last['ema_slow']:.2f}")
    print(f"Cross Up  : {cross}")
    print(f"RSI       : {last['rsi']:.1f} {rsi_ok}")
    print(f"Volume OK : {vol_ok}")
    print(f"{'─'*40}")

    time.sleep(60)