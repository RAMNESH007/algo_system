# risk/manager.py
from config import RISK_PER_TRADE_PCT

class RiskManager:
    def __init__(self, total_capital, max_drawdown=0.10):
        self.total_capital = total_capital
        self.current_capital = total_capital
        self.peak_capital = total_capital
        self.max_drawdown = max_drawdown
        self.trading_allowed = True
        self.trades = []

    def update_capital(self, new_capital):
        self.current_capital = new_capital
        if new_capital > self.peak_capital:
            self.peak_capital = new_capital
        self.check_drawdown()

    def check_drawdown(self):
        drawdown = (self.peak_capital - self.current_capital) / self.peak_capital
        if drawdown >= self.max_drawdown:
            self.trading_allowed = False
            print(f"⚠️ DRAWDOWN LIMIT HIT: {drawdown*100:.1f}% — Trading stopped!")
        return self.trading_allowed

    def position_size(self):
        return self.current_capital * RISK_PER_TRADE_PCT

    def log_trade(self, market, signal, price, size, pnl=0):
        self.trades.append({
            "market": market,
            "signal": signal,
            "price": price,
            "size": size,
            "pnl": pnl
        })
        print(f"📝 Trade: {market} | {signal} | PnL: {pnl}")

    def get_stats(self):
        if not self.trades:
            return "No trades yet"
        total_pnl = sum(t['pnl'] for t in self.trades)
        wins = len([t for t in self.trades if t['pnl'] > 0])
        total = len(self.trades)
        win_rate = (wins/total*100) if total > 0 else 0
        return {
            "total_trades": total,
            "win_rate": f"{win_rate:.1f}%",
            "total_pnl": f"{total_pnl:.2f}",
            "trading_allowed": self.trading_allowed
        }