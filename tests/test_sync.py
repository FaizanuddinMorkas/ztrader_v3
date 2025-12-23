#!/usr/bin/env python3
"""
Quick test script to verify sync logging works
Tests with just 3 symbols to see immediate output
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.sync import DataSync

print("=" * 80)
print("QUICK SYNC TEST - 3 Symbols")
print("=" * 80)
print()

# Test with just 3 symbols
test_symbols = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS']

sync = DataSync(max_workers=3)

print(f"Testing sync with {len(test_symbols)} symbols...")
print(f"This should show immediate progress output")
print()

results = sync.sync_all_symbols(
    timeframes=['1d'],
    symbols=test_symbols,
    full_download=True
)

print()
print("=" * 80)
print("TEST RESULTS")
print("=" * 80)
print(f"Successful: {results['successful']}")
print(f"Failed: {results['failed']}")
print(f"Total rows: {results['total_rows']}")
print(f"Duration: {results['duration']:.2f}s")
print("=" * 80)
