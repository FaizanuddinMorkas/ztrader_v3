#!/usr/bin/env python3
"""
Extend Instruments with Top Gainers (NSE Only)

This script uses yfinance screener to find top gaining stocks in the Indian market,
filters for NSE listed companies, and adds them to the system.
"""

import sys
import logging
from pathlib import Path
import yfinance.screener as yfs
from yfinance.screener import EquityQuery

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.storage import InstrumentsDB, FundamentalsDB, DatabaseConnection
from src.data.downloader import YFinanceDownloader
from src.data.fundamentals import FundamentalsDownloader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('extend_instruments')

def fetch_top_gainers(count=20):
    """
    Fetch top gainers using yfinance screener.
    Returns a list of dicts with symbol details.
    """
    logger.info(f"Fetching top {count} gainers from Yahoo Finance...")
    
    # query: percent change > 3% AND region = India AND volume > 10000
    q = EquityQuery('AND', [
        EquityQuery('GT', ['percentchange', 3]),
        EquityQuery('EQ', ['region', 'in']),
        EquityQuery('GT', ['dayvolume', 10000])
    ])
    
    try:
        response = yfs.screener.screen(query=q, count=count*2) # Fetch more to allow for filtering
        quotes = response.get('quotes', [])
        logger.info(f"Retrieved {len(quotes)} raw results.")
        return quotes
    except Exception as e:
        logger.error(f"Failed to fetch gainers: {e}")
        return []

def filter_nse_stocks(quotes):
    """
    Filter for NSE stocks only (ending with .NS).
    """
    nse_stocks = []
    for q in quotes:
        symbol = q.get('symbol', '')
        if symbol.endswith('.NS'):
            nse_stocks.append(q)
    
    logger.info(f"Filtered down to {len(nse_stocks)} NSE stocks.")
    return nse_stocks

def main():
    logger.info("Starting instrument extension process...")
    
    # 1. Fetch and Filter
    raw_gainers = fetch_top_gainers(count=50)
    nse_gainers = filter_nse_stocks(raw_gainers)
    
    if not nse_gainers:
        logger.warning("No NSE gainers found matching criteria.")
        return

    # 2. Check against Database
    db = InstrumentsDB()
    existing_df = db.get_all_active()
    existing_symbols = set(existing_df['symbol'].tolist()) if not existing_df.empty else set()
    
    to_add = []
    for stock in nse_gainers:
        symbol = stock['symbol']
        if symbol not in existing_symbols:
            to_add.append(stock)
    
    if not to_add:
        logger.info("All found gainers are already in the database.")
        return
        
    logger.info(f"Found {len(to_add)} new stocks to add.")
    
    # 3. Add to Database and Sync
    downloader = YFinanceDownloader()
    fund_downloader = FundamentalsDownloader()
    fund_db = FundamentalsDB()
    
    for i, stock in enumerate(to_add, 1):
        symbol = stock['symbol']
        name = stock.get('shortName', stock.get('longName', symbol))
        
        logger.info(f"Processing [{i}/{len(to_add)}]: {symbol} - {name}")
        
        # Add to instruments
        try:
            db.insert_instrument(
                symbol=symbol,
                name=name,
                sector=None, # yfinance screener results might not have this detailed info easily accessible in this view
                industry=None,
                is_nifty_50=False,
                is_nifty_100=False
            )
            logger.info(f"  - Added to instruments table")
        except Exception as e:
            logger.error(f"  - Failed to add to DB: {e}")
            continue
            
        # Sync OHLCV (1d)
        try:
            rows = downloader.download_and_store(symbol, '1d', period='2y')
            logger.info(f"  - Synced {rows} daily candles")
        except Exception as e:
            logger.error(f"  - Failed to sync OHLCV: {e}")
            
        # Sync Fundamentals
        try:
            fundamentals = fund_downloader.download_fundamentals(symbol)
            if fundamentals:
                fund_db.upsert_fundamentals(fundamentals)
                pe = fundamentals.get('trailing_pe', 'N/A')
                logger.info(f"  - Synced Fundamentals (PE: {pe})")
            else:
                logger.warning(f"  - No fundamentals found")
        except Exception as e:
             logger.error(f"  - Failed to sync fundamentals: {e}")
             
    logger.info("Extension process completed.")

if __name__ == '__main__':
    main()
