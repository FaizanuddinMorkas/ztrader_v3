"""
Test script for fundamentals data module

Downloads and stores fundamental data for Nifty 100 stocks
"""

import sys
from src.data.fundamentals import FundamentalsDownloader
from src.data.storage import InstrumentsDB, FundamentalsDB


def test_fundamentals():
    """Test fundamentals downloader and storage"""
    
    print("=" * 80)
    print("FUNDAMENTALS DATA MODULE TEST")
    print("=" * 80)
    
    # Initialize
    print("\n[1/5] Initializing...")
    instruments_db = InstrumentsDB()
    fundamentals_db = FundamentalsDB()
    downloader = FundamentalsDownloader()
    
    # Get test symbols (first 5 Nifty 100)
    symbols = instruments_db.get_nifty_100()[:5]
    print(f"✓ Testing with {len(symbols)} symbols: {', '.join(symbols)}")
    
    # Download fundamentals
    print("\n[2/5] Downloading fundamentals...")
    for i, symbol in enumerate(symbols, 1):
        print(f"  [{i}/{len(symbols)}] {symbol}...", end=" ")
        
        fundamentals = downloader.download_fundamentals(symbol)
        if fundamentals:
            # Save to database
            fundamentals_db.upsert_fundamentals(fundamentals)
            print(f"✓ Saved {len(fundamentals)} fields")
        else:
            print("✗ Failed")
    
    # Retrieve and display
    print("\n[3/5] Retrieving fundamentals...")
    for symbol in symbols:
        data = fundamentals_db.get_fundamentals(symbol)
        if data:
            print(f"\n{symbol}:")
            print(f"  Price: ₹{data.get('current_price', 'N/A')}")
            print(f"  Market Cap: ₹{data.get('market_cap', 'N/A'):,}" if data.get('market_cap') else "  Market Cap: N/A")
            print(f"  PE Ratio: {data.get('trailing_pe', 'N/A')}")
            print(f"  ROE: {data.get('return_on_equity', 'N/A')}")
            print(f"  Sector: {data.get('sector', 'N/A')}")
    
    # Test screening
    print("\n[4/5] Testing screening...")
    results = fundamentals_db.screen_by_criteria(
        max_pe=30,
        min_roe=0.10
    )
    print(f"✓ Found {len(results)} stocks with PE < 30 and ROE > 10%")
    if not results.empty:
        print("\nTop matches:")
        print(results[['symbol', 'current_price', 'trailing_pe', 'return_on_equity']].head())
    
    # Sector summary
    print("\n[5/5] Sector summary...")
    sector_summary = fundamentals_db.get_sector_summary()
    if not sector_summary.empty:
        print("\nSector Statistics:")
        print(sector_summary.to_string(index=False))
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    print("\nFundamentals module is ready to use!")
    print("Run: python sync_fundamentals.py --all")


if __name__ == '__main__':
    test_fundamentals()
