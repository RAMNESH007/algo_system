# main.py
import schedule
import time
import json
import os
from config import *
from risk.manager import RiskManager
from alerts.telegram import send_alert
from brokers.alpaca import AlpacaBroker
from brokers.binance_broker import BinanceBroker
from brokers.zerodha import ZerodhaBroker
from brokers.market_hours import is_us_open, is_india_open
from strategies.combined import get_combined_signal
from strategies.risk_levels import (check_stop_loss,
                                    check_take_profit,
                                    calculate_pnl)

# ═══════════════════════════════════════
# INITIALIZE
# ═══════════════════════════════════════
rm = RiskManager(TOTAL_CAPITAL, MAX_DRAWDOWN_PCT)
alpaca = AlpacaBroker(ALPACA_API_KEY, ALPACA_SECRET, ALPACA_BASE_URL)
binance = BinanceBroker(BINANCE_API_KEY, BINANCE_SECRET)

# Load Zerodha
def load_zerodha():
    try:
        if os.path.exists('zerodha_token.json'):
            with open('zerodha_token.json', 'r') as f:
                data = json.load(f)
            z = ZerodhaBroker(
                ZERODHA_API_KEY,
                ZERODHA_SECRET,
                data['access_token']
            )
            print("✅ Zerodha loaded!")
            return z
        else:
            print("⚠️ Run zerodha_login.py first!")
            return None
    except Exception as e:
        print(f"❌ Zerodha error: {e}")
        return None

zerodha = load_zerodha()

# Position tracking
long_positions = {}
short_positions = {}

# ═══════════════════════════════════════
# US STRATEGY
# ═══════════════════════════════════════
def run_us_strategy():
    if not rm.trading_allowed:
        print("⚠️ Trading stopped")
        return
    if not is_us_open():
        print("💤 US Market closed")
        return

    try:
        balance = alpaca.get_balance()
        print(f"💰 Alpaca: ${balance:.2f}")

        for symbol in US_SYMBOLS:
            try:
                df = alpaca.get_data(symbol)
                if df is None or len(df) < 30:
                    continue

                signal = get_combined_signal(df)
                price = df['close'].iloc[-1]
                size = int(rm.position_size() / price)
                print(f"📊 {symbol}: ${price:.2f} | {signal}")

                # Stop loss / Take profit — LONG
                if symbol in long_positions:
                    entry = long_positions[symbol]
                    if check_stop_loss(entry, price):
                        alpaca.close_position(symbol)
                        pnl = calculate_pnl(entry, price, size)
                        long_positions.pop(symbol)
                        rm.log_trade('US', 'STOP_LOSS', price, size, pnl)
                        send_alert(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                                  f"🛑 *STOP LOSS* {symbol}\n"
                                  f"💵 ${price:.2f} | 🔴 ${pnl:.2f}")
                        continue
                    if check_take_profit(entry, price):
                        alpaca.close_position(symbol)
                        pnl = calculate_pnl(entry, price, size)
                        long_positions.pop(symbol)
                        rm.log_trade('US', 'TAKE_PROFIT', price, size, pnl)
                        send_alert(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                                  f"🎯 *TAKE PROFIT* {symbol}\n"
                                  f"💵 ${price:.2f} | 🟢 ${pnl:.2f}")
                        continue

                # Stop loss / Take profit — SHORT
                if symbol in short_positions:
                    entry = short_positions[symbol]
                    if check_stop_loss(entry, price, is_short=True):
                        alpaca.place_order(symbol, size, 'buy')
                        pnl = calculate_pnl(entry, price, size, True)
                        short_positions.pop(symbol)
                        rm.log_trade('US', 'SHORT_STOP', price, size, pnl)
                        send_alert(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                                  f"🛑 *SHORT STOP* {symbol}\n"
                                  f"💵 ${price:.2f} | 🔴 ${pnl:.2f}")
                        continue
                    if check_take_profit(entry, price, is_short=True):
                        alpaca.place_order(symbol, size, 'buy')
                        pnl = calculate_pnl(entry, price, size, True)
                        short_positions.pop(symbol)
                        rm.log_trade('US', 'SHORT_PROFIT', price, size, pnl)
                        send_alert(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                                  f"🎯 *SHORT PROFIT* {symbol}\n"
                                  f"💵 ${price:.2f} | 🟢 ${pnl:.2f}")
                        continue

                # New signals
                if signal == "BUY" and symbol not in long_positions:
                    if size > 0:
                        alpaca.place_order(symbol, size, 'buy')
                        long_positions[symbol] = price
                        send_alert(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                                  f"✅ *BUY* {symbol} 🇺🇸\n"
                                  f"💵 ${price:.2f} | 📦 {size} shares\n"
                                  f"🛑 ${price*(1-STOP_LOSS_PCT):.2f} | "
                                  f"🎯 ${price*(1+TAKE_PROFIT_PCT):.2f}")

                elif signal == "SHORT" and symbol not in short_positions:
                    if size > 0:
                        alpaca.place_order(symbol, size, 'sell')
                        short_positions[symbol] = price
                        send_alert(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                                  f"🔻 *SHORT* {symbol} 🇺🇸\n"
                                  f"💵 ${price:.2f} | 📦 {size} shares\n"
                                  f"🛑 ${price*(1+STOP_LOSS_PCT):.2f} | "
                                  f"🎯 ${price*(1-TAKE_PROFIT_PCT):.2f}")

                elif signal == "SELL" and symbol in long_positions:
                    alpaca.close_position(symbol)
                    entry = long_positions.pop(symbol)
                    pnl = calculate_pnl(entry, price, size)
                    emoji = "🟢" if pnl > 0 else "🔴"
                    send_alert(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                              f"📤 *SELL* {symbol}\n"
                              f"💵 ${price:.2f} | {emoji} ${pnl:.2f}")

                elif signal == "COVER" and symbol in short_positions:
                    alpaca.place_order(symbol, size, 'buy')
                    entry = short_positions.pop(symbol)
                    pnl = calculate_pnl(entry, price, size, True)
                    emoji = "🟢" if pnl > 0 else "🔴"
                    send_alert(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                              f"📤 *COVER* {symbol}\n"
                              f"💵 ${price:.2f} | {emoji} ${pnl:.2f}")

            except Exception as e:
                print(f"❌ {symbol}: {e}")

    except Exception as e:
        print(f"❌ US error: {e}")

