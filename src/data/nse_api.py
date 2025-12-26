"""
NSE India API Client

Provides access to all NSE India public APIs for market data, top movers,
sectoral indices, and more.

Usage:
    from src.data.nse_api import NSEClient
    
    client = NSEClient()
    gainers = client.get_top_gainers(limit=10)
    sector_perf = client.get_sector_performance()
"""

import requests
import pandas as pd
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class NSEClient:
    """Client for NSE India public APIs"""
    
    BASE_URL = "https://www.nseindia.com"
    API_BASE = f"{BASE_URL}/api"
    
    # Sectoral indices available on NSE
    SECTORAL_INDICES = [
        "NIFTY BANK",
        "NIFTY IT", 
        "NIFTY PHARMA",
        "NIFTY AUTO",
        "NIFTY METAL",
        "NIFTY ENERGY",
        "NIFTY FMCG",
        "NIFTY REALTY",
        "NIFTY MEDIA",
        "NIFTY PSU BANK",
        "NIFTY PRIVATE BANK",
        "NIFTY FINANCIAL SERVICES",
        "NIFTY HEALTHCARE",
        "NIFTY CONSUMER DURABLES",
        "NIFTY OIL AND GAS",
        "NIFTY COMMODITIES"
    ]
    
    def __init__(self, cache_ttl: int = 300):
        """
        Initialize NSE API client
        
        Args:
            cache_ttl: Cache time-to-live in seconds (default: 300 = 5 minutes)
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        self.cache = {}
        self.cache_ttl = cache_ttl
        self.last_request_time = 0
        self.min_request_interval = 1.5  # seconds
        
        # Initialize session with cookies
        self._init_session()
    
    def _init_session(self):
        """Initialize session by visiting homepage to get cookies"""
        try:
            self.session.get(self.BASE_URL, timeout=10)
            time.sleep(1)
            logger.debug("NSE session initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize NSE session: {e}")
    
    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _get_from_cache(self, key: str) -> Optional[any]:
        """Get data from cache if not expired"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit: {key}")
                return data
        return None
    
    def _set_cache(self, key: str, value: any):
        """Set data in cache"""
        self.cache[key] = (value, time.time())
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None, use_cache: bool = True) -> Dict:
        """
        Make API request with caching and rate limiting
        
        Args:
            endpoint: API endpoint (e.g., '/live-analysis-variations')
            params: Query parameters
            use_cache: Whether to use cache
            
        Returns:
            JSON response as dictionary
        """
        cache_key = f"{endpoint}_{params}"
        
        # Check cache
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached is not None:
                return cached
        
        # Rate limit
        self._rate_limit()
        
        # Make request
        url = f"{self.API_BASE}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Cache response
            if use_cache:
                self._set_cache(cache_key, data)
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"NSE API request failed: {url} - {e}")
            raise
    
    # ============================================================================
    # Top Movers APIs
    # ============================================================================
    
    def get_top_gainers(self, limit: int = 10, index: str = None) -> pd.DataFrame:
        """
        Get top gaining stocks
        
        Args:
            limit: Number of stocks to return
            index: Filter by index (e.g., 'NIFTY', 'NIFTY500', 'BANKNIFTY', 'allSec')
                   If None, returns from all indices
            
        Returns:
            DataFrame with columns: symbol, ltp, perChange, open, high, low, volume, etc.
        """
        try:
            data = self._make_request('/live-analysis-variations', {'index': 'gainers'})
            
            # API returns data nested under category keys (NIFTY, BANKNIFTY, etc.)
            # Extract data from all categories or specific index
            all_stocks = []
            
            if index:
                # Get data from specific index only
                if index in data and isinstance(data[index], dict) and 'data' in data[index]:
                    stocks = data[index]['data']
                    if isinstance(stocks, list):
                        all_stocks.extend(stocks)
            else:
                # Get data from all indices
                for key, value in data.items():
                    if isinstance(value, dict) and 'data' in value:
                        stocks = value['data']
                        if isinstance(stocks, list):
                            all_stocks.extend(stocks)
            
            if not all_stocks:
                return pd.DataFrame()
            
            df = pd.DataFrame(all_stocks)
            
            if not df.empty:
                # Sort by percentage change and get top N
                if 'perChange' in df.columns:
                    df = df.sort_values('perChange', ascending=False)
                df = df.head(limit)
                
                # Add .NS suffix for consistency
                if 'symbol' in df.columns:
                    df['symbol'] = df['symbol'] + '.NS'
            
            return df
        except Exception as e:
            logger.error(f"Error fetching top gainers: {e}")
            return pd.DataFrame()
    
    def get_top_losers(self, limit: int = 10) -> pd.DataFrame:
        """
        Get top losing stocks
        
        Args:
            limit: Number of stocks to return
            
        Returns:
            DataFrame with columns: symbol, ltp, pChange, open, high, low, volume, etc.
        """
        try:
            data = self._make_request('/live-analysis-variations', {'index': 'losers'})
            
            # Extract data from all categories
            all_stocks = []
            for key, value in data.items():
                if isinstance(value, dict) and 'data' in value:
                    stocks = value['data']
                    if isinstance(stocks, list):
                        all_stocks.extend(stocks)
            
            if not all_stocks:
                return pd.DataFrame()
            
            df = pd.DataFrame(all_stocks)
            
            if not df.empty:
                if 'perChange' in df.columns:
                    df = df.sort_values('perChange', ascending=True)  # Ascending for losers
                df = df.head(limit)
                
                if 'symbol' in df.columns:
                    df['symbol'] = df['symbol'] + '.NS'
            
            return df
        except Exception as e:
            logger.error(f"Error fetching top losers: {e}")
            return pd.DataFrame()
    
    def get_most_active_by_volume(self, limit: int = 10) -> pd.DataFrame:
        """
        Get most active stocks by volume
        
        Note: NSE live-analysis API for volume doesn't work reliably.
        This method fetches Nifty 500 stocks and sorts by volume as a workaround.
        """
        try:
            # Workaround: Get all Nifty 500 stocks and sort by volume
            df = self.get_top_movers_from_index('NIFTY 500', limit=500, sort_by='gainers')
            
            if df.empty:
                return pd.DataFrame()
            
            # Sort by volume
            if 'totalTradedVolume' in df.columns:
                df = df.sort_values('totalTradedVolume', ascending=False)
            elif 'volume' in df.columns:
                df = df.sort_values('volume', ascending=False)
            
            return df.head(limit)
            
        except Exception as e:
            logger.error(f"Error fetching most active by volume: {e}")
            return pd.DataFrame()
    
    def get_most_active_by_value(self, limit: int = 10) -> pd.DataFrame:
        """
        Get most active stocks by value (volume shockers)
        
        Note: NSE live-analysis API for value doesn't work reliably.
        This method fetches Nifty 500 stocks and sorts by traded value as a workaround.
        """
        try:
            # Workaround: Get all Nifty 500 stocks and sort by traded value
            df = self.get_top_movers_from_index('NIFTY 500', limit=500, sort_by='gainers')
            
            if df.empty:
                return pd.DataFrame()
            
            # Sort by traded value
            if 'totalTradedValue' in df.columns:
                df = df.sort_values('totalTradedValue', ascending=False)
            elif 'value' in df.columns:
                df = df.sort_values('value', ascending=False)
            
            return df.head(limit)
            
        except Exception as e:
            logger.error(f"Error fetching most active by value: {e}")
            return pd.DataFrame()
    
    def get_top_movers_from_index(self, index_name: str, limit: int = 10, sort_by: str = 'gainers') -> pd.DataFrame:
        """
        Get top gainers or losers from a specific index (e.g., Nifty 500, Nifty 50)
        
        Args:
            index_name: Index name (e.g., 'NIFTY 500', 'NIFTY 50', 'NIFTY BANK')
            limit: Number of stocks to return
            sort_by: 'gainers' for top gainers, 'losers' for top losers
            
        Returns:
            DataFrame with top movers from the index
        """
        try:
            data = self.get_index_data(index_name)
            
            if 'data' not in data or len(data['data']) <= 1:
                return pd.DataFrame()
            
            # First row is the index itself, rest are stocks
            stocks = data['data'][1:]
            df = pd.DataFrame(stocks)
            
            if not df.empty:
                # Sort by percentage change
                if 'pChange' in df.columns:
                    ascending = (sort_by == 'losers')
                    df = df.sort_values('pChange', ascending=ascending)
                
                df = df.head(limit)
                
                # Add .NS suffix
                if 'symbol' in df.columns:
                    df['symbol'] = df['symbol'] + '.NS'
            
            return df
        except Exception as e:
            logger.error(f"Error fetching top movers from {index_name}: {e}")
            return pd.DataFrame()
    
    def get_52week_high(self, limit: int = 10) -> pd.DataFrame:
        """
        Get stocks hitting 52-week high today
        
        Returns stocks where today's high price equals or exceeds their 52-week high.
        This matches the behavior of NSE website, Groww, and MoneyControl.
        """
        try:
            # Get all Nifty 500 stocks
            df = self.get_top_movers_from_index('NIFTY 500', limit=500, sort_by='gainers')
            
            if df.empty:
                return pd.DataFrame()
            
            # Filter stocks hitting 52-week high today
            # dayHigh should be >= yearHigh (or very close, within 0.5%)
            if 'dayHigh' in df.columns and 'yearHigh' in df.columns:
                # Stock is at 52W high if today's high is within 0.5% of year high
                df['at_52w_high'] = (df['dayHigh'] >= df['yearHigh'] * 0.995)
                df_filtered = df[df['at_52w_high']].copy()
                
                if not df_filtered.empty:
                    # Sort by percentage change (biggest gainers at 52W high first)
                    if 'pChange' in df_filtered.columns:
                        df_filtered = df_filtered.sort_values('pChange', ascending=False)
                    
                    # Drop the helper column
                    df_filtered = df_filtered.drop('at_52w_high', axis=1)
                    return df_filtered.head(limit)
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching 52-week high: {e}")
            return pd.DataFrame()
    
    def get_52week_low(self, limit: int = 10) -> pd.DataFrame:
        """
        Get stocks hitting 52-week low today
        
        Returns stocks where today's low price equals or is below their 52-week low.
        This matches the behavior of NSE website, Groww, and MoneyControl.
        """
        try:
            # Get all Nifty 500 stocks
            df = self.get_top_movers_from_index('NIFTY 500', limit=500, sort_by='gainers')
            
            if df.empty:
                return pd.DataFrame()
            
            # Filter stocks hitting 52-week low today
            # dayLow should be <= yearLow (or very close, within 0.5%)
            if 'dayLow' in df.columns and 'yearLow' in df.columns:
                # Stock is at 52W low if today's low is within 0.5% of year low
                df['at_52w_low'] = (df['dayLow'] <= df['yearLow'] * 1.005)
                df_filtered = df[df['at_52w_low']].copy()
                
                if not df_filtered.empty:
                    # Sort by percentage change (biggest losers at 52W low first)
                    if 'pChange' in df_filtered.columns:
                        df_filtered = df_filtered.sort_values('pChange', ascending=True)
                    
                    # Drop the helper column
                    df_filtered = df_filtered.drop('at_52w_low', axis=1)
                    return df_filtered.head(limit)
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching 52-week low: {e}")
            return pd.DataFrame()
    
    # ============================================================================
    # Sectoral Indices APIs
    # ============================================================================
    
    def get_sector_index(self, sector: str) -> Dict:
        """
        Get sector index data
        
        Args:
            sector: Sector name (e.g., 'NIFTY BANK', 'NIFTY IT')
            
        Returns:
            Dictionary with index data and constituent stocks
        """
        data = self._make_request('/equity-stockIndices', {'index': sector})
        return data
    
    def get_sector_performance(self) -> pd.DataFrame:
        """
        Get performance of all sectoral indices
        
        Returns:
            DataFrame with columns: sector, last, pChange, open, high, low
        """
        sectors_data = []
        
        for sector in self.SECTORAL_INDICES:
            try:
                data = self.get_sector_index(sector)
                
                if 'data' in data and len(data['data']) > 0:
                    # First row is the index itself
                    index_data = data['data'][0]
                    sectors_data.append({
                        'sector': sector,
                        'last': index_data.get('last', 0),
                        'pChange': index_data.get('pChange', 0),
                        'open': index_data.get('open', 0),
                        'high': index_data.get('high', 0),
                        'low': index_data.get('low', 0),
                        'yearHigh': index_data.get('yearHigh', 0),
                        'yearLow': index_data.get('yearLow', 0),
                    })
                
                time.sleep(0.5)  # Small delay between sector requests
                
            except Exception as e:
                logger.warning(f"Failed to fetch {sector}: {e}")
                continue
        
        df = pd.DataFrame(sectors_data)
        if not df.empty:
            df = df.sort_values('pChange', ascending=False)
        
        return df
    
    def get_sector_stocks(self, sector: str) -> pd.DataFrame:
        """
        Get all stocks in a sector with their performance
        
        Args:
            sector: Sector name (e.g., 'NIFTY BANK')
            
        Returns:
            DataFrame with stock data
        """
        data = self.get_sector_index(sector)
        
        if 'data' in data and len(data['data']) > 1:
            # Skip first row (index itself), rest are stocks
            stocks = data['data'][1:]
            df = pd.DataFrame(stocks)
            
            if not df.empty:
                df['symbol'] = df['symbol'] + '.NS'
                df = df.sort_values('pChange', ascending=False)
            
            return df
        
        return pd.DataFrame()
    
    # ============================================================================
    # Market Overview APIs
    # ============================================================================
    
    def get_market_status(self) -> Dict:
        """Get current market status"""
        return self._make_request('/marketStatus')
    
    def get_all_indices(self) -> pd.DataFrame:
        """Get all NSE indices"""
        data = self._make_request('/allIndices')
        return pd.DataFrame(data.get('data', []))
    
    def get_index_data(self, index: str = 'NIFTY 50') -> Dict:
        """
        Get specific index data
        
        Args:
            index: Index name (e.g., 'NIFTY 50', 'NIFTY BANK')
        """
        return self._make_request('/equity-stockIndices', {'index': index})
    
    # ============================================================================
    # Individual Stock APIs
    # ============================================================================
    
    def get_quote(self, symbol: str) -> Dict:
        """
        Get stock quote
        
        Args:
            symbol: Stock symbol without .NS suffix (e.g., 'RELIANCE')
        """
        symbol = symbol.replace('.NS', '')  # Remove .NS if present
        return self._make_request('/quote-equity', {'symbol': symbol})
    
    # ============================================================================
    # Utility Methods
    # ============================================================================
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache = {}
        logger.info("Cache cleared")
    
    def get_market_overview(self) -> Dict:
        """
        Get comprehensive market overview
        
        Returns:
            Dictionary with gainers, losers, active stocks, and sector performance
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'top_gainers': self.get_top_gainers(limit=10),
            'top_losers': self.get_top_losers(limit=10),
            'most_active_volume': self.get_most_active_by_volume(limit=10),
            'sector_performance': self.get_sector_performance(),
            'market_status': self.get_market_status()
        }
