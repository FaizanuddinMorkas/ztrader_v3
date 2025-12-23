"""
Data downloader module using yfinance
"""

import yfinance as yf
import pandas as pd
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from src.config.settings import DataConfig, TradingConfig
from src.data.storage import OHLCVDB

logger = logging.getLogger(__name__)


class YFinanceDownloader:
    """Downloads market data using yfinance"""
    
    def __init__(self):
        self.db = OHLCVDB()
    
    def download_historical(self, symbol: str, timeframe: str,
                           period: str = '1y') -> pd.DataFrame:
        """
        Download historical data for a symbol
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            timeframe: Timeframe ('1m', '5m', '15m', '1h', '1d')
            period: Period to download ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', 'max')
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Immediate console feedback
            print(f"⬇ {symbol} {timeframe}...", flush=True)
            logger.info(f"Downloading {symbol} {timeframe} for period {period}...")
            
            # Use yf.download() instead of ticker.history() - it's faster!
            df = yf.download(
                symbol,
                period=period,
                interval=timeframe,
                progress=False  # Disable yfinance progress bar
            )
            
            # Add delay to prevent rate limiting
            import time
            time.sleep(2.0)  # Wait 2 seconds between requests (increased from 0.5s)
            
            if df.empty:
                logger.warning(f"No data returned for {symbol} {timeframe}")
                return pd.DataFrame()
            
            # Prepare data for database
            df = df.reset_index()
            
            # Fix MultiIndex columns (yf.download returns MultiIndex for single symbol)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            df.columns = df.columns.str.lower()
            
            # Rename columns to match database schema
            column_mapping = {
                'date': 'time',
                'datetime': 'time'
            }
            df = df.rename(columns=column_mapping)
            
            # Select only required columns
            required_cols = ['time', 'open', 'high', 'low', 'close', 'volume']
            df = df[required_cols]
            
            logger.info(f"✓ Downloaded {len(df)} candles for {symbol} {timeframe} "
                       f"(from {df['time'].min()} to {df['time'].max()})")
            return df
            
        except Exception as e:
            error_msg = str(e)
            
            # Try to extract HTTP status code if available
            status_code = None
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                status_code = e.response.status_code
            elif hasattr(e, 'args') and len(e.args) > 0:
                # Try to find status code in error message
                import re
                match = re.search(r'(\d{3})', error_msg)
                if match:
                    status_code = int(match.group(1))
            
            # Detect specific error types with status codes
            if status_code == 429 or "429" in error_msg:
                logger.error(f"⚠️ RATE LIMIT [HTTP 429]: {symbol} {timeframe} - Yahoo Finance rate limit (429 Too Many Requests). Wait 5 minutes and use --workers 1")
                print(f"🚫 RATE LIMIT [429]: {symbol} - Too many requests!", flush=True)
            elif status_code == 404 or "404" in error_msg or "Not Found" in error_msg:
                logger.error(f"❌ NOT FOUND [HTTP 404]: {symbol} {timeframe} - Symbol not found on Yahoo Finance")
                print(f"❌ NOT FOUND [404]: {symbol} - Invalid symbol", flush=True)
            elif "Expecting value" in error_msg or "line 1 column 1" in error_msg:
                # This is likely rate limiting (empty response)
                logger.error(f"⚠️ RATE LIMIT (Empty Response): {symbol} {timeframe} - Got empty/invalid response. Likely rate limited. Use --workers 1")
                print(f"🚫 RATE LIMIT: {symbol} - Empty response (likely HTTP 429)", flush=True)
            elif "timeout" in error_msg.lower():
                logger.error(f"⏱️ TIMEOUT: {symbol} {timeframe} - Request timed out")
                print(f"⏱️ TIMEOUT: {symbol}", flush=True)
            elif "connection" in error_msg.lower():
                logger.error(f"🔌 CONNECTION: {symbol} {timeframe} - {error_msg}")
                print(f"🔌 CONNECTION ERROR: {symbol}", flush=True)
            else:
                logger.error(f"❌ ERROR: {symbol} {timeframe} - {error_msg}")
                print(f"❌ ERROR: {symbol} - {error_msg[:100]}", flush=True)
            
            # Log status code if found
            if status_code:
                logger.error(f"   HTTP Status Code: {status_code}")
                print(f"   Status: {status_code}", flush=True)
            
            return pd.DataFrame()
    
    def download_and_store(self, symbol: str, timeframe: str,
                          period: str = '1y') -> int:
        """
        Download historical data and store in database
        
        Returns:
            Number of rows inserted (duplicates are skipped)
        """
        df = self.download_historical(symbol, timeframe, period)
        
        if df.empty:
            return 0
        
        total_candles = len(df)
        rows_inserted = self.db.insert_ohlcv(symbol, timeframe, df)
        
        duplicates_skipped = total_candles - rows_inserted
        
        if duplicates_skipped > 0:
            logger.info(f"→ Inserted {rows_inserted} rows for {symbol} {timeframe} "
                       f"(skipped {duplicates_skipped} duplicates)")
        else:
            logger.info(f"→ Inserted {rows_inserted} rows for {symbol} {timeframe}")
        
        return rows_inserted
    
    def download_multiple_symbols(self, symbols: List[str], timeframe: str,
                                  period: str = '1y') -> dict:
        """
        Download data for multiple symbols
        
        Returns:
            Dictionary with symbol as key and number of rows inserted as value
        """
        results = {}
        
        for symbol in symbols:
            try:
                rows = self.download_and_store(symbol, timeframe, period)
                results[symbol] = rows
            except Exception as e:
                logger.error(f"Failed to download {symbol}: {e}")
                results[symbol] = 0
        
        return results
    
    def update_latest_data(self, symbol: str, timeframe: str, force: bool = False) -> int:
        """
        Update with latest data since last download
        
        Checks the latest timestamp in database and downloads only new data
        """
        latest_time = self.db.get_latest_timestamp(symbol, timeframe)
        
        if latest_time is None:
            # No data exists, download full history
            logger.info(f"No existing data for {symbol} {timeframe}, downloading full history")
            return self.download_and_store(symbol, timeframe, period='1y')
        
        # Get current time with timezone awareness
        import pytz
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        
        # Handle weekends and Monday pre-market - use Friday as last market day
        if now.weekday() == 5:  # Saturday
            now = now - timedelta(days=1)
        elif now.weekday() == 6:  # Sunday
            now = now - timedelta(days=2)
        elif now.weekday() == 0 and now.hour < 9:  # Monday before 9 AM
            now = now - timedelta(days=3)
        
        # Ensure latest_time is timezone-aware
        if latest_time.tzinfo is None:
            latest_time = ist.localize(latest_time)
        
        # Calculate days since last update
        days_since = (now - latest_time).days
        
        # Check if sync is needed (unless force=True)
        if not force and days_since < 1:
            logger.info(f"{symbol} {timeframe} is up to date (skipping sync)")
            return 0
        
        # Download recent data
        period = f"{min(days_since + 1, 30)}d"  # Max 30 days
        df = self.download_historical(symbol, timeframe, period)
        
        if df.empty:
            return 0
        
        # Filter only new data (make timezone-naive for comparison)
        latest_time_naive = latest_time.replace(tzinfo=None) if latest_time.tzinfo else latest_time
        df = df[df['time'] > latest_time_naive]
        
        if df.empty:
            logger.info(f"No new data for {symbol} {timeframe}")
            return 0
        
        rows_inserted = self.db.insert_ohlcv(symbol, timeframe, df)
        logger.info(f"Updated {symbol} {timeframe} with {rows_inserted} new candles")
        return rows_inserted


def download_nifty100_data(timeframes: List[str] = None,
                          period: str = '1y') -> dict:
    """
    Convenience function to download data for all Nifty 100 stocks
    
    Args:
        timeframes: List of timeframes to download (default: from config)
        period: Period to download
    
    Returns:
        Dictionary with results for each symbol and timeframe
    """
    from src.data.storage import InstrumentsDB
    
    if timeframes is None:
        timeframes = TradingConfig.DEFAULT_TIMEFRAMES
    
    # Get Nifty 100 symbols
    instruments_db = InstrumentsDB()
    symbols = instruments_db.get_nifty_100()
    
    logger.info(f"Downloading data for {len(symbols)} symbols across {len(timeframes)} timeframes")
    
    downloader = YFinanceDownloader()
    results = {}
    
    for timeframe in timeframes:
        logger.info(f"Downloading {timeframe} data...")
        results[timeframe] = downloader.download_multiple_symbols(symbols, timeframe, period)
    
    return results