# ═══════════════════════════════════════
# CRYPTO STRATEGY
# ═══════════════════════════════════════
def run_crypto_strategy():
    if not rm.trading_allowed:
        return

    try:
        for symbol in CRYPTO_SYMBOLS:
            try:
                df = binance.get_data(symbol, interval='1m', limit=100)
                if df is None or len(df) < 30:
                    continue

                signal = get_combined_signal(df)
                price = float(df['close'].iloc[-1])
                print(f"📊 {symbol}: ${price:.2f} | {signal}")

                # Stop loss / Take profit
                if symbol in long_positions:
                    entry = long_positions[symbol]
                    usdt = binance.get_balance('USDT')
                    qty = round((usdt * 0.05) / price, 6)

                    if check_stop_loss(entry, price):
                        asset = symbol.replace('USDT', '')
                        qty = binance.get_balance(asset)
                        binance.place_order(symbol, 'SELL', round(qty, 6))
                        pnl = calculate_pnl(entry, price, qty)
                        long_positions.pop(symbol)
                        send_alert(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                                  f"🛑 *STOP LOSS* {symbol}\n"
                                  f"💵 ${price:.2f} | 🔴 ${pnl:.2f}")
                        continue

                    if check_take_profit(entry, price):
                        asset = symbol.replace('USDT', '')
                        qty = binance.get_balance(asset)
                        binance.place_order(symbol, 'SELL', round(qty, 6))
                        pnl = calculate_pnl(entry, price, qty)
                        long_positions.pop(symbol)
                        send_alert(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                                  f"🎯 *TAKE PROFIT* {symbol}\n"
                                  f"💵 ${price:.2f} | 🟢 ${pnl:.2f}")
                        continue

                # New signals
                if signal == "BUY" and symbol not in long_positions:
                    usdt_balance = binance.get_balance('USDT')
                    quantity = round((usdt_balance * 0.05) / price, 6)
                    if quantity > 0:
                        binance.place_order(symbol, 'BUY', quantity)
                        long_positions[symbol] = price
                        send_alert(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                                  f"✅ *BUY* {symbol} 🌍\n"
                                  f"💵 ${price:.2f} | 📦 {quantity}\n"
                                  f"🛑 ${price*(1-STOP_LOSS_PCT):.2f} | "
                                  f"🎯 ${price*(1+TAKE_PROFIT_PCT):.2f}")

                elif signal == "SELL" and symbol in long_positions:
                    asset = symbol.replace('USDT', '')
                    qty = binance.get_balance(asset)
                    if qty > 0:
                        binance.place_order(symbol, 'SELL', round(qty, 6))
                        entry = long_positions.pop(symbol)
                        pnl = calculate_pnl(entry, price, qty)
                        emoji = "🟢" if pnl > 0 else "🔴"
                        send_alert(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                                  f"📤 *SELL* {symbol}\n"
                                  f"💵 ${price:.2f} | {emoji} ${pnl:.2f}")

            except Exception as e:
                print(f"❌ {symbol}: {e}")

    except Exception as e:
        print(f"❌ Crypto error: {e}")

