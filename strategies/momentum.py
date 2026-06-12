# strategies/momentum.py
import pandas as pd

def momentum_signal(df):
    df = df.copy()
    if 'close' not in df.columns:
        df.columns = [c.lower() for c in df.columns]

    # MACD
    df['ema12'] = df['close'].ewm(span=12).mean()
    df['ema26'] = df['close'].ewm(span=26).mean()
    df['macd'] = df['ema12'] - df['ema26']
    df['signal'] = df['macd'].ewm(span=9).mean()
    df['histogram'] = df['macd'] - df['signal']

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # BUY — MACD crosses above signal
    if (prev['macd'] <= prev['signal'] and
            last['macd'] > last['signal'] and
            last['histogram'] > 0):
        return "BUY"

    # SHORT — MACD crosses below signal
    elif (prev['macd'] >= prev['signal'] and
          last['macd'] < last['signal'] and
          last['histogram'] < 0):
        return "SHORT"

    # SELL
    elif last['macd'] < last['signal'] and last['histogram'] < 0:
        return "SELL"

    # COVER
    elif last['macd'] > last['signal'] and last['histogram'] > 0:
        return "COVER"

    else:
        return "HOLD"