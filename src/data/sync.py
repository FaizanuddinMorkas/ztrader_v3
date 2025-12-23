"""
Data synchronization class for managing OHLCV data downloads and updates
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.data.downloader import YFinanceDownloader
from src.data.storage import InstrumentsDB, OHLCVDB
from src.config.settings import DataConfig, TradingConfig
from src.utils.logger import setup_logger

logger = setup_logger('data_sync')


class DataSync:
    """
    Manages data synchronization for OHLCV data
    
    Features:
    - Initial bulk download for new symbols
    - Incremental updates for existing data
    - Multi-threaded downloads for performance
    - Progress tracking and error handling
    """
    
    def __init__(self, max_workers: int = None):
        """
        Initialize DataSync
        
        Args:
            max_workers: Number of parallel download threads (default: from config)
        """
        self.downloader = YFinanceDownloader()
        self.instruments_db = InstrumentsDB()
        self.ohlcv_db = OHLCVDB()
        self.max_workers = max_workers or DataConfig.YFINANCE_MAX_WORKERS
    
    def sync_symbol(self, symbol: str, timeframe: str, full_download: bool = True, period: str = '5y', force: bool = False) -> dict:
        """
        Sync data for a single symbol and timeframe
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            timeframe: Timeframe ('1m', '5m', '15m', '1h', '1d')
            full_download: If True, download full history; else incremental update
        
        Returns:
            Dictionary with sync results
        """
        try:
            # Create new downloader instance for this thread to avoid connection conflicts
            downloader = YFinanceDownloader()
            
            if full_download:
                # Full download with custom period
                period = self._get_period_for_timeframe(timeframe)
                rows = downloader.download_and_store(symbol, timeframe, period=period)
                return {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'status': 'success',
                    'rows': rows,
                    'type': 'full'
                }
            else:
                # Incremental update
                rows = downloader.update_latest_data(symbol, timeframe, force=force)
                return {
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'status': 'success',
                    'rows': rows,
                    'type': 'incremental'
                }
        except Exception as e:
            error_msg = str(e)
            
            # Categorize error
            if "rate limit" in error_msg.lower() or "expecting value" in error_msg.lower():
                error_type = "RATE_LIMIT"
            elif "not found" in error_msg.lower() or "404" in error_msg:
                error_type = "NOT_FOUND"
            elif "timeout" in error_msg.lower():
                error_type = "TIMEOUT"
            elif "connection" in error_msg.lower():
                error_type = "CONNECTION"
            else:
                error_type = "OTHER"
            
            logger.error(f"[{error_type}] Error syncing {symbol} {timeframe}: {error_msg}")
            
            return {
                'symbol': symbol,
                'timeframe': timeframe,
                'status': 'error',
                'error': error_msg,
                'error_type': error_type,
                'rows': 0
            }
    
    def sync_all_symbols(self, timeframes: List[str] = None,
                        symbols: List[str] = None,
                        full_download: bool = False, period: str = '5y', force: bool = False) -> Dict:
        """
        Sync data for multiple symbols and timeframes
        
        Args:
            timeframes: List of timeframes (default: from config)
            symbols: List of symbols (default: all Nifty 100)
            full_download: If True, download full history
            period: Period to download (e.g., '5y', '2y', 'max')
        
        Returns:
            Dictionary with overall sync results
        """
        if timeframes is None:
            timeframes = TradingConfig.DEFAULT_TIMEFRAMES
        
        if symbols is None:
            # Get all active instruments (not just Nifty 100)
            instruments_df = self.instruments_db.get_all_active()
            symbols = instruments_df['symbol'].tolist()
        
        logger.info(f"Starting sync for {len(symbols)} symbols across {len(timeframes)} timeframes")
        logger.info(f"Mode: {'Full download' if full_download else 'Incremental update'}")
        
        results = {
            'total_symbols': len(symbols),
            'total_timeframes': len(timeframes),
            'total_tasks': len(symbols) * len(timeframes),
            'successful': 0,
            'failed': 0,
            'total_rows': 0,
            'details': [],
            'start_time': datetime.now(),
            'end_time': None
        }
        
        # Create tasks
        tasks = [
            (symbol, timeframe, full_download)
            for symbol in symbols
            for timeframe in timeframes
        ]
        
        # Execute in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.sync_symbol, symbol, tf, full_download, period, force): (symbol, tf)
                for symbol in symbols
                for tf in timeframes
            }
            completed = 0
            start_time = datetime.now()
            
            for future in as_completed(futures):
                result = future.result()
                results['details'].append(result)
                
                if result['status'] == 'success':
                    results['successful'] += 1
                    results['total_rows'] += result['rows']
                else:
                    results['failed'] += 1
                
                completed += 1
                
                # Progress logging every symbol (more detailed)
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = completed / elapsed if elapsed > 0 else 0
                remaining = results['total_tasks'] - completed
                eta_seconds = remaining / rate if rate > 0 else 0
                
                # Immediate console output (not buffered)
                progress_msg = (
                    f"[{completed}/{results['total_tasks']}] "
                    f"{result['symbol']:20s} {result['timeframe']:5s} - "
                    f"{'✓' if result['status'] == 'success' else '✗'} "
                    f"{result['rows']:5d} rows | "
                    f"Progress: {(completed/results['total_tasks']*100):5.1f}% | "
                    f"ETA: {int(eta_seconds//60)}m {int(eta_seconds%60)}s"
                )
                
                # Print to console immediately
                print(progress_msg, flush=True)
                
                # Also log
                logger.info(progress_msg)
        
        results['end_time'] = datetime.now()
        results['duration'] = (results['end_time'] - results['start_time']).total_seconds()
        
        logger.info(f"Sync completed: {results['successful']} successful, {results['failed']} failed")
        logger.info(f"Total rows inserted: {results['total_rows']}")
        logger.info(f"Duration: {results['duration']:.2f} seconds")
        
        return results
    
    def sync_timeframe(self, timeframe: str, symbols: List[str] = None,
                      full_download: bool = False, period: str = '5y') -> Dict:
        """
        Sync data for a specific timeframe across all symbols
        
        Args:
            timeframe: Timeframe to sync
            symbols: List of symbols (default: all Nifty 100)
            full_download: If True, download full history
        
        Returns:
            Dictionary with sync results
        """
        return self.sync_all_symbols(
            timeframes=[timeframe],
            symbols=symbols,
            full_download=full_download,
            period=period
        )
    
    def get_sync_status(self, symbols: List[str] = None) -> pd.DataFrame:
        """
        Get current sync status for symbols
        
        Args:
            symbols: List of symbols to check (default: all Nifty 100)
        
        Returns:
            DataFrame with sync status
        """
        if symbols is None:
            # Get all active instruments (not just Nifty 100)
            instruments_df = self.instruments_db.get_all_active()
            symbols = instruments_df['symbol'].tolist()
        
        status_data = []
        
        for symbol in symbols:
            for timeframe in TradingConfig.DEFAULT_TIMEFRAMES:
                latest_time = self.ohlcv_db.get_latest_timestamp(symbol, timeframe)
                
                status_data.append({
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'latest_data': latest_time,
                    'days_old': (datetime.now() - latest_time).days if latest_time else None,
                    'needs_update': self._needs_update(latest_time, timeframe)
                })
        
        return pd.DataFrame(status_data)
    
    def _get_period_for_timeframe(self, timeframe: str) -> str:
        """Get appropriate download period for timeframe"""
        period_map = {
            '1m': '7d',    # yfinance limit
            '5m': '60d',
            '15m': '60d',
            '30m': '60d',
            '1h': '730d',  # 2 years
            '1d': 'max',   # All available
            '1w': 'max'
        }
        return period_map.get(timeframe, '1y')
    
    def _needs_update(self, latest_time: Optional[datetime], timeframe: str) -> bool:
        """Check if data needs update based on latest timestamp"""
        if latest_time is None:
            return True
        
        # Update thresholds
        thresholds = {
            '1m': timedelta(hours=1),
            '5m': timedelta(hours=2),
            '15m': timedelta(hours=4),
            '30m': timedelta(hours=6),
            '1h': timedelta(days=1),
            '1d': timedelta(days=1),
            '1w': timedelta(days=7)
        }
        
        threshold = thresholds.get(timeframe, timedelta(days=1))
        return (datetime.now() - latest_time) > threshold