# ═══════════════════════════════════════
# INDIA STRATEGY
# ═══════════════════════════════════════
def run_india_strategy():
    if zerodha is None:
        print("⚠️ Zerodha not connected")
        return
    if not is_india_open():
        print("💤 India Market closed")
        return

    try:
        balance = zerodha.get_balance()
        print(f"💰 Zerodha: ₹{balance:.2f}")

        for symbol in INDIA_SYMBOLS:
            try:
                df = zerodha.get_data(symbol)
                if df is None or len(df) < 30:
                    continue

                signal = get_combined_signal(df)
                price = df['close'].iloc[-1]
                size = int(rm.position_size() / price)
                key = f"IN_{symbol}"
                print(f"📊 {symbol}: ₹{price:.2f} | {signal}")

                # Stop loss / Take profit
                if key in long_positions:
                    entry = long_positions[key]
                    if check_stop_loss(entry, price):
                        zerodha.close_position(symbol, size)
                        pnl = calculate_pnl(entry, price, size)
                        long_positions.pop(key)
                        send_alert(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                                  f"🛑 *STOP LOSS* {symbol} 🇮🇳\n"
                                  f"💵 ₹{price:.2f} | 🔴 ₹{pnl:.2f}")
                        continue
                    if check_take_profit(entry, price):
                        zerodha.close_position(symbol, size)
                        pnl = calculate_pnl(entry, price, size)
                        long_positions.pop(key)
                        send_alert(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                                  f"🎯 *TAKE PROFIT* {symbol} 🇮🇳\n"
                                  f"💵 ₹{price:.2f} | 🟢 ₹{pnl:.2f}")
                        continue

                # New signals
                if signal == "BUY" and key not in long_positions:
                    if size > 0:
                        zerodha.place_order(symbol, size, 'buy')
                        long_positions[key] = price
                        send_alert(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                                  f"✅ *BUY* {symbol} 🇮🇳\n"
                                  f"💵 ₹{price:.2f} | 📦 {size} shares\n"
                                  f"🛑 ₹{price*(1-STOP_LOSS_PCT):.2f} | "
                                  f"🎯 ₹{price*(1+TAKE_PROFIT_PCT):.2f}")

                elif signal == "SELL" and key in long_positions:
                    zerodha.close_position(symbol, size)
                    entry = long_positions.pop(key)
                    pnl = calculate_pnl(entry, price, size)
                    emoji = "🟢" if pnl > 0 else "🔴"
                    send_alert(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                              f"📤 *SELL* {symbol} 🇮🇳\n"
                              f"💵 ₹{price:.2f} | {emoji} ₹{pnl:.2f}")

            except Exception as e:
                print(f"❌ {symbol}: {e}")

    except Exception as e:
        print(f"❌ India error: {e}")

# ═══════════════════════════════════════
# MASTER CONTROLLER
# ═══════════════════════════════════════
def master_run():
    print(f"\n{'═'*40}")
    print(f"🤖 MyAlgoBot running...")
    run_india_strategy()
    run_us_strategy()
    run_crypto_strategy()
    print(f"{'═'*40}")

# Every 1 minute
schedule.every(1).minutes.do(master_run)

send_alert(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
          "🚀 *MyAlgoBot v2 Started!*\n"
          f"🇮🇳 India: {len(INDIA_SYMBOLS)} stocks\n"
          f"🇺🇸 US: {len(US_SYMBOLS)} stocks\n"
          f"🌍 Crypto: {len(CRYPTO_SYMBOLS)} pairs\n"
          f"📉 Short selling: ON\n"
          f"🛑 Stop loss: {STOP_LOSS_PCT*100}%\n"
          f"🎯 Take profit: {TAKE_PROFIT_PCT*100}%\n"
          f"⏱ Every 1 minute")

print(f"✅ MyAlgoBot v2 started!")
print(f"🇮🇳 India: {INDIA_SYMBOLS}")
print(f"🇺🇸 US: {US_SYMBOLS}")
print(f"🌍 Crypto: {CRYPTO_SYMBOLS}")
print(f"📉 Short selling: ON")
print(f"🛑 Stop: {STOP_LOSS_PCT*100}% | 🎯 Target: {TAKE_PROFIT_PCT*100}%")

while True:
    schedule.run_pending()
    time.sleep(1)