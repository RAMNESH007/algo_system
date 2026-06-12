# strategies/mean_reversion.py
import pandas as pd

def mean_reversion_signal(df):
    df = df.copy()
    if 'close' not in df.columns:
        df.columns = [c.lower() for c in df.columns]

    # Bollinger Bands
    df['sma'] = df['close'].rolling(20).mean()
    df['std'] = df['close'].rolling(20).std()
    df['upper'] = df['sma'] + (2 * df['std'])
    df['lower'] = df['sma'] - (2 * df['std'])

    # RSI
    delta = df['close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = delta.clip(upper=0).abs().rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    last = df.iloc[-1]

    # BUY — oversold
    if last['close'] <= last['lower'] and last['rsi'] < 35:
        return "BUY"
    # SHORT — overbought
    elif last['close'] >= last['upper'] and last['rsi'] > 65:
        return "SHORT"
    # SELL — back to mean from below
    elif last['close'] >= last['sma'] and last['rsi'] > 55:
        return "SELL"
    # COVER — back to mean from above
    elif last['close'] <= last['sma'] and last['rsi'] < 45:
        return "COVER"
    else:
        return "HOLD"