"""
Daily Signal Generator

Generates trading signals for all Nifty 100 stocks with fundamental filtering
"""

import pandas as pd
import logging
from typing import List, Dict, Optional
from datetime import datetime

from src.data.storage import InstrumentsDB, OHLCVDB, FundamentalsDB
from src.strategies import MultiIndicatorStrategy

logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    Generate daily trading signals for Nifty 100 stocks
    
    Features:
    - Fundamental pre-filtering (PE, ROE, market cap)
    - Multi-indicator strategy analysis
    - Confidence-based filtering
    """
    
    def __init__(self, timeframe: str = '1d', lookback: int = 365):
        """
        Initialize signal generator
        
        Args:
            timeframe: Timeframe for analysis (default: '1d')
            lookback: Number of candles to analyze (default: 365)
        """
        self.timeframe = timeframe
        self.lookback = lookback
        
        # Timeframe-specific settings
        if timeframe == '75m':
            self.lookback_candles = 150  # ~2 weeks of 75m data
            self.min_candles = 100
        else:  # '1d' (daily)
            self.lookback_candles = lookback
            self.min_candles = 50
        
        self.instruments_db = InstrumentsDB()
        self.ohlcv_db = OHLCVDB()
        self.fundamentals_db = FundamentalsDB()
    
    def filter_by_fundamentals(self, symbol: str) -> bool:
        """
        Pre-filter stocks by fundamentals
        
        Criteria:
        - PE < 30 (not overvalued)
        - ROE > 15% (profitable)
        - Market cap > 100B (liquid)
        
        Args:
            symbol: Stock symbol
            
        Returns:
            True if passes filters
        """
        try:
            fundamentals = self.fundamentals_db.get_fundamentals(symbol)
            
            if not fundamentals:
                logger.warning(f"{symbol}: No fundamental data")
                return False
            
            # Check criteria
            pe = fundamentals.get('trailing_pe')
            roe = fundamentals.get('return_on_equity')
            market_cap = fundamentals.get('market_cap')
            
            # PE check
            if pe and pe > 30:
                logger.debug(f"{symbol}: PE {pe:.1f} > 30 (overvalued)")
                return False
            
            # ROE check
            if roe and roe < 0.15:
                logger.debug(f"{symbol}: ROE {roe:.1%} < 15% (low profitability)")
                return False
            
            # Market cap check
            if market_cap and market_cap < 100e9:
                logger.debug(f"{symbol}: Market cap ₹{market_cap/1e9:.1f}B < ₹100B (low liquidity)")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error filtering {symbol}: {e}")
            return False
    
    def generate_signals(self, 
                        symbols: Optional[List[str]] = None,
                        use_fundamental_filter: bool = True,
                        min_confidence: float = 65.0) -> List[Dict]:
        """
        Generate signals for multiple symbols
        
        Args:
            symbols: List of symbols (default: all Nifty 100)
            use_fundamental_filter: Apply fundamental filtering
            min_confidence: Minimum confidence threshold
            
        Returns:
            List of signal dictionaries
        """
        # Get symbols
        if symbols is None:
            symbols = self.instruments_db.get_nifty_100()
        
        logger.info(f"Generating signals for {len(symbols)} symbols")
        logger.info(f"Timeframe: {self.timeframe}, Lookback: {self.lookback} candles")
        logger.info(f"Fundamental filter: {use_fundamental_filter}, Min confidence: {min_confidence}%")
        
        signals = []
        filtered_count = 0
        insufficient_data = 0
        
        for i, symbol in enumerate(symbols, 1):
            try:
                # Fundamental filter
                if use_fundamental_filter and not self.filter_by_fundamentals(symbol):
                    filtered_count += 1
                    continue
                
                # Load OHLCV data
                df = self.ohlcv_db.get_ohlcv(symbol, self.timeframe, limit=self.lookback_candles)
                
                if len(df) < self.min_candles:
                    logger.warning(f"[{i}/{len(symbols)}] {symbol}: Insufficient data ({len(df)} candles)")
                    insufficient_data += 1
                    continue
                
                # Create strategy and generate signal
                strategy = MultiIndicatorStrategy(symbol, df)
                signal = strategy.generate_signal()
                
                if signal and signal['confidence'] >= min_confidence:
                    signals.append(signal)
                    logger.info(f"[{i}/{len(symbols)}] {symbol}: ✅ Signal generated (confidence: {signal['confidence']:.1f}%)")
                else:
                    logger.debug(f"[{i}/{len(symbols)}] {symbol}: No signal")
                
            except Exception as e:
                logger.error(f"[{i}/{len(symbols)}] {symbol}: Error - {e}")
        
        # Summary
        logger.info(f"\nSignal Generation Summary:")
        logger.info(f"  Total symbols: {len(symbols)}")
        logger.info(f"  Filtered by fundamentals: {filtered_count}")
        logger.info(f"  Insufficient data: {insufficient_data}")
        logger.info(f"  Analyzed: {len(symbols) - filtered_count - insufficient_data}")
        logger.info(f"  Signals generated: {len(signals)}")
        
        return signals
    
    def generate_daily_signals(self) -> List[Dict]:
        """
        Generate signals for daily trading
        
        Uses default settings:
        - All Nifty 100 stocks
        - Fundamental filtering enabled
        - Minimum 65% confidence
        
        Returns:
            List of signals
        """
        return self.generate_signals(
            symbols=None,
            use_fundamental_filter=True,
            min_confidence=65.0
        )
