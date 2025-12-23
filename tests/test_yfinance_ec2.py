#!/usr/bin/env python3
"""Test yfinance on EC2"""

import yfinance as yf
import pandas as pd
from datetime import datetime

print("=" * 60)
print("Testing yfinance on EC2")
print("=" * 60)
print()

# Test 1: Import check
print("✅ yfinance imported successfully")
print(f"   Version: {yf.__version__}")
print()

# Test 2: Download data for a single symbol
print("Testing data download for RELIANCE.NS...")
try:
    ticker = yf.Ticker("RELIANCE.NS")
    data = ticker.history(period="5d")
    
    if len(data) > 0:
        print(f"✅ Successfully downloaded {len(data)} rows")
        print()
        print("Latest data:")
        print(data.tail())
        print()
    else:
        print("❌ No data downloaded")
except Exception as e:
    print(f"❌ Error downloading data: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("Test completed at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 60)
