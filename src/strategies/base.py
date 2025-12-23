"""
Base strategy class for all trading strategies

Provides common functionality for indicator calculation, signal generation,
and risk management.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseStrategy:
    """
    Base class for all trading strategies
    
    Provides:
    - Indicator calculation interface
    - Signal generation framework
    - Risk management methods
    - Performance tracking
    """
    
    def __init__(self, symbol: str, df: pd.DataFrame):
        """
        Initialize strategy
        
        Args:
            symbol: Stock symbol
            df: DataFrame with OHLCV data
        """
        self.symbol = symbol
        self.df = df.copy()
        self.signals = []
        self.indicators = {}
        
        # Validate data
        self._validate_data()
    
    def _validate_data(self):
        """Validate OHLCV data"""
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required_cols if col not in self.df.columns]
        
        if missing:
            raise ValueError(f"Missing columns: {missing}")
        
        if len(self.df) < 50:
            raise ValueError(f"Insufficient data: {len(self.df)} candles (need ≥50)")
    
    def calculate_indicators(self):
        """
        Calculate all required indicators
        
        Override in subclass to add specific indicators
        """
        raise NotImplementedError("Subclass must implement calculate_indicators()")
    
    def analyze(self) -> Dict:
        """
        Analyze market conditions
        
        Returns:
            Dictionary with analysis results
        """
        raise NotImplementedError("Subclass must implement analyze()")
    
    def generate_signal(self) -> Optional[Dict]:
        """
        Generate trading signal
        
        Returns:
            Signal dictionary or None if no signal
        """
        raise NotImplementedError("Subclass must implement generate_signal()")
    
    def calculate_stop_loss(self, entry_price: float) -> float:
        """
        Calculate stop-loss price
        
        Args:
            entry_price: Entry price
            
        Returns:
            Stop-loss price
        """
        raise NotImplementedError("Subclass must implement calculate_stop_loss()")
    
    def calculate_take_profit(self, entry_price: float, stop_loss: float) -> List[float]:
        """
        Calculate take-profit targets
        
        Args:
            entry_price: Entry price
            stop_loss: Stop-loss price
            
        Returns:
            List of take-profit prices
        """
        raise NotImplementedError("Subclass must implement calculate_take_profit()")
    
    def get_current_price(self) -> float:
        """Get current (latest) price"""
        return float(self.df['close'].iloc[-1])
    
    def get_latest_candle(self) -> pd.Series:
        """Get latest candle data"""
        return self.df.iloc[-1]
    
    def format_signal(self, signal_type: str, confidence: float, 
                     entry: float, stop_loss: float, targets: List[float],
                     analysis: Dict) -> Dict:
        """
        Format signal for output
        
        Args:
            signal_type: 'BUY' or 'SELL'
            confidence: Confidence score (0-100)
            entry: Entry price
            stop_loss: Stop-loss price
            targets: List of take-profit prices
            analysis: Analysis details
            
        Returns:
            Formatted signal dictionary
        """
        risk = abs(entry - stop_loss)
        reward = abs(targets[0] - entry)
        risk_reward = reward / risk if risk > 0 else 0
        
        return {
            'symbol': self.symbol,
            'timestamp': datetime.now(),
            'signal_type': signal_type,
            'confidence': round(confidence, 2),
            'entry_price': round(entry, 2),
            'stop_loss': round(stop_loss, 2),
            'target1': round(targets[0], 2),
            'target2': round(targets[1], 2) if len(targets) > 1 else None,
            'target3': round(targets[2], 2) if len(targets) > 2 else None,
            'risk': round(risk, 2),
            'reward': round(reward, 2),
            'risk_reward_ratio': round(risk_reward, 2),
            'analysis': analysis
        }
    
    def __repr__(self):
        return f"{self.__class__.__name__}(symbol={self.symbol}, candles={len(self.df)})"
