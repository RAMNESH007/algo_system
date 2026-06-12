# brokers/binance_broker.py
from binance.client import Client
import pandas as pd

class BinanceBroker:
    def __init__(self, api_key, secret):
        self.client = Client(
            api_key,
            secret,
            testnet=True
        )

    def get_balance(self, asset='USDT'):
        try:
            balance = self.client.get_asset_balance(asset=asset)
            return float(balance['free'])
        except Exception as e:
            print(f"❌ Balance error: {e}")
            return 0.0

    def get_data(self, symbol='BTCUSDT', interval='1m', limit=100):
        try:
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            df = pd.DataFrame(klines, columns=[
                'time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_vol', 'trades',
                'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
            df['close'] = df['close'].astype(float)
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['volume'] = df['volume'].astype(float)
            return df
        except Exception as e:
            print(f"❌ Data error: {e}")
            return None

    def place_order(self, symbol, side, quantity):
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            print(f"✅ Crypto: {side} {quantity} {symbol}")
            return order
        except Exception as e:
            print(f"❌ Order failed: {e}")