"""
Database connection and operations module
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
import pandas as pd

from src.config.settings import DatabaseConfig


class DatabaseConnection:
    """Manages PostgreSQL database connections"""
    
    def __init__(self):
        self.config = DatabaseConfig
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = psycopg2.connect(
            host=self.config.HOST,
            port=self.config.PORT,
            database=self.config.NAME,
            user=self.config.USER,
            password=self.config.PASSWORD
        )
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dicts"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.rowcount
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute a query multiple times with different parameters"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(query, params_list)
                return cur.rowcount
    
    def query_to_dataframe(self, query: str, params: tuple = None) -> pd.DataFrame:
        """Execute query and return results as pandas DataFrame"""
        with self.get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params)


class InstrumentsDB:
    """Database operations for instruments table"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def get_all_active(self) -> pd.DataFrame:
        """Get all active instruments"""
        query = """
            SELECT symbol, name, sector, industry, is_nifty_50, is_nifty_100
            FROM instruments
            WHERE is_active = true
            ORDER BY symbol
        """
        return self.db.query_to_dataframe(query)
    
    def get_nifty_100(self) -> List[str]:
        """Get list of Nifty 100 symbols"""
        query = """
            SELECT symbol FROM instruments
            WHERE is_nifty_100 = true AND is_active = true
            ORDER BY symbol
        """
        results = self.db.execute_query(query)
        return [row['symbol'] for row in results]
    
    def get_by_sector(self, sector: str) -> pd.DataFrame:
        """Get instruments by sector"""
        query = """
            SELECT symbol, name, industry
            FROM instruments
            WHERE sector = %s AND is_active = true
            ORDER BY symbol
        """
        return self.db.query_to_dataframe(query, (sector,))
    
    def insert_instrument(self, symbol: str, name: str, sector: str = None,
                         industry: str = None, is_nifty_50: bool = False,
                         is_nifty_100: bool = True) -> int:
        """Insert a new instrument"""
        query = """
            INSERT INTO instruments (symbol, name, sector, industry, is_nifty_50, is_nifty_100)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol) DO UPDATE
            SET name = EXCLUDED.name,
                sector = EXCLUDED.sector,
                industry = EXCLUDED.industry,
                is_nifty_50 = EXCLUDED.is_nifty_50,
                is_nifty_100 = EXCLUDED.is_nifty_100,
                updated_at = NOW()
        """
        return self.db.execute_update(query, (symbol, name, sector, industry, is_nifty_50, is_nifty_100))


