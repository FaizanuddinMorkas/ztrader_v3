#!/usr/bin/env python3
"""
Test script to verify Tata Motors demerged entity ticker symbols
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

import yfinance as yf

print("=" * 80)
print("Testing Tata Motors Demerged Entity Ticker Symbols")
print("=" * 80)
print()

# Test possible ticker symbols for demerged entities
test_symbols = [
    # Passenger Vehicles possibilities
    'TATAMOTORSPV.NS',
    'TATAMOTORS-PV.NS',
    'TMPV.NS',
    'TATAPV.NS',
    
    # Commercial Vehicles possibilities
    'TATAMOTOR-CV.NS',
    'TATAMOTORS-CV.NS',
    'TMLCV.NS',
    'TMCV.NS',
    'TATACV.NS',
    
    # Also test existing symbols
    'TATAMOTORS.NS',
    'TATAMOTORS-DVR.NS',
]

print("Testing symbols on NSE via yfinance...\n")

found_symbols = []
not_found_symbols = []

for symbol in test_symbols:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Check if we got valid data
        if info and len(info) > 1 and 'symbol' in info:
            long_name = info.get('longName', info.get('shortName', 'N/A'))
            print(f"✓ {symbol:25s} - FOUND: {long_name}")
            found_symbols.append((symbol, long_name))
        else:
            print(f"✗ {symbol:25s} - Not found or no data")
            not_found_symbols.append(symbol)
    except Exception as e:
        print(f"✗ {symbol:25s} - Error: {str(e)[:50]}")
        not_found_symbols.append(symbol)

print()
print("=" * 80)
print("Summary")
print("=" * 80)
print(f"Found: {len(found_symbols)} symbols")
print(f"Not found: {len(not_found_symbols)} symbols")
print()

if found_symbols:
    print("Valid symbols to add to seed data:")
    for symbol, name in found_symbols:
        print(f"  ('{symbol}', '{name}', 'Automobile', 'Auto Manufacturer', False),")
else:
    print("No new symbols found. The demerged entities may not be listed yet.")
    print("Continue using TATAMOTORS.NS and TATAMOTORS-DVR.NS")

print()
print("=" * 80)
