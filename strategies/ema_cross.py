# strategies/ema_cross.py
import pandas as pd

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = delta.clip(upper=0).abs().rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def compute_macd(series):
    ema12 = series.ewm(span=12).mean()
    ema26 = series.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    return macd, signal

def ema_signal(df):
    df = df.copy()
    if 'close' not in df.columns:
        df.columns = [c.lower() for c in df.columns]

    # Indicators
    df['ema_fast'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=21, adjust=False).mean()
    df['rsi'] = compute_rsi(df['close'], 14)
    df['macd'], df['macd_signal'] = compute_macd(df['close'])
    df['volume_ma'] = df['volume'].rolling(20).mean()

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Crossover detection
    ema_cross_up = (prev['ema_fast'] <= prev['ema_slow'] and
                    last['ema_fast'] > last['ema_slow'])
    ema_cross_down = (prev['ema_fast'] >= prev['ema_slow'] and
                      last['ema_fast'] < last['ema_slow'])

    # MACD confirmation
    macd_bull = last['macd'] > last['macd_signal']
    macd_bear = last['macd'] < last['macd_signal']

    # RSI filters
    rsi_buy_ok = last['rsi'] < 75
    rsi_sell_ok = last['rsi'] > 25
    rsi_overbought = last['rsi'] > 80
    rsi_oversold = last['rsi'] < 20

    # BUY — long signal
    if ema_cross_up and rsi_buy_ok and macd_bull:
        return "BUY"

    # SHORT — short sell signal
    elif ema_cross_down and rsi_sell_ok and macd_bear:
        return "SHORT"

    # SELL — close long
    elif ema_cross_down or rsi_overbought:
        return "SELL"

    # COVER — close short
    elif ema_cross_up or rsi_oversold:
        return "COVER"

    else:
        return "HOLD"