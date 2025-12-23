#!/usr/bin/env python3
"""
Test and compare filtered vs scored fundamental strategies

Creates a NEW daily_signals_scored.py that uses the scored strategy
"""

import sys
import os

# Create a copy of daily_signals.py that uses the scored strategy
daily_signals_path = '/Users/faizanuddinmorkas/Work/Personal/ztrader_new/daily_signals.py'
scored_signals_path = '/Users/faizanuddinmorkas/Work/Personal/ztrader_new/daily_signals_scored.py'

print("Creating daily_signals_scored.py...")

with open(daily_signals_path, 'r') as f:
    content = f.read()

# Replace the strategy import
content = content.replace(
    'from src.strategies.signal_generator import SignalGenerator',
    '''from src.strategies.signal_generator import SignalGenerator
from src.strategies.multi_indicator_scored import MultiIndicatorScoredStrategy'''
)

# Modify the generator initialization to use scored strategy
# Find the line: generator = SignalGenerator(timeframe=args.timeframe, lookback=365)
# Add strategy_class parameter
content = content.replace(
    'generator = SignalGenerator(timeframe=args.timeframe, lookback=365)',
    'generator = SignalGenerator(timeframe=args.timeframe, lookback=365, strategy_class=MultiIndicatorScoredStrategy)'
)

# Change the title
content = content.replace(
    'print("DAILY TRADING SIGNALS")',
    'print("DAILY TRADING SIGNALS (SCORED FUNDAMENTALS)")'
)

# Write the new file
with open(scored_signals_path, 'w') as f:
    f.write(content)

print(f"✅ Created: {scored_signals_path}")
print()
print("Now you can test both strategies:")
print()
print("1. FILTERED (Current):")
print("   python3 daily_signals.py --test --symbols SBIN.NS BPCL.NS TCS.NS")
print()
print("2. SCORED (New):")
print("   python3 daily_signals_scored.py --test --symbols SBIN.NS BPCL.NS TCS.NS RELIANCE.NS")
print()
print("The scored version will analyze ALL symbols (no fundamental filter)")
