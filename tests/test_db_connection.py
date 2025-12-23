#!/usr/bin/env python3
"""Test database connection on EC2"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("Testing Database Connection on EC2")
print("=" * 60)
print()

# Print connection details (without password)
print("Database Configuration:")
print(f"  Host: {os.getenv('DB_HOST')}")
print(f"  Port: {os.getenv('DB_PORT')}")
print(f"  Database: {os.getenv('DB_NAME')}")
print(f"  User: {os.getenv('DB_USER')}")
print()

# Test connection
try:
    from src.data.storage import InstrumentsDB, OHLCVDB
    
    print("Testing InstrumentsDB connection...")
    instruments_db = InstrumentsDB()
    instruments = instruments_db.get_all_active()
    print(f"✅ Connected! Found {len(instruments)} active instruments")
    print()
    
    print("Sample instruments:")
    for _, row in instruments.head(5).iterrows():
        print(f"  - {row['symbol']}: {row['name']}")
    print()
    
    print("Testing OHLCVDB connection...")
    ohlcv_db = OHLCVDB()
    
    # Test with first symbol
    test_symbol = instruments.iloc[0]['symbol']
    latest_time = ohlcv_db.get_latest_timestamp(test_symbol, '1d')
    
    if latest_time:
        print(f"✅ OHLCV data accessible")
        print(f"  Latest data for {test_symbol}: {latest_time}")
    else:
        print(f"⚠️  No OHLCV data found for {test_symbol}")
    
    print()
    print("=" * 60)
    print("✅ Database connection test PASSED")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Database connection FAILED")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
