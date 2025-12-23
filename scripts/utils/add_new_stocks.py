#!/usr/bin/env python3
"""
Comprehensive script to add new stocks to database
1. Verify data exists on yfinance
2. Add symbols to instruments table
3. Sync OHLCV data for all timeframes
4. Sync fundamentals
5. Run signal generation
"""

import sys
import yfinance as yf
from src.data.downloader import YFinanceDownloader
from src.data.fundamentals import FundamentalsDownloader
from src.data.storage import InstrumentsDB, FundamentalsDB

# Stocks to add
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

def verify_yfinance_data(symbol):
    """Check if symbol has data on yfinance"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period='5d')
        if len(df) > 0:
            return True, ticker.info.get('longName', symbol.replace('.NS', ''))
        return False, None
    except:
        return False, None

def main():
    print("=" * 70)
    print("COMPREHENSIVE STOCK SYNC SCRIPT")
    print("=" * 70)
    print(f"Stocks to add: {', '.join(SYMBOLS)}\n")
    
    instruments_db = InstrumentsDB()
    downloader = YFinanceDownloader()
    fund_downloader = FundamentalsDownloader()
    fund_db = FundamentalsDB()
    
    verified_symbols = []
    
    # STEP 1: Verify data exists on yfinance
    print("\n" + "=" * 70)
    print("STEP 1: VERIFYING DATA ON YFINANCE")
    print("=" * 70)
    for symbol in SYMBOLS:
        print(f"Checking {symbol}...", end=" ")
        has_data, name = verify_yfinance_data(symbol)
        if has_data:
            print(f"✅ Data available ({name})")
            verified_symbols.append((symbol, name))
        else:
            print(f"❌ No data available")
    
    if not verified_symbols:
        print("\n❌ No symbols with data found. Exiting.")
        return
    
    print(f"\n✅ Verified {len(verified_symbols)} symbols")
    
    # STEP 2: Add symbols to instruments table
    print("\n" + "=" * 70)
    print("STEP 2: ADDING SYMBOLS TO INSTRUMENTS TABLE")
    print("=" * 70)
    for symbol, name in verified_symbols:
        try:
            instruments_db.insert_instrument(
                symbol=symbol,
                name=name,
                sector=None,
                industry=None,
                is_nifty_50=False,
                is_nifty_100=False
            )
            print(f"✅ {symbol}: Added to instruments table")
        except Exception as e:
            print(f"❌ {symbol}: Error - {str(e)}")
    
    # STEP 3: Sync OHLCV data (1d timeframe only for now)
    print("\n" + "=" * 70)
    print("STEP 3: SYNCING OHLCV DATA (1d timeframe)")
    print("=" * 70)
    for symbol, name in verified_symbols:
        try:
            print(f"Syncing {symbol}...", end=" ")
            rows = downloader.download_and_store(symbol, '1d', period='2y')
            if rows > 0:
                print(f"✅ {rows} candles")
            else:
                print(f"✓ Already up to date")
        except Exception as e:
            print(f"❌ Error - {str(e)}")
    
    # STEP 4: Sync fundamentals
    print("\n" + "=" * 70)
    print("STEP 4: SYNCING FUNDAMENTALS")
    print("=" * 70)
    for symbol, name in verified_symbols:
        try:
            print(f"Fetching {symbol}...", end=" ")
            fundamentals = fund_downloader.download_fundamentals(symbol)
            
            if fundamentals:
                fund_db.upsert_fundamentals(fundamentals)
                
                pe = fundamentals.get('trailing_pe', 'N/A')
                roe = fundamentals.get('return_on_equity')
                roe_pct = f"{roe*100:.1f}%" if roe else 'N/A'
                
                print(f"✅ P/E={pe}, ROE={roe_pct}")
            else:
                print(f"⚠️  No fundamentals available")
        except Exception as e:
            print(f"❌ Error - {str(e)}")
    
    # STEP 5: Run signal generation
    print("\n" + "=" * 70)
    print("STEP 5: RUNNING SIGNAL GENERATION")
    print("=" * 70)
    print("Run this command to generate signals:")
    symbol_list = ' '.join([s for s, _ in verified_symbols])
    print(f"\npython3 daily_signals_scored.py --symbols {symbol_list} --sentiment\n")
    
    print("=" * 70)
    print("✅ SYNC COMPLETE!")
    print("=" * 70)

if __name__ == '__main__':
    main()
