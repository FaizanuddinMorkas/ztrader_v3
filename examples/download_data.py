"""
Example script: Download historical data for Nifty 100 stocks

This script demonstrates how to:
1. Connect to the database
2. Get list of Nifty 100 symbols
3. Download historical OHLCV data
4. Store data in the database
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.downloader import YFinanceDownloader, download_nifty100_data
from src.data.storage import InstrumentsDB
from src.utils.logger import setup_logger

# Setup logging
logger = setup_logger('download_data')


def main():
    """Download historical data for Nifty 100 stocks"""
    
    logger.info("=" * 60)
    logger.info("Nifty 100 Historical Data Download")
    logger.info("=" * 60)
    
    # Check if we have instruments in database
    instruments_db = InstrumentsDB()
    symbols = instruments_db.get_nifty_100()
    
    if not symbols:
        logger.error("No Nifty 100 symbols found in database!")
        logger.error("Please populate the instruments table first.")
        return
    
    logger.info(f"Found {len(symbols)} Nifty 100 symbols in database")
    
    # Download data for multiple timeframes
    timeframes = ['1d', '1h']  # Daily and hourly data
    period = '1y'  # Last 1 year
    
    logger.info(f"Downloading {period} of data for timeframes: {timeframes}")
    logger.info("This may take several minutes...")
    
    # Download data
    results = download_nifty100_data(timeframes=timeframes, period=period)
    
    # Print summary
    logger.info("=" * 60)
    logger.info("Download Summary")
    logger.info("=" * 60)
    
    for timeframe, symbol_results in results.items():
        total_rows = sum(symbol_results.values())
        successful = sum(1 for rows in symbol_results.values() if rows > 0)
        
        logger.info(f"\nTimeframe: {timeframe}")
        logger.info(f"  Symbols processed: {len(symbol_results)}")
        logger.info(f"  Successful: {successful}")
        logger.info(f"  Total rows inserted: {total_rows}")
    
    logger.info("\n" + "=" * 60)
    logger.info("Download completed!")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
