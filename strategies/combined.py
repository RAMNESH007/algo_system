# strategies/combined.py
from strategies.ema_cross import ema_signal
from strategies.mean_reversion import mean_reversion_signal
from strategies.momentum import momentum_signal

def get_combined_signal(df):
    try:
        ema = ema_signal(df)
        mr = mean_reversion_signal(df)
        mom = momentum_signal(df)

        signals = [ema, mr, mom]
        print(f"  EMA: {ema} | MR: {mr} | MOM: {mom}")

        buy_count = signals.count("BUY")
        short_count = signals.count("SHORT")
        sell_count = signals.count("SELL")
        cover_count = signals.count("COVER")

        # Need 2/3 agreement
        if buy_count >= 2:
            return "BUY"
        elif short_count >= 2:
            return "SHORT"
        elif sell_count >= 2:
            return "SELL"
        elif cover_count >= 2:
            return "COVER"
        else:
            return "HOLD"

    except Exception as e:
        print(f"❌ Combined signal error: {e}")
        return "HOLD"