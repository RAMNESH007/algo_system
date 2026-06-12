# brokers/zerodha.py
from kiteconnect import KiteConnect
import pandas as pd
from datetime import datetime, timedelta

class ZerodhaBroker:
    def __init__(self, api_key, api_secret, access_token=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.kite = KiteConnect(api_key=api_key)
        if access_token:
            self.kite.set_access_token(access_token)

    def get_login_url(self):
        return self.kite.login_url()

    def generate_access_token(self, request_token):
        try:
            data = self.kite.generate_session(
                request_token,
                api_secret=self.api_secret
            )
            return data["access_token"]
        except Exception as e:
            print(f"❌ Token error: {e}")
            return None

    def get_balance(self):
        try:
            margins = self.kite.margins()
            return float(margins['equity']['available']['live_balance'])
        except Exception as e:
            print(f"❌ Balance error: {e}")
            return 0.0

    def get_data(self, symbol, interval='minute', days=2):
        try:
            instruments = self.kite.instruments('NSE')
            df_inst = pd.DataFrame(instruments)
            token = df_inst[
                df_inst['tradingsymbol'] == symbol
            ]['instrument_token'].values[0]
            end = datetime.now()
            start = end - timedelta(days=days)
            data = self.kite.historical_data(
                token, start, end, interval
            )
            df = pd.DataFrame(data)
            return df
        except Exception as e:
            print(f"❌ Data error: {e}")
            return None

    def place_order(self, symbol, qty, side):
        try:
            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=self.kite.EXCHANGE_NSE,
                tradingsymbol=symbol,
                transaction_type=(
                    self.kite.TRANSACTION_TYPE_BUY
                    if side == 'buy'
                    else self.kite.TRANSACTION_TYPE_SELL
                ),
                quantity=qty,
                product=self.kite.PRODUCT_MIS,
                order_type=self.kite.ORDER_TYPE_MARKET
            )
            print(f"✅ Zerodha MIS: {side} {qty} {symbol}")
            return order_id
        except Exception as e:
            print(f"❌ Order failed: {e}")

    def close_position(self, symbol, qty):
        try:
            self.place_order(symbol, qty, 'sell')
            print(f"📤 Closed: {symbol}")
        except Exception as e:
            print(f"❌ Close failed: {e}")

    def get_positions(self):
        try:
            return self.kite.positions()['day']
        except Exception as e:
            print(f"❌ Positions error: {e}")
            return []

    def get_orders(self):
        try:
            return self.kite.orders()
        except Exception as e:
            print(f"❌ Orders error: {e}")
            return []