# backtest/run.py
import backtrader as bt
import yfinance as yf
import pandas as pd

# ═══════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════
SYMBOL = 'AAPL'
START_DATE = '2020-01-01'
END_DATE = '2024-01-01'
STARTING_CAPITAL = 50000
RISK_PER_TRADE = 0.10
COMMISSION = 0.001
EMA_FAST = 9
EMA_SLOW = 21
STOP_LOSS_PCT = 0.05
TAKE_PROFIT_PCT = 0.15

print(f"\n{'═'*50}")
print(f"  ALGO BACKTEST SYSTEM")
print(f"  Symbol: {SYMBOL} | {START_DATE} → {END_DATE}")
print(f"{'═'*50}\n")

# ═══════════════════════════════════════
# DOWNLOAD DATA
# ═══════════════════════════════════════
print("📥 Downloading data...")
raw = yf.download(SYMBOL, start=START_DATE, end=END_DATE, interval='1d')
raw.columns = [col[0].lower() if isinstance(col, tuple) else col.lower()
               for col in raw.columns]
raw.index.name = 'datetime'
raw.to_csv('data/AAPL.csv')
print(f"✅ {len(raw)} candles downloaded\n")

# ═══════════════════════════════════════
# DATA FEED
# ═══════════════════════════════════════
class PandasData(bt.feeds.PandasData):
    params = (
        ('datetime', None),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', -1),
    )

# ═══════════════════════════════════════
# STRATEGY
# ═══════════════════════════════════════
class EMAStrategy(bt.Strategy):

    def __init__(self):
        self.ema_fast = bt.indicators.EMA(period=EMA_FAST)
        self.ema_slow = bt.indicators.EMA(period=EMA_SLOW)
        self.rsi = bt.indicators.RSI(period=14)

        self.order = None
        self.buy_price = None
        self.stop_price = None
        self.target_price = None

        self.trades_count = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_profit = 0
        self.total_loss = 0
        self.max_drawdown = 0
        self.peak = STARTING_CAPITAL

    def next(self):
        if self.order:
            return

        # Track drawdown
        current_value = self.broker.getvalue()
        if current_value > self.peak:
            self.peak = current_value
        drawdown = (self.peak - current_value) / self.peak * 100
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown

        # Exit logic
        if self.position:
            if self.data.close[0] <= self.stop_price:
                self.order = self.sell(size=self.position.size)
                return
            if self.data.close[0] >= self.target_price:
                self.order = self.sell(size=self.position.size)
                return

        # Entry logic
        if not self.position:
            ema_cross = (self.ema_fast[0] > self.ema_slow[0] and
                        self.ema_fast[-1] <= self.ema_slow[-1])

            if ema_cross:
                cash = self.broker.getcash()
                size = int((cash * RISK_PER_TRADE) / self.data.close[0])

                if size > 0:
                    self.buy_price = self.data.close[0]
                    self.stop_price = self.buy_price * (1 - STOP_LOSS_PCT)
                    self.target_price = self.buy_price * (1 + TAKE_PROFIT_PCT)
                    self.order = self.buy(size=size)
                    self.trades_count += 1
                    print(f"🟢 BUY  @ ${self.buy_price:.2f} | "
                          f"Stop: ${self.stop_price:.2f} | "
                          f"Target: ${self.target_price:.2f}")

    def notify_order(self, order):
        if order.status in [order.Completed]:
            self.order = None

    def notify_trade(self, trade):
        if trade.isclosed:
            pnl = trade.pnl
            if pnl > 0:
                self.winning_trades += 1
                self.total_profit += pnl
                print(f"✅ WIN  PnL: ${pnl:.2f}")
            else:
                self.losing_trades += 1
                self.total_loss += pnl
                print(f"❌ LOSS PnL: ${pnl:.2f}")

    def stop(self):
        final = self.broker.getvalue()
        profit = final - STARTING_CAPITAL
        win_rate = (self.winning_trades / self.trades_count * 100) if self.trades_count > 0 else 0
        avg_win = self.total_profit / self.winning_trades if self.winning_trades > 0 else 0
        avg_loss = self.total_loss / self.losing_trades if self.losing_trades > 0 else 0
        profit_factor = abs(self.total_profit / self.total_loss) if self.total_loss != 0 else 0
        expectancy = (win_rate/100 * avg_win) + ((1 - win_rate/100) * avg_loss)

        print(f"\n{'═'*50}")
        print(f"  📈 BACKTEST RESULTS — {SYMBOL}")
        print(f"{'═'*50}")
        print(f"  Period          : {START_DATE} → {END_DATE}")
        print(f"  Starting Capital: ${STARTING_CAPITAL:,.2f}")
        print(f"  Final Capital   : ${final:,.2f}")
        print(f"  Total Profit    : ${profit:,.2f}")
        print(f"  Return          : {(profit/STARTING_CAPITAL)*100:.1f}%")
        print(f"{'─'*50}")
        print(f"  Total Trades    : {self.trades_count}")
        print(f"  Winning Trades  : {self.winning_trades}")
        print(f"  Losing Trades   : {self.losing_trades}")
        print(f"  Win Rate        : {win_rate:.1f}%")
        print(f"{'─'*50}")
        print(f"  Avg Win         : ${avg_win:.2f}")
        print(f"  Avg Loss        : ${avg_loss:.2f}")
        print(f"  Profit Factor   : {profit_factor:.2f}")
        print(f"  Expectancy      : ${expectancy:.2f}")
        print(f"  Max Drawdown    : {self.max_drawdown:.1f}%")
        print(f"{'─'*50}")

        if profit > 0 and win_rate > 40 and self.max_drawdown < 20:
            print(f"  Grade : ✅ GOOD — Safe to paper trade")
        elif profit > 0:
            print(f"  Grade : ⚠️  AVERAGE — Needs improvement")
        else:
            print(f"  Grade : ❌ POOR — Do not trade live")
        print(f"{'═'*50}\n")

# ═══════════════════════════════════════
# RUN
# ═══════════════════════════════════════
cerebro = bt.Cerebro()
cerebro.addstrategy(EMAStrategy)

df = pd.read_csv('data/AAPL.csv', index_col='datetime', parse_dates=True)
df = df[['open', 'high', 'low', 'close', 'volume']]

feed = PandasData(dataname=df)
cerebro.adddata(feed)
cerebro.broker.setcash(STARTING_CAPITAL)
cerebro.broker.setcommission(commission=COMMISSION)

cerebro.run()
cerebro.plot(style='candlestick')