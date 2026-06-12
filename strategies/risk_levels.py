# strategies/risk_levels.py
from config import STOP_LOSS_PCT, TAKE_PROFIT_PCT

def check_stop_loss(entry_price, current_price, is_short=False):
    if is_short:
        return current_price >= entry_price * (1 + STOP_LOSS_PCT)
    else:
        return current_price <= entry_price * (1 - STOP_LOSS_PCT)

def check_take_profit(entry_price, current_price, is_short=False):
    if is_short:
        return current_price <= entry_price * (1 - TAKE_PROFIT_PCT)
    else:
        return current_price >= entry_price * (1 + TAKE_PROFIT_PCT)

def calculate_pnl(entry_price, exit_price, quantity, is_short=False):
    if is_short:
        return (entry_price - exit_price) * quantity
    else:
        return (exit_price - entry_price) * quantity