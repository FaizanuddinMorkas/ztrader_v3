#!/usr/bin/env python3
"""
Quick script to sync specific stocks to database
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.data.downloader import YFinanceDownloader
from src.data.fundamentals import FundamentalsDownloader
from src.data.storage import DatabaseConnection, FundamentalsDB, InstrumentsDB

# Stocks to sync
SYMBOLS = [
    'RECLTD.NS',      # REC
    'PFC.NS',         # PFC
    'BDL.NS',         # BDL
    'BSE.NS',         # BSE
    'BIOCON.NS',      # BIOCON
    'GODREJCP.NS',    # GODREJ CONSUMER
    'BANKINDIA.NS',   # BOI
    'SRF.NS'          # SRF
]

def main():
    print("Syncing special stocks to database...")
    print(f"Stocks: {', '.join(SYMBOLS)}\n")
    
    downloader = YFinanceDownloader()
    fund_downloader = FundamentalsDownloader()
    fund_db = FundamentalsDB()
    instruments_db = InstrumentsDB()
    
    # First, ensure all symbols are in instruments table
    print("=" * 60)
    print("CHECKING/ADDING SYMBOLS TO INSTRUMENTS TABLE")
    print("=" * 60)
    for symbol in SYMBOLS:
        try:
            # Check if symbol exists
            existing = instruments_db.get_instrument(symbol)
            
            if existing:
                print(f"✓ {symbol}: Already in instruments table")
            else:
                # Add to instruments table
                instruments_db.add_instrument({
                    'symbol': symbol,
                    'name': symbol.replace('.NS', ''),  # Simple name extraction
                    'exchange': 'NSE',
                    'type': 'EQUITY'
                })
                print(f"✅ {symbol}: Added to instruments table")
        except Exception as e:
            print(f"❌ {symbol}: Error adding to instruments - {str(e)}")
    
    print("")
    
    # Sync OHLCV data
    print("=" * 60)
    print("SYNCING OHLCV DATA")
    print("=" * 60)
    for symbol in SYMBOLS:
        try:
            print(f"Syncing {symbol}...")
            
            # Download and store 2 years of daily data (covers 365 candles + buffer)
            rows = downloader.download_and_store(symbol, '1d', period='2y')
            
            if rows > 0:
                print(f"✅ {symbol}: Synced {rows} candles\n")
            else:
                print(f"❌ {symbol}: No data synced\n")
                
        except Exception as e:
            print(f"❌ {symbol}: Error - {str(e)}\n")
    
    # Sync Fundamentals
    print("\n" + "=" * 60)
    print("SYNCING FUNDAMENTALS")
    print("=" * 60)
    for symbol in SYMBOLS:
        try:
            print(f"Fetching fundamentals for {symbol}...")
            
            # Download fundamentals
            fundamentals = fund_downloader.download_fundamentals(symbol)
            
            if fundamentals:
                # Store in database using FundamentalsDB
                fund_db.upsert_fundamentals(fundamentals)
                
                pe = fundamentals.get('trailing_pe', 'N/A')
                roe = fundamentals.get('return_on_equity')
                roe_pct = f"{roe*100:.1f}%" if roe else 'N/A'
                debt_eq = fundamentals.get('debt_to_equity', 'N/A')
                
                print(f"✅ {symbol}: P/E={pe}, ROE={roe_pct}, Debt/Eq={debt_eq}\n")
            else:
                print(f"❌ {symbol}: No fundamentals available\n")
                
        except Exception as e:
            print(f"❌ {symbol}: Error - {str(e)}\n")
    
    print("=" * 60)
    print("✅ Sync complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
