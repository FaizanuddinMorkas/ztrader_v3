"""
Sync fundamentals data for all Nifty 100 symbols

Downloads fundamental data from yfinance and stores in database
"""

import sys
import time
import logging
from datetime import datetime
from src.data.fundamentals import FundamentalsDownloader
from src.data.storage import InstrumentsDB, FundamentalsDB

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def sync_all_fundamentals():
    """Download and store fundamentals for all Nifty 100 symbols"""
    
    print("=" * 80)
    print("SYNCING FUNDAMENTALS FOR ALL NIFTY 100 SYMBOLS")
    print("=" * 80)
    
    # Initialize
    instruments_db = InstrumentsDB()
    fundamentals_db = FundamentalsDB()
    downloader = FundamentalsDownloader()
    
    # Get all Nifty 100 symbols
    symbols = instruments_db.get_nifty_100()
    print(f"\nTotal symbols to sync: {len(symbols)}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Track results
    successful = 0
    failed = 0
    failed_symbols = []
    
    # Download and store
    for i, symbol in enumerate(symbols, 1):
        try:
            print(f"[{i}/{len(symbols)}] {symbol:20s} ", end="", flush=True)
            
            # Download
            fundamentals = downloader.download_fundamentals(symbol)
            
            if fundamentals:
                # Store
                fundamentals_db.upsert_fundamentals(fundamentals)
                
                # Display key metrics
                pe = fundamentals.get('trailing_pe', 'N/A')
                market_cap = fundamentals.get('market_cap', 0)
                
                if market_cap:
                    market_cap_str = f"₹{market_cap/1e9:.1f}B" if market_cap < 1e12 else f"₹{market_cap/1e12:.2f}T"
                else:
                    market_cap_str = "N/A"
                
                print(f"✓ PE: {pe:>8} | MCap: {market_cap_str:>10}")
                successful += 1
            else:
                print("✗ No data")
                failed += 1
                failed_symbols.append(symbol)
            
            # Rate limiting
            if i < len(symbols):
                time.sleep(0.5)
                
        except Exception as e:
            print(f"✗ Error: {e}")
            failed += 1
            failed_symbols.append(symbol)
            logger.error(f"Error syncing {symbol}: {e}")
    
    # Summary
    print()
    print("=" * 80)
    print("SYNC SUMMARY")
    print("=" * 80)
    print(f"Total symbols: {len(symbols)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    
    if failed_symbols:
        print(f"\nFailed symbols: {', '.join(failed_symbols)}")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Show sample data
    print("\nSample fundamentals data:")
    all_data = fundamentals_db.get_all_fundamentals()
    if not all_data.empty:
        print(all_data[['symbol', 'current_price', 'market_cap', 'trailing_pe', 'return_on_equity', 'sector']].head(10).to_string(index=False))
    
    # Sector summary
    print("\nSector summary:")
    sector_summary = fundamentals_db.get_sector_summary()
    if not sector_summary.empty:
        print(sector_summary.to_string(index=False))


if __name__ == '__main__':
    sync_all_fundamentals()
