"""Quick test to see what S/R levels are detected"""
import sys
sys.path.insert(0, '/Users/faizanuddinmorkas/Work/Personal/ztrader_new')

from src.data.storage import get_storage
from src.indicators.support_resistance import SupportResistance

storage = get_storage()
symbol = 'SBIN.NS'

# Get data
df = storage.get_ohlcv(symbol, timeframe='1d', limit=365)
current_price = df.iloc[-1]['close']

print(f"\n{symbol} - Current Price: ₹{current_price:.2f}")
print("="*70)

# Create S/R detector
sr = SupportResistance(df)

# Find resistance with current settings
resistance = sr.find_resistance_levels(lookback=100, distance=5, prominence=0.5)

print(f"\nTotal resistance levels found: {len(resistance)}")
print(f"Resistance above current price:")

count = 0
for r in resistance:
    if r['price'] > current_price:
        pct_above = ((r['price'] - current_price) / current_price) * 100
        print(f"  ₹{r['price']:.2f} (+{pct_above:.1f}%, {r['touches']} touches, prom={r['prominence']:.2f})")
        count += 1
        if count >= 10:
            break

if count == 0:
    print("  None found!")

# Now test with a hypothetical stop-loss
print(f"\nTesting R:R validation:")
stop_loss = current_price * 0.97  # 3% stop
risk = current_price - stop_loss
print(f"  Entry: ₹{current_price:.2f}")
print(f"  Stop: ₹{stop_loss:.2f}")
print(f"  Risk: ₹{risk:.2f}")

# Check R:R for each resistance
valid_targets = sr.get_resistance_targets(current_price, stop_loss, min_rr=1.5, count=3)
print(f"\n  Valid targets (R:R >= 1.5): {len(valid_targets)}")
for i, t in enumerate(valid_targets):
    print(f"    T{i+1}: ₹{t['price']:.2f} (R:R {t['rr_ratio']:.2f})")
