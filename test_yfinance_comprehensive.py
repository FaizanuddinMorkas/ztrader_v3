#!/usr/bin/env python3
"""Comprehensive yfinance test on EC2"""

import yfinance as yf
import pandas as pd
from datetime import datetime
import sys

print("=" * 60)
print("Comprehensive yfinance Test on EC2")
print("=" * 60)
print()

# Test 1: Import check
print("✅ yfinance imported successfully")
print(f"   Version: {yf.__version__}")
print()

# Test 2: Internet connectivity
print("Testing internet connectivity...")
try:
    import urllib.request
    urllib.request.urlopen('https://www.google.com', timeout=5)
    print("✅ Internet connection is working")
except Exception as e:
    print(f"❌ Internet connection failed: {e}")
print()

# Test 3: Try multiple symbols
symbols = [
    "RELIANCE.NS",
    "TCS.NS", 
    "INFY.NS",
    "AAPL",  # US stock
    "^NSEI"  # Nifty 50 index
]

print("Testing data download for multiple symbols...")
print("-" * 60)

for symbol in symbols:
    print(f"\nTesting {symbol}...")
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="5d")
        
        if len(data) > 0:
            print(f"  ✅ Success: {len(data)} rows downloaded")
            print(f"  Latest close: {data['Close'].iloc[-1]:.2f}")
            print(f"  Date range: {data.index[0].date()} to {data.index[-1].date()}")
        else:
            print(f"  ❌ No data returned")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

print()
print("-" * 60)

# Test 4: Try with different period
print("\nTesting with different time periods for RELIANCE.NS...")
periods = ["1d", "5d", "1mo"]
for period in periods:
    try:
        ticker = yf.Ticker("RELIANCE.NS")
        data = ticker.history(period=period)
        print(f"  Period {period:4s}: {len(data):3d} rows")
    except Exception as e:
        print(f"  Period {period:4s}: Error - {e}")

print()
print("=" * 60)
print("Test completed at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 60)
