"""
Fibonacci Retracement and Extension Levels

Calculates key Fibonacci levels for support/resistance identification.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple


class FibonacciLevels:
    """Calculate Fibonacci retracement and extension levels"""
    
    # Standard Fibonacci ratios
    RETRACEMENT_LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786]
    EXTENSION_LEVELS = [1.272, 1.618, 2.0]
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with price data
        
        Args:
            df: DataFrame with OHLC data
        """
        self.df = df
    
    def find_swing_points(self, lookback: int = 50) -> Tuple[float, float, int, int]:
        """
        Find recent swing high and swing low
        
        Args:
            lookback: Number of candles to look back
            
        Returns:
            (swing_high, swing_low, high_index, low_index)
        """
        recent_data = self.df.tail(lookback)
        
        swing_high = recent_data['high'].max()
        swing_low = recent_data['low'].min()
        
        high_index = recent_data['high'].idxmax()
        low_index = recent_data['low'].idxmin()
        
        return swing_high, swing_low, high_index, low_index
    
    def calculate_retracements(self, lookback: int = 50) -> Dict[str, float]:
        """
        Calculate Fibonacci retracement levels
        
        For uptrend: Levels from swing_low to swing_high
        For downtrend: Levels from swing_high to swing_low
        
        Args:
            lookback: Number of candles to analyze
            
        Returns:
            Dictionary with Fibonacci levels
        """
        swing_high, swing_low, high_idx, low_idx = self.find_swing_points(lookback)
        
        # Determine trend direction
        is_uptrend = low_idx < high_idx
        
        price_range = swing_high - swing_low
        
        levels = {
            'swing_high': swing_high,
            'swing_low': swing_low,
            'is_uptrend': is_uptrend
        }
        
        if is_uptrend:
            # Retracement from high back down (support levels)
            for ratio in self.RETRACEMENT_LEVELS:
                level_price = swing_high - (price_range * ratio)
                levels[f'fib_{ratio:.3f}'] = level_price
        else:
            # Retracement from low back up (resistance levels)
            for ratio in self.RETRACEMENT_LEVELS:
                level_price = swing_low + (price_range * ratio)
                levels[f'fib_{ratio:.3f}'] = level_price
        
        return levels
    
    def calculate_extensions(self, lookback: int = 50) -> Dict[str, float]:
        """
        Calculate Fibonacci extension levels (for targets)
        
        Args:
            lookback: Number of candles to analyze
            
        Returns:
            Dictionary with extension levels
        """
        swing_high, swing_low, high_idx, low_idx = self.find_swing_points(lookback)
        
        is_uptrend = low_idx < high_idx
        price_range = swing_high - swing_low
        
        levels = {}
        
        if is_uptrend:
            # Extensions above swing high (targets for longs)
            for ratio in self.EXTENSION_LEVELS:
                level_price = swing_high + (price_range * (ratio - 1))
                levels[f'ext_{ratio:.3f}'] = level_price
        else:
            # Extensions below swing low (targets for shorts)
            for ratio in self.EXTENSION_LEVELS:
                level_price = swing_low - (price_range * (ratio - 1))
                levels[f'ext_{ratio:.3f}'] = level_price
        
        return levels
    
    def get_nearest_support(self, current_price: float, lookback: int = 50) -> float:
        """
        Get nearest Fibonacci support level below current price
        
        Args:
            current_price: Current market price
            lookback: Number of candles to analyze
            
        Returns:
            Nearest support level
        """
        levels = self.calculate_retracements(lookback)
        
        # Filter support levels below current price
        support_levels = []
        for key, value in levels.items():
            if key.startswith('fib_') and value < current_price:
                support_levels.append(value)
        
        # Add swing low as ultimate support
        if levels['swing_low'] < current_price:
            support_levels.append(levels['swing_low'])
        
        # Return nearest (highest) support
        if support_levels:
            return max(support_levels)
        else:
            # Fallback to swing low
            return levels['swing_low']
    
    def get_nearest_resistance(self, current_price: float, lookback: int = 50) -> float:
        """
        Get nearest Fibonacci resistance level above current price
        
        Args:
            current_price: Current market price
            lookback: Number of candles to analyze
            
        Returns:
            Nearest resistance level
        """
        levels = self.calculate_retracements(lookback)
        extensions = self.calculate_extensions(lookback)
        
        # Filter resistance levels above current price
        resistance_levels = []
        
        for key, value in levels.items():
            if key.startswith('fib_') and value > current_price:
                resistance_levels.append(value)
        
        # Add swing high
        if levels['swing_high'] > current_price:
            resistance_levels.append(levels['swing_high'])
        
        # Add extension levels
        for key, value in extensions.items():
            if value > current_price:
                resistance_levels.append(value)
        
        # Return nearest (lowest) resistance
        if resistance_levels:
            return min(resistance_levels)
        else:
            # Fallback to swing high
            return levels['swing_high']
    
    def get_all_levels(self, lookback: int = 50) -> Dict:
        """
        Get all Fibonacci levels (retracements + extensions)
        
        Args:
            lookback: Number of candles to analyze
            
        Returns:
            Complete dictionary of all levels
        """
        retracements = self.calculate_retracements(lookback)
        extensions = self.calculate_extensions(lookback)
        
        return {**retracements, **extensions}
