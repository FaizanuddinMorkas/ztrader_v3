"""
Timeframe resampling utilities for custom candle generation
"""

import pandas as pd
from typing import Optional
from datetime import datetime
from dateutil.relativedelta import relativedelta

from src.data.storage import OHLCVDB
from src.utils.logger import setup_logger

logger = setup_logger('resample')


class TimeframeResampler:
    """
    Resample OHLCV data to custom timeframes
    
    Features:
    - Generate 75-minute candles from 15-minute data
    - Support for any custom timeframe
    - Proper OHLCV aggregation
    """
    
    def __init__(self):
        self.ohlcv_db = OHLCVDB()
    
    def resample_to_75m(self, symbol: str, start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Generate 75-minute candles from 15-minute data
        Fetches data in monthly batches to reduce memory usage
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            start_date: Optional start date
            end_date: Optional end date
        
        Returns:
            DataFrame with 75-minute OHLCV data
        """
        from datetime import timedelta
        from dateutil.relativedelta import relativedelta
        
        # Set default date range if not provided
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - relativedelta(years=1)  # 1 year of data
        
        all_75m_data = []
        
        # Process data in monthly batches to reduce memory usage
        current_start = start_date
        while current_start < end_date:
            current_end = min(current_start + relativedelta(months=1), end_date)
            
            # Fetch 15m data for this month
            query = """
                SELECT time, open, high, low, close, volume
                FROM ohlcv_data
                WHERE symbol = %s AND timeframe = '15m'
                  AND time >= %s AND time < %s
                ORDER BY time
            """
            
            df_month = self.ohlcv_db.db.query_to_dataframe(
                query, 
                (symbol, current_start, current_end)
            )
            
            if not df_month.empty:
                # Set time as index for resampling
                df_month.set_index('time', inplace=True)
                
                # Resample to 75 minutes
                df_75m_month = df_month.resample('75min').agg({
                    'open': 'first',
                    'high': 'max',
                    'low': 'min',
                    'close': 'last',
                    'volume': 'sum'
                })
                
                # Remove rows with NaN (incomplete candles)
                df_75m_month.dropna(inplace=True)
                
                # Convert volume to integer (PostgreSQL bigint)
                df_75m_month['volume'] = df_75m_month['volume'].astype('int64')
                
                # Reset index
                df_75m_month.reset_index(inplace=True)
                
                all_75m_data.append(df_75m_month)
            
            # Move to next month
            current_start = current_end
        
        # Combine all monthly data
        if all_75m_data:
            df_75m = pd.concat(all_75m_data, ignore_index=True)
            logger.info(f"Generated {len(df_75m)} 75-minute candles for {symbol}")
            return df_75m
        else:
            logger.warning(f"No 15m data found for {symbol}")
            return pd.DataFrame()
    
    def resample_to_custom(self, symbol: str, source_timeframe: str,
                          target_minutes: int, start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Resample to any custom timeframe
        
        Args:
            symbol: Stock symbol
            source_timeframe: Source timeframe (e.g., '15m', '5m')
            target_minutes: Target timeframe in minutes (e.g., 75, 90, 45)
            start_date: Optional start date
            end_date: Optional end date
        
        Returns:
            DataFrame with custom timeframe OHLCV data
        """
        # Fetch source data
        query = """
            SELECT time, open, high, low, close, volume
            FROM ohlcv_data
            WHERE symbol = %s AND timeframe = %s
        """
        params = [symbol, source_timeframe]
        
        if start_date:
            query += " AND time >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND time <= %s"
            params.append(end_date)
        
        query += " ORDER BY time"
        
        df = self.ohlcv_db.db.query_to_dataframe(query, tuple(params))
        
        if df.empty:
            logger.warning(f"No {source_timeframe} data found for {symbol}")
            return pd.DataFrame()
        
        # Set time as index
        df.set_index('time', inplace=True)
        
        # Resample to custom timeframe
        df_custom = df.resample(f'{target_minutes}T').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        })
        
        # Remove incomplete candles
        df_custom.dropna(inplace=True)
        
        # Convert volume to integer
        df_custom['volume'] = df_custom['volume'].astype('int64')
        
        # Reset index
        df_custom.reset_index(inplace=True)
        
        logger.info(f"Generated {len(df_custom)} {target_minutes}-minute candles for {symbol}")
        
        return df_custom
    
    def store_75m_data(self, symbol: str, start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> int:
        """
        Generate and store 75-minute candles in database
        
        Args:
            symbol: Stock symbol
            start_date: Optional start date
            end_date: Optional end date
        
        Returns:
            Number of rows inserted
        """
        # Generate 75m candles
        df_75m = self.resample_to_75m(symbol, start_date, end_date)
        
        if df_75m.empty:
            return 0
        
        # Store in database
        rows = self.ohlcv_db.insert_ohlcv(symbol, '75m', df_75m)
        
        logger.info(f"Stored {rows} 75-minute candles for {symbol}")
        
        return rows


def generate_75m_for_all_symbols():
    """
    Generate 75-minute candles for all Nifty 100 symbols
    """
    from src.data.storage import InstrumentsDB
    import time
    
    instruments_db = InstrumentsDB()
    resampler = TimeframeResampler()
    
    symbols = instruments_db.get_nifty_100()
    
    total_rows = 0
    successful = 0
    failed = 0
    
    for i, symbol in enumerate(symbols, 1):
        try:
            print(f"[{i}/{len(symbols)}] Generating 75m candles for {symbol}...", flush=True)
            rows = resampler.store_75m_data(symbol)
            total_rows += rows
            successful += 1
            print(f"  ✓ {rows} candles generated", flush=True)
            
            # Add delay to prevent database overload
            time.sleep(0.5)
            
        except Exception as e:
            failed += 1
            print(f"  ✗ Error: {e}", flush=True)
            logger.error(f"Error generating 75m for {symbol}: {e}")
            
            # Add longer delay after error
            time.sleep(1.0)
    
    print(f"\n{'='*80}")
    print(f"75-Minute Candle Generation Complete")
    print(f"{'='*80}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total candles: {total_rows}")
    print(f"{'='*80}")


if __name__ == "__main__":
    # Generate 75m candles for all symbols
    generate_75m_for_all_symbols()
