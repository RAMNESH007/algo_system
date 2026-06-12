from config import TOTAL_CAPITAL
from risk.manager import RiskManager

rm = RiskManager(TOTAL_CAPITAL)

print(f"💰 Total Capital: ₹{rm.total_capital}")
print(f"📊 Position Size: ₹{rm.position_size()}")
print(f"✅ Trading Allowed: {rm.trading_allowed}")

# Simulate a loss
rm.update_capital(TOTAL_CAPITAL * 0.85)  # 15% loss
print(f"⚠️ After 15% loss - Trading Allowed: {rm.trading_allowed}")