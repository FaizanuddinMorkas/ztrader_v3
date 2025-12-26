"""
Fetch all NSE stocks and insert into instruments table

This script:
1. Downloads the complete list of NSE equity stocks from NSE India website
2. Validates symbols using yfinance
3. Inserts them into the instruments database
"""

import requests
import pandas as pd
import yfinance as yf
import logging
from typing import List, Dict
import time
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.data.storage import InstrumentsDB
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class NSEStockFetcher:
    """Fetch all NSE stocks from NSE India website"""
    
    # NSE India API endpoint for equity list
    NSE_EQUITY_URL = "https://www.nseindia.com/api/equity-stockIndices?index=SECURITIES%20IN%20F%26O"
    NSE_ALL_STOCKS_URL = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500"
    NSE_EQUITY_LIST_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    
    def __init__(self):
        self.instruments_db = InstrumentsDB()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def fetch_from_nse_csv(self) -> pd.DataFrame:
        """
        Fetch stock list from NSE CSV file
        
        Returns:
            DataFrame with columns: symbol, name, series, isin
        """
        logger.info("Fetching NSE equity list from CSV...")
        
        try:
            # First, visit NSE homepage to get cookies
            self.session.get("https://www.nseindia.com", timeout=10)
            time.sleep(2)
            
            # Download the CSV
            response = self.session.get(self.NSE_EQUITY_LIST_URL, timeout=30)
            response.raise_for_status()
            
            # Parse CSV
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            
            # Strip whitespace from column names
            df.columns = df.columns.str.strip()
            
            logger.info(f"Fetched {len(df)} stocks from NSE CSV")
            logger.info(f"Columns: {df.columns.tolist()}")
            
            # Filter for equity stocks (EQ series)
            df = df[df['SERIES'] == 'EQ'].copy()
            
            # Rename columns
            df = df.rename(columns={
                'SYMBOL': 'symbol',
                'NAME OF COMPANY': 'name',
                'SERIES': 'series',
                'ISIN NUMBER': 'isin'
            })
            
            # Clean up
            df['symbol'] = df['symbol'].str.strip()
            df['name'] = df['name'].str.strip()
            
            logger.info(f"Filtered to {len(df)} equity stocks (EQ series)")
            
            return df[['symbol', 'name', 'isin']]
            
        except Exception as e:
            logger.error(f"Error fetching from NSE CSV: {e}")
            return pd.DataFrame()
    
    def fetch_from_nifty_indices(self) -> pd.DataFrame:
        """
        Fetch stocks from Nifty indices as fallback
        
        Returns:
            DataFrame with symbol and name
        """
        logger.info("Fetching from Nifty indices as fallback...")
        
        all_stocks = []
        indices = [
            "NIFTY 50",
            "NIFTY NEXT 50",
            "NIFTY MIDCAP 50",
            "NIFTY MIDCAP 100",
            "NIFTY SMALLCAP 100",
            "NIFTY 500"
        ]
        
        for index in indices:
            try:
                # Visit homepage first
                self.session.get("https://www.nseindia.com", timeout=10)
                time.sleep(1)
                
                url = f"https://www.nseindia.com/api/equity-stockIndices?index={index.replace(' ', '%20')}"
                response = self.session.get(url, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    stocks = data.get('data', [])
                    
                    for stock in stocks:
                        if stock.get('symbol'):
                            all_stocks.append({
                                'symbol': stock['symbol'],
                                'name': stock.get('meta', {}).get('companyName', stock['symbol']),
                                'index': index
                            })
                    
                    logger.info(f"Fetched {len(stocks)} stocks from {index}")
                    time.sleep(2)  # Rate limiting
                    
            except Exception as e:
                logger.warning(f"Error fetching {index}: {e}")
                continue
        
        if all_stocks:
            df = pd.DataFrame(all_stocks)
            # Remove duplicates
            df = df.drop_duplicates(subset=['symbol'])
            logger.info(f"Total unique stocks from indices: {len(df)}")
            return df
        
        return pd.DataFrame()
    
    def validate_symbol_with_yfinance(self, symbol: str) -> Dict:
        """
        Validate symbol with yfinance and get additional info
        
        Args:
            symbol: NSE symbol (without .NS suffix)
            
        Returns:
            Dict with validation result and info
        """
        try:
            ticker = yf.Ticker(f"{symbol}.NS")
            info = ticker.info
            
            # Check if valid
            if info and 'symbol' in info:
                return {
                    'valid': True,
                    'name': info.get('longName', info.get('shortName', symbol)),
                    'sector': info.get('sector'),
                    'industry': info.get('industry'),
                    'market_cap': info.get('marketCap')
                }
            else:
                return {'valid': False}
                
        except Exception as e:
            logger.debug(f"Validation failed for {symbol}: {e}")
            return {'valid': False}
    
    def batch_validate_symbols(self, symbols: List[str], batch_size: int = 50) -> List[Dict]:
        """
        Validate multiple symbols in batches
        
        Args:
            symbols: List of NSE symbols
            batch_size: Number of symbols to validate at once
            
        Returns:
            List of validated stock info
        """
        validated_stocks = []
        total = len(symbols)
        
        logger.info(f"Validating {total} symbols with yfinance...")
        
        for i in range(0, total, batch_size):
            batch = symbols[i:i+batch_size]
            
            for j, symbol in enumerate(batch, 1):
                try:
                    result = self.validate_symbol_with_yfinance(symbol)
                    
                    if result['valid']:
                        validated_stocks.append({
                            'symbol': f"{symbol}.NS",
                            'name': result['name'],
                            'sector': result.get('sector'),
                            'industry': result.get('industry')
                        })
                        logger.info(f"[{i+j}/{total}] ✅ {symbol}: {result['name']}")
                    else:
                        logger.debug(f"[{i+j}/{total}] ❌ {symbol}: Invalid")
                    
                    # Rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"[{i+j}/{total}] Error validating {symbol}: {e}")
            
            logger.info(f"Batch {i//batch_size + 1} complete. Validated: {len(validated_stocks)}")
        
        return validated_stocks
    
    def insert_stocks_to_db_batch(self, stocks: List[Dict], validate: bool = True, batch_size: int = 100) -> int:
        """
        Insert stocks into instruments database using batch COPY
        
        Args:
            stocks: List of stock dictionaries
            validate: Whether to validate with yfinance first
            batch_size: Number of stocks to insert per batch
            
        Returns:
            Number of stocks inserted
        """
        if validate:
            # Extract symbols (remove .NS if present)
            symbols = [s['symbol'].replace('.NS', '') for s in stocks]
            validated_stocks = self.batch_validate_symbols(symbols)
        else:
            validated_stocks = stocks
        
        if not validated_stocks:
            logger.warning("No stocks to insert")
            return 0
        
        logger.info(f"Inserting {len(validated_stocks)} stocks into database using batch COPY...")
        
        # Convert to DataFrame for batch insert
        df = pd.DataFrame(validated_stocks)
        
        # Ensure all required columns exist
        if 'sector' not in df.columns:
            df['sector'] = None
        if 'industry' not in df.columns:
            df['industry'] = None
        
        df['is_nifty_50'] = False
        df['is_nifty_100'] = False
        
        # Reorder columns to match database schema
        df = df[['symbol', 'name', 'sector', 'industry', 'is_nifty_50', 'is_nifty_100']]
        
        # Use COPY for batch insert
        from io import StringIO
        import psycopg2
        
        inserted = 0
        total_batches = (len(df) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min((batch_num + 1) * batch_size, len(df))
            batch_df = df.iloc[start_idx:end_idx]
            
            try:
                # Create temp table and use COPY
                with self.instruments_db.db.get_connection() as conn:
                    with conn.cursor() as cur:
                        # Create temp table
                        cur.execute("""
                            CREATE TEMP TABLE temp_instruments (
                                symbol VARCHAR(50),
                                name VARCHAR(255),
                                sector VARCHAR(100),
                                industry VARCHAR(100),
                                is_nifty_50 BOOLEAN,
                                is_nifty_100 BOOLEAN
                            ) ON COMMIT DROP
                        """)
                        
                        # Prepare CSV data
                        csv_buffer = StringIO()
                        batch_df.to_csv(csv_buffer, index=False, header=False, sep='\t')
                        csv_buffer.seek(0)
                        
                        # COPY to temp table
                        cur.copy_from(csv_buffer, 'temp_instruments', sep='\t', null='')
                        
                        # Insert from temp to main table with conflict handling
                        cur.execute("""
                            INSERT INTO instruments (symbol, name, sector, industry, is_nifty_50, is_nifty_100)
                            SELECT symbol, name, sector, industry, is_nifty_50, is_nifty_100
                            FROM temp_instruments
                            ON CONFLICT (symbol) DO UPDATE
                            SET name = EXCLUDED.name,
                                sector = COALESCE(EXCLUDED.sector, instruments.sector),
                                industry = COALESCE(EXCLUDED.industry, instruments.industry),
                                updated_at = NOW()
                        """)
                        
                        batch_inserted = cur.rowcount
                        inserted += batch_inserted
                        
                        conn.commit()
                        
                        logger.info(f"Batch {batch_num + 1}/{total_batches}: Inserted {batch_inserted} stocks (Total: {inserted})")
                        
            except Exception as e:
                logger.error(f"Error inserting batch {batch_num + 1}: {e}")
                continue
        
        logger.info(f"Successfully inserted/updated {inserted} stocks")
        return inserted


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fetch all NSE stocks and insert into database")
    parser.add_argument('--validate', action='store_true', 
                       help='Validate each symbol with yfinance (slower but more accurate)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of stocks to process (for testing)')
    parser.add_argument('--method', choices=['csv', 'indices', 'both'], default='csv',
                       help='Method to fetch stocks: csv (NSE CSV), indices (Nifty indices), or both')
    
    args = parser.parse_args()
    
    fetcher = NSEStockFetcher()
    all_stocks = []
    
    # Fetch stocks based on method
    if args.method in ['csv', 'both']:
        df_csv = fetcher.fetch_from_nse_csv()
        if not df_csv.empty:
            stocks_csv = df_csv.to_dict('records')
            # Add .NS suffix
            for stock in stocks_csv:
                stock['symbol'] = f"{stock['symbol']}.NS"
            all_stocks.extend(stocks_csv)
            logger.info(f"Added {len(stocks_csv)} stocks from CSV")
    
    if args.method in ['indices', 'both']:
        df_indices = fetcher.fetch_from_nifty_indices()
        if not df_indices.empty:
            stocks_indices = df_indices.to_dict('records')
            # Add .NS suffix
            for stock in stocks_indices:
                stock['symbol'] = f"{stock['symbol']}.NS"
            all_stocks.extend(stocks_indices)
            logger.info(f"Added {len(stocks_indices)} stocks from indices")
    
    if not all_stocks:
        logger.error("No stocks fetched. Exiting.")
        return
    
    # Remove duplicates
    seen = set()
    unique_stocks = []
    for stock in all_stocks:
        if stock['symbol'] not in seen:
            seen.add(stock['symbol'])
            unique_stocks.append(stock)
    
    logger.info(f"Total unique stocks: {len(unique_stocks)}")
    
    # Apply limit if specified
    if args.limit:
        unique_stocks = unique_stocks[:args.limit]
        logger.info(f"Limited to {args.limit} stocks for testing")
    
    # Insert into database
    inserted = fetcher.insert_stocks_to_db_batch(unique_stocks, validate=args.validate, batch_size=100)
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Summary:")
    logger.info(f"  Total stocks fetched: {len(unique_stocks)}")
    logger.info(f"  Successfully inserted: {inserted}")
    logger.info(f"{'='*50}")


if __name__ == "__main__":
    main()