class OHLCVDB:
    """Database operations for OHLCV data table"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def insert_ohlcv(self, symbol: str, timeframe: str, df: pd.DataFrame, batch_size: int = 10000) -> int:
        """
        Insert OHLCV data using COPY to temp table then INSERT (fast + handles duplicates)
        
        Args:
            symbol: Stock symbol
            timeframe: Timeframe
            df: DataFrame with columns: time, open, high, low, close, volume
            batch_size: Number of rows per batch (default: 10000)
        
        Returns:
            Total number of rows inserted
        """
        import io
        
        if df.empty:
            return 0
        
        # Prepare data
        df_copy = df.copy()
        df_copy['symbol'] = symbol
        df_copy['timeframe'] = timeframe
        df_copy = df_copy[['time', 'symbol', 'timeframe', 'open', 'high', 'low', 'close', 'volume']]
        
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Create temp table
                cur.execute("""
                    CREATE TEMP TABLE temp_ohlcv (
                        time TIMESTAMPTZ,
                        symbol TEXT,
                        timeframe TEXT,
                        open NUMERIC,
                        high NUMERIC,
                        low NUMERIC,
                        close NUMERIC,
                        volume BIGINT
                    ) ON COMMIT DROP
                """)
                
                # Use COPY to load into temp table (super fast)
                buffer = io.StringIO()
                df_copy.to_csv(buffer, index=False, header=False, sep='\t')
                buffer.seek(0)
                
                cur.copy_expert(
                    "COPY temp_ohlcv FROM STDIN WITH (FORMAT CSV, DELIMITER E'\\t')",
                    buffer
                )
                
                # Insert from temp to main table with conflict handling
                cur.execute("""
                    INSERT INTO ohlcv_data (time, symbol, timeframe, open, high, low, close, volume)
                    SELECT time, symbol, timeframe, open, high, low, close, volume
                    FROM temp_ohlcv
                    ON CONFLICT (time, symbol, timeframe) DO NOTHING
                """)
                
                rows_inserted = cur.rowcount
        
        return rows_inserted
    
    def get_ohlcv(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        """
        Get OHLCV data for a symbol and timeframe
        
        Args:
            symbol: Stock symbol
            timeframe: Timeframe
            limit: Number of candles to fetch (default: 100)
        """
        query = """
            SELECT time, open, high, low, close, volume
            FROM ohlcv_data
            WHERE symbol = %s AND timeframe = %s
            ORDER BY time DESC
            LIMIT %s
        """
        df = self.db.query_to_dataframe(query, (symbol, timeframe, limit))
        if not df.empty:
            df = df.sort_values('time').reset_index(drop=True)
            df['time'] = pd.to_datetime(df['time'])
        return df
    
    def get_ohlcv_range(self, symbol: str, timeframe: str,
                       start_date: str, end_date: str) -> pd.DataFrame:
        """Get OHLCV data for a date range"""
        query = """
            SELECT time, open, high, low, close, volume
            FROM ohlcv_data
            WHERE symbol = %s AND timeframe = %s
              AND time >= %s AND time <= %s
            ORDER BY time ASC
        """
        df = self.db.query_to_dataframe(query, (symbol, timeframe, start_date, end_date))
        if not df.empty:
            df['time'] = pd.to_datetime(df['time'])
        return df
    
    def get_latest_timestamp(self, symbol: str, timeframe: str) -> Optional[pd.Timestamp]:
        """Get the latest timestamp for a symbol/timeframe"""
        query = """
            SELECT MAX(time) as latest_time
            FROM ohlcv_data
            WHERE symbol = %s AND timeframe = %s
        """
        result = self.db.execute_query(query, (symbol, timeframe))
        if result and result[0]['latest_time']:
            return pd.to_datetime(result[0]['latest_time'])
        return None


class FundamentalsDB:
    """Database operations for fundamentals table"""
    
    def __init__(self):
        self.db = DatabaseConnection()
    
    def upsert_fundamentals(self, fundamentals: Dict[str, Any]) -> int:
        """
        Insert or update fundamental data for a symbol
        
        Args:
            fundamentals: Dictionary with fundamental data
            
        Returns:
            Number of rows affected
        """
        import json
        
        # Extract symbol
        symbol = fundamentals.get('symbol')
        if not symbol:
            raise ValueError("Symbol is required")
        
        # Convert raw_data dict to JSON string
        raw_data = fundamentals.get('raw_data', {})
        if isinstance(raw_data, dict):
            raw_data_json = json.dumps(raw_data)
        else:
            raw_data_json = raw_data
        
        # Build column names and values
        columns = []
        values = []
        
        for key, value in fundamentals.items():
            if key == 'raw_data':
                columns.append('raw_data')
                values.append(raw_data_json)
            elif key != 'symbol':
                columns.append(key)
                values.append(value)
        
        # Build INSERT ... ON CONFLICT UPDATE query
        cols_str = ', '.join(['symbol'] + columns)
        placeholders = ', '.join(['%s'] * (len(columns) + 1))
        
        # Build UPDATE clause
        update_cols = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns])
        
        query = f"""
            INSERT INTO fundamentals ({cols_str})
            VALUES ({placeholders})
            ON CONFLICT (symbol) DO UPDATE SET
                {update_cols}
        """
        
        params = tuple([symbol] + values)
        
        return self.db.execute_update(query, params)
    
    def get_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get fundamental data for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with fundamental data, or None if not found
        """
        query = "SELECT * FROM fundamentals WHERE symbol = %s"
        results = self.db.execute_query(query, (symbol,))
        
        if results:
            return dict(results[0])
        return None
    
    def get_all_fundamentals(self) -> pd.DataFrame:
        """Get fundamental data for all symbols"""
        query = """
            SELECT symbol, updated_at, current_price, market_cap, trailing_pe,
                   price_to_book, return_on_equity, profit_margins,
                   revenue_growth, earnings_growth, dividend_yield,
                   sector, industry, beta
            FROM fundamentals
            ORDER BY symbol
        """
        return self.db.query_to_dataframe(query)
    
    def screen_by_criteria(self, 
                          min_market_cap: Optional[float] = None,
                          max_pe: Optional[float] = None,
                          min_roe: Optional[float] = None,
                          sector: Optional[str] = None) -> pd.DataFrame:
        """
        Screen stocks by fundamental criteria
        
        Args:
            min_market_cap: Minimum market cap
            max_pe: Maximum PE ratio
            min_roe: Minimum ROE
            sector: Sector filter
            
        Returns:
            DataFrame with matching stocks
        """
        conditions = []
        params = []
        
        if min_market_cap:
            conditions.append("market_cap >= %s")
            params.append(min_market_cap)
        
        if max_pe:
            conditions.append("trailing_pe <= %s AND trailing_pe > 0")
            params.append(max_pe)
        
        if min_roe:
            conditions.append("return_on_equity >= %s")
            params.append(min_roe)
        
        if sector:
            conditions.append("sector = %s")
            params.append(sector)
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT symbol, current_price, market_cap, trailing_pe,
                   price_to_book, return_on_equity, sector, industry
            FROM fundamentals
            WHERE {where_clause}
            ORDER BY market_cap DESC
        """
        
        return self.db.query_to_dataframe(query, tuple(params) if params else None)
    
    def get_sector_summary(self) -> pd.DataFrame:
        """Get summary statistics by sector"""
        query = """
            SELECT 
                sector,
                COUNT(*) as count,
                AVG(trailing_pe) as avg_pe,
                AVG(price_to_book) as avg_pb,
                AVG(return_on_equity) as avg_roe,
                AVG(profit_margins) as avg_profit_margin
            FROM fundamentals
            WHERE sector IS NOT NULL
            GROUP BY sector
            ORDER BY count DESC
        """
        return self.db.query_to_dataframe(query)
