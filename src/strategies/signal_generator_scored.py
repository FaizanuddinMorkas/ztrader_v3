"""
Signal Generator for Scored Fundamentals Strategy

Uses MultiIndicatorScoredStrategy instead of filtering fundamentals
"""

import pandas as pd
import logging
from typing import List, Dict, Optional
from datetime import datetime

from src.data.storage import InstrumentsDB, OHLCVDB, FundamentalsDB
from src.strategies import MultiIndicatorScoredStrategy

logger = logging.getLogger(__name__)


class SignalGeneratorScored:
    """
    Generate signals using fundamental scoring (not filtering)
    
    Differences from SignalGenerator:
    - Does NOT filter stocks by fundamentals
    - Uses MultiIndicatorScoredStrategy
    - Passes fundamentals to strategy for scoring
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
            self.lookback_candles = 150
            self.min_candles = 100
        else:
            self.lookback_candles = lookback
            self.min_candles = 50
        
        self.instruments_db = InstrumentsDB()
        self.ohlcv_db = OHLCVDB()
        self.fundamentals_db = FundamentalsDB()
    
    def generate_signals(self, 
                        symbols: Optional[List[str]] = None,
                        use_fundamental_filter: bool = False,  # Always False for scored
                        min_confidence: float = 65.0,
                        batch_size: int = 100) -> List[Dict]:
        """
        Generate signals for multiple symbols using batch processing
        
        Args:
            symbols: List of symbols (default: all Nifty 100)
            use_fundamental_filter: Ignored (always False for scored strategy)
            min_confidence: Minimum confidence threshold
            batch_size: Number of stocks to process per batch (default: 100)
            
        Returns:
            List of signal dictionaries
        """
        # Get symbols
        if symbols is None:
            symbols = self.instruments_db.get_nifty_100()
        
        logger.info(f"Generating signals for {len(symbols)} symbols (SCORED FUNDAMENTALS)")
        logger.info(f"Timeframe: {self.timeframe}, Lookback: {self.lookback} candles")
        logger.info(f"Fundamental scoring: ENABLED, Min confidence: {min_confidence}%")
        logger.info(f"Batch processing: {batch_size} stocks per batch")
        
        all_signals = []
        total_insufficient_data = 0
        
        # Process symbols in batches
        num_batches = (len(symbols) + batch_size - 1) // batch_size
        
        for batch_num in range(num_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(symbols))
            batch_symbols = symbols[start_idx:end_idx]
            
            logger.info(f"\n📦 Processing batch {batch_num + 1}/{num_batches} ({len(batch_symbols)} stocks)")
            
            batch_signals = []
            batch_insufficient = 0
            
            for i, symbol in enumerate(batch_symbols, 1):
                global_idx = start_idx + i
                try:
                    # Load OHLCV data
                    df = self.ohlcv_db.get_ohlcv(symbol, self.timeframe, limit=self.lookback_candles)
                    
                    if len(df) < self.min_candles:
                        logger.warning(f"[{global_idx}/{len(symbols)}] {symbol}: Insufficient data ({len(df)} candles)")
                        batch_insufficient += 1
                        continue
                    
                    # Get fundamentals (for scoring, not filtering)
                    fundamentals = self.fundamentals_db.get_fundamentals(symbol)
                    
                    # Create scored strategy and generate signal
                    strategy = MultiIndicatorScoredStrategy(symbol, df, min_confidence=min_confidence)
                    signal = strategy.generate_signal(fundamentals=fundamentals)
                    
                    if signal:
                        batch_signals.append(signal)
                        fund_score = signal.get('fundamental_score', 0)
                        tech_conf = signal.get('technical_confidence', 0)
                        logger.info(
                            f"[{global_idx}/{len(symbols)}] {symbol}: ✅ Signal generated "
                            f"(confidence: {signal['confidence']:.1f}%, tech: {tech_conf:.1f}%, fund: {fund_score:+d})"
                        )
                    else:
                        logger.debug(f"[{global_idx}/{len(symbols)}] {symbol}: No signal")
                    
                except Exception as e:
                    logger.error(f"[{global_idx}/{len(symbols)}] {symbol}: Error - {e}")
            
            # Add batch results to total
            all_signals.extend(batch_signals)
            total_insufficient_data += batch_insufficient
            
            logger.info(f"✅ Batch {batch_num + 1} complete: {len(batch_signals)} signals found")
        
        # Summary
        logger.info(f"\nSignal Generation Summary:")
        logger.info(f"  Total symbols: {len(symbols)}")
        logger.info(f"  Filtered by fundamentals: 0 (scoring enabled)")
        logger.info(f"  Insufficient data: {total_insufficient_data}")
        logger.info(f"  Analyzed: {len(symbols) - total_insufficient_data}")
        logger.info(f"  Signals generated: {len(all_signals)}")
        
        return all_signals
