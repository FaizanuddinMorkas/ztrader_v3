"""
Support and Resistance Level Detection

Uses scipy.signal.find_peaks to identify actual support and resistance levels
based on swing highs and lows in price action.
"""

import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class SupportResistance:
    """Detect support and resistance levels using peak detection"""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with price data
        
        Args:
            df: DataFrame with OHLCV data
        """
        self.df = df
    
    def find_resistance_levels(self, lookback: int = 100, distance: int = 5, 
                              prominence: float = 0.5) -> List[Dict]:
        """
        Find resistance levels (swing highs) using peak detection
        
        Args:
            lookback: Number of candles to analyze
            distance: Minimum candles between peaks
            prominence: Minimum prominence as % of price (2.0 = 2%)
            
        Returns:
            List of resistance levels with metadata
        """
        # Get recent data
        recent_df = self.df.tail(lookback).copy()
        highs = recent_df['high'].values
        
        # Calculate absolute prominence threshold
        avg_price = highs.mean()
        prominence_threshold = avg_price * (prominence / 100)
        
        # Find peaks (resistance levels)
        peaks, properties = find_peaks(
            highs, 
            distance=distance,
            prominence=prominence_threshold
        )
        
        if len(peaks) == 0:
            logger.debug("No resistance levels found")
            return []
        
        # Build resistance levels with metadata
        resistance_levels = []
        for i, peak_idx in enumerate(peaks):
            actual_idx = recent_df.index[peak_idx]
            price = recent_df.iloc[peak_idx]['high']
            prominence = properties['prominences'][i]
            
            # Count how many times this level was tested
            touches = self._count_touches(price, tolerance=0.01)
            
            resistance_levels.append({
                'price': price,
                'index': actual_idx,
                'prominence': prominence,
                'touches': touches,
                'strength': prominence * touches,  # Combined strength score
                'type': 'resistance'
            })
        
        # Sort by price (ascending)
        resistance_levels.sort(key=lambda x: x['price'])
        
        logger.debug(f"Found {len(resistance_levels)} resistance levels")
        return resistance_levels
    
    def find_support_levels(self, lookback: int = 100, distance: int = 5,
                           prominence: float = 0.5) -> List[Dict]:
        """
        Find support levels (swing lows) using peak detection
        
        Args:
            lookback: Number of candles to analyze
            distance: Minimum candles between peaks
            prominence: Minimum prominence as % of price (2.0 = 2%)
            
        Returns:
            List of support levels with metadata
        """
        # Get recent data
        recent_df = self.df.tail(lookback).copy()
        lows = recent_df['low'].values
        
        # Calculate absolute prominence threshold
        avg_price = lows.mean()
        prominence_threshold = avg_price * (prominence / 100)
        
        # Find peaks in inverted data (valleys = support)
        valleys, properties = find_peaks(
            -lows,  # Invert to find valleys
            distance=distance,
            prominence=prominence_threshold
        )
        
        if len(valleys) == 0:
            logger.debug("No support levels found")
            return []
        
        # Build support levels with metadata
        support_levels = []
        for i, valley_idx in enumerate(valleys):
            actual_idx = recent_df.index[valley_idx]
            price = recent_df.iloc[valley_idx]['low']
            prominence = properties['prominences'][i]
            
            # Count how many times this level was tested
            touches = self._count_touches(price, tolerance=0.01)
            
            support_levels.append({
                'price': price,
                'index': actual_idx,
                'prominence': prominence,
                'touches': touches,
                'strength': prominence * touches,
                'type': 'support'
            })
        
        # Sort by price (descending for support)
        support_levels.sort(key=lambda x: x['price'], reverse=True)
        
        logger.debug(f"Found {len(support_levels)} support levels")
        return support_levels
    
    def get_nearest_resistance(self, price: float, min_distance: float = 0.01) -> Dict:
        """
        Get nearest resistance level above given price
        
        Args:
            price: Current price
            min_distance: Minimum distance as % (1% = 0.01)
            
        Returns:
            Nearest resistance level dict or None
        """
        resistance_levels = self.find_resistance_levels()
        
        # Filter levels above price with minimum distance
        valid_levels = [
            r for r in resistance_levels 
            if r['price'] > price * (1 + min_distance)
        ]
        
        if not valid_levels:
            return None
        
        # Return nearest (lowest price above current)
        return valid_levels[0]
    
    def get_nearest_support(self, price: float, min_distance: float = 0.01) -> Dict:
        """
        Get nearest support level below given price
        
        Args:
            price: Current price
            min_distance: Minimum distance as % (1% = 0.01)
            
        Returns:
            Nearest support level dict or None
        """
        support_levels = self.find_support_levels()
        
        # Filter levels below price with minimum distance
        valid_levels = [
            s for s in support_levels 
            if s['price'] < price * (1 - min_distance)
        ]
        
        if not valid_levels:
            return None
        
        # Return nearest (highest price below current)
        return valid_levels[0]
    
    def get_resistance_targets(self, entry_price: float, stop_loss: float,
                              min_rr: float = 1.5, count: int = 3) -> List[Dict]:
        """
        Get resistance levels suitable for targets with minimum R:R validation
        
        Args:
            entry_price: Entry price
            stop_loss: Stop-loss price
            min_rr: Minimum risk:reward ratio (1.5 = 1:1.5)
            count: Number of targets to return
            
        Returns:
            List of validated resistance levels for targets
        """
        resistance_levels = self.find_resistance_levels()
        risk = entry_price - stop_loss
        
        if risk <= 0:
            logger.warning("Invalid risk (entry <= stop_loss)")
            return []
        
        # Filter and validate resistance levels
        valid_targets = []
        for level in resistance_levels:
            if level['price'] <= entry_price:
                continue
            
            reward = level['price'] - entry_price
            rr_ratio = reward / risk
            
            if rr_ratio >= min_rr:
                level['reward'] = reward
                level['rr_ratio'] = rr_ratio
                valid_targets.append(level)
        
        # Sort by price (nearest first)
        valid_targets.sort(key=lambda x: x['price'])
        
        # Return requested count
        return valid_targets[:count]
    
    def _count_touches(self, price: float, tolerance: float = 0.01) -> int:
        """
        Count how many times price touched this level
        
        Args:
            price: Price level to check
            tolerance: Tolerance as % (1% = 0.01)
            
        Returns:
            Number of touches
        """
        upper_bound = price * (1 + tolerance)
        lower_bound = price * (1 - tolerance)
        
        # Count candles where high/low touched this level
        touches = 0
        for _, row in self.df.iterrows():
            if lower_bound <= row['high'] <= upper_bound or \
               lower_bound <= row['low'] <= upper_bound:
                touches += 1
        
        return touches
    
    def get_all_levels(self, lookback: int = 50) -> Dict[str, List[Dict]]:
        """
        Get all support and resistance levels
        
        Args:
            lookback: Number of candles to analyze
            
        Returns:
            Dict with 'support' and 'resistance' lists
        """
        return {
            'support': self.find_support_levels(lookback=lookback),
            'resistance': self.find_resistance_levels(lookback=lookback)
        }
