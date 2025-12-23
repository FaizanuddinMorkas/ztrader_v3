#!/usr/bin/env python3
"""Check what candle data is being sent to AI"""

import sys
sys.path.insert(0, '/Users/faizanuddinmorkas/Work/Personal/ztrader_new')

from src.data.storage import OHLCVDB
from datetime import datetime

db = OHLCVDB()

# Get last 30 candles for SBIN.NS
symbol = 'SBIN.NS'
timeframe = '1d'

query = """
    SELECT time, open, high, low, close, volume
    FROM ohlcv_data
    WHERE symbol = %s AND timeframe = %s
    ORDER BY time DESC
    LIMIT 30
"""

with db.db.get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(query, (symbol, timeframe))
        rows = cur.fetchall()
        
        print(f"Last 30 candles for {symbol}:")
        print(f"{'Date':<12} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10} {'Volume':>12}")
        print("-" * 70)
        
        for row in reversed(rows):  # Show oldest first
            time, open_p, high, low, close, volume = row
            print(f"{str(time):<12} {open_p:>10.2f} {high:>10.2f} {low:>10.2f} {close:>10.2f} {volume:>12,}")
        
        print(f"\nOldest candle: {rows[-1][0]}")
        print(f"Newest candle: {rows[0][0]}")
        print(f"Total candles: {len(rows)}")
