# brokers/market_hours.py
from datetime import datetime
import pytz

IST = pytz.timezone('Asia/Kolkata')

def is_us_open():
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return False
    h, m = now.hour, now.minute
    return (h == 19) or (20 <= h <= 23) or (h == 0 and m <= 30)

def is_india_open():
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return False
    h, m = now.hour, now.minute
    return (h == 9 and m >= 15) or (10 <= h <= 14) or (h == 15 and m <= 30)

def is_crypto_open():
    return True