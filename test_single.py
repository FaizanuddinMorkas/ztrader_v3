#!/usr/bin/env python3
"""
Simple single-symbol test to verify database connection
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.downloader import YFinanceDownloader

print("Testing single symbol download and insert...")
print()

downloader = YFinanceDownloader()

# Test with just one symbol
symbol = 'RELIANCE.NS'
timeframe = '1d'

print(f"Downloading {symbol} {timeframe}...")
rows = downloader.download_and_store(symbol, timeframe, period='1y')

print(f"\nResult: {rows} rows inserted")
print("Test complete!")
