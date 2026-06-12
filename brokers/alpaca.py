# brokers/alpaca.py
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from datetime import datetime, timedelta
import pandas as pd

class AlpacaBroker:
    def __init__(self, api_key, secret, base_url=None):
        self.trading = TradingClient(api_key, secret, paper=True)
        self.data = StockHistoricalDataClient(api_key, secret)

    def get_balance(self):
        account = self.trading.get_account()
        return float(account.cash)

    def get_data(self, symbol, limit=100):
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Minute,
            start=datetime.now() - timedelta(hours=3),
            limit=limit
        )
        bars = self.data.get_stock_bars(request)
        df = bars.df.reset_index()
        return df

    def get_all_positions(self):
        return self.trading.get_all_positions()

    def place_order(self, symbol, qty, side):
        try:
            order = self.trading.submit_order(
                MarketOrderRequest(
                    symbol=symbol,
                    qty=qty,
                    side=OrderSide.BUY if side == 'buy' else OrderSide.SELL,
                    time_in_force=TimeInForce.GTC
                )
            )
            print(f"✅ Order: {side} {qty} {symbol}")
            return order
        except Exception as e:
            print(f"❌ Order failed: {e}")

    def close_position(self, symbol):
        try:
            self.trading.close_position(symbol)
            print(f"📤 Position closed: {symbol}")
        except Exception as e:
            print(f"❌ Close failed: {e}")