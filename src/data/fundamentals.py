"""
Fundamentals data downloader using yfinance

Fetches fundamental data (PE ratio, market cap, etc.) for stocks
"""

import yfinance as yf
import pandas as pd
import logging
from typing import Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class FundamentalsDownloader:
    """
    Download fundamental data from yfinance
    
    Fetches company info, valuation metrics, profitability, growth, etc.
    """
    
    # Fields to extract from yfinance info
    FIELD_MAPPING = {
        # Price Metrics
        'currentPrice': 'current_price',
        'previousClose': 'previous_close',
        'open': 'open',
        'dayLow': 'day_low',
        'dayHigh': 'day_high',
        'fiftyTwoWeekLow': 'fifty_two_week_low',
        'fiftyTwoWeekHigh': 'fifty_two_week_high',
        'fiftyDayAverage': 'fifty_day_average',
        'twoHundredDayAverage': 'two_hundred_day_average',
        
        # Valuation Ratios
        'marketCap': 'market_cap',
        'enterpriseValue': 'enterprise_value',
        'trailingPE': 'trailing_pe',
        'forwardPE': 'forward_pe',
        'priceToBook': 'price_to_book',
        'priceToSalesTrailing12Months': 'price_to_sales',
        'pegRatio': 'peg_ratio',
        'enterpriseToRevenue': 'enterprise_to_revenue',
        'enterpriseToEbitda': 'enterprise_to_ebitda',
        
        # Profitability
        'profitMargins': 'profit_margins',
        'grossMargins': 'gross_margins',
        'ebitdaMargins': 'ebitda_margins',
        'operatingMargins': 'operating_margins',
        'returnOnEquity': 'return_on_equity',
        'returnOnAssets': 'return_on_assets',
        
        # Growth
        'revenueGrowth': 'revenue_growth',
        'earningsGrowth': 'earnings_growth',
        'earningsQuarterlyGrowth': 'earnings_quarterly_growth',
        'revenueQuarterlyGrowth': 'revenue_quarterly_growth',
        
        # Financial Health
        'totalCash': 'total_cash',
        'totalDebt': 'total_debt',
        'totalRevenue': 'total_revenue',
        'debtToEquity': 'debt_to_equity',
        'currentRatio': 'current_ratio',
        'quickRatio': 'quick_ratio',
        'bookValue': 'book_value',
        'revenuePerShare': 'revenue_per_share',
        'totalCashPerShare': 'total_cash_per_share',
        
        # Dividends
        'dividendRate': 'dividend_rate',
        'dividendYield': 'dividend_yield',
        'payoutRatio': 'payout_ratio',
        'fiveYearAvgDividendYield': 'five_year_avg_dividend_yield',
        
        # Volume & Liquidity
        'volume': 'volume',
        'averageVolume': 'average_volume',
        'averageVolume10days': 'average_volume_10days',
        'bid': 'bid',
        'ask': 'ask',
        'bidSize': 'bid_size',
        'askSize': 'ask_size',
        
        # Shares
        'sharesOutstanding': 'shares_outstanding',
        'floatShares': 'float_shares',
        'sharesShort': 'shares_short',
        'shortRatio': 'short_ratio',
        'shortPercentOfFloat': 'short_percent_of_float',
        'heldPercentInsiders': 'held_percent_insiders',
        'heldPercentInstitutions': 'held_percent_institutions',
        
        # Analyst Data
        'targetHighPrice': 'target_high_price',
        'targetLowPrice': 'target_low_price',
        'targetMeanPrice': 'target_mean_price',
        'targetMedianPrice': 'target_median_price',
        'recommendationMean': 'recommendation_mean',
        'recommendationKey': 'recommendation_key',
        'numberOfAnalystOpinions': 'number_of_analyst_opinions',
        
        # Company Info
        'sector': 'sector',
        'industry': 'industry',
        'beta': 'beta',
    }
    
    def download_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Download fundamental data for a symbol
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
            
        Returns:
            Dictionary with fundamental data, or None if error
        """
        try:
            logger.info(f"Downloading fundamentals for {symbol}")
            
            # Create ticker object
            ticker = yf.Ticker(symbol)
            
            # Get info dictionary
            info = ticker.info
            
            if not info or len(info) < 5:
                logger.warning(f"No fundamental data available for {symbol}")
                return None
            
            # Extract mapped fields
            fundamentals = {'symbol': symbol}
            
            for yf_field, db_field in self.FIELD_MAPPING.items():
                value = info.get(yf_field)
                if value is not None:
                    fundamentals[db_field] = value
            
            # Store complete raw data as JSON
            fundamentals['raw_data'] = info
            fundamentals['updated_at'] = datetime.now()
            
            logger.info(f"✓ Downloaded {len(fundamentals)} fields for {symbol}")
            return fundamentals
            
        except Exception as e:
            logger.error(f"Error downloading fundamentals for {symbol}: {e}")
            return None
    
    def download_multiple(self, symbols: list) -> Dict[str, Dict[str, Any]]:
        """
        Download fundamentals for multiple symbols
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbol to fundamentals data
        """
        results = {}
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"[{i}/{len(symbols)}] Downloading {symbol}...")
            
            fundamentals = self.download_fundamentals(symbol)
            if fundamentals:
                results[symbol] = fundamentals
            
            # Small delay to avoid rate limiting
            if i < len(symbols):
                import time
                time.sleep(0.5)
        
        logger.info(f"Downloaded fundamentals for {len(results)}/{len(symbols)} symbols")
        return results
    
    def get_summary(self, symbol: str) -> Optional[str]:
        """
        Get quick summary of key metrics
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Formatted summary string
        """
        fundamentals = self.download_fundamentals(symbol)
        if not fundamentals:
            return None
        
        summary = f"""
{symbol} Fundamentals Summary
{'=' * 50}
Price: ₹{fundamentals.get('current_price', 'N/A')}
52-Week Range: ₹{fundamentals.get('fifty_two_week_low', 'N/A')} - ₹{fundamentals.get('fifty_two_week_high', 'N/A')}

Valuation:
  Market Cap: ₹{fundamentals.get('market_cap', 'N/A'):,}
  PE Ratio: {fundamentals.get('trailing_pe', 'N/A')}
  PB Ratio: {fundamentals.get('price_to_book', 'N/A')}

Profitability:
  ROE: {fundamentals.get('return_on_equity', 'N/A')}
  Profit Margin: {fundamentals.get('profit_margins', 'N/A')}

Growth:
  Revenue Growth: {fundamentals.get('revenue_growth', 'N/A')}
  Earnings Growth: {fundamentals.get('earnings_growth', 'N/A')}

Sector: {fundamentals.get('sector', 'N/A')}
Industry: {fundamentals.get('industry', 'N/A')}
"""
        return summary
