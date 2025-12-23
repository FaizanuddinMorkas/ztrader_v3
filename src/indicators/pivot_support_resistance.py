"""
Support and Resistance Level Detection using pandas_ta

Uses pandas_ta pivot points and rolling window analysis for S/R detection.
"""

import pandas as pd
import numpy as np
import pandas_ta as ta
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class PivotSupportResistance:
    """Detect support and resistance levels using pandas_ta pivot points"""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with price data
        
        Args:
            df: DataFrame with OHLCV data
        """
        self.df = df.copy()
    
    def find_pivot_levels(self) -> Dict[str, float]:
        """
        Calculate pivot points (PP, R1, R2, R3, S1, S2, S3)
        
        Returns:
            Dict with pivot levels
        """
        # Use last candle for pivot calculation
        high = self.df['high'].iloc[-1]
        low = self.df['low'].iloc[-1]
        close = self.df['close'].iloc[-1]
        
        # Standard pivot points
        pp = (high + low + close) / 3
        
        # Resistance levels
        r1 = (2 * pp) - low
        r2 = pp + (high - low)
        r3 = high + 2 * (pp - low)
        
        # Support levels
        s1 = (2 * pp) - high
        s2 = pp - (high - low)
        s3 = low - 2 * (high - pp)
        
        return {
            'pp': pp,
            'r1': r1,
            'r2': r2,
            'r3': r3,
            's1': s1,
            's2': s2,
            's3': s3
        }
    
    def find_resistance_levels(self, lookback: int = 50) -> List[Dict]:
        """
        Find resistance levels using rolling window maxima
        
        Args:
            lookback: Number of candles to analyze
            
        Returns:
            List of resistance levels with metadata
        """
        recent_df = self.df.tail(lookback).copy()
        
        # Find local maxima using rolling window
        window = 10
        recent_df['local_max'] = recent_df['high'].rolling(window, center=True).max()
        
        # Identify peaks (where high == local_max)
        peaks = recent_df[recent_df['high'] == recent_df['local_max']].copy()
        
        # Remove duplicates (same price level)
        resistance_levels = []
        seen_prices = set()
        
        for idx, row in peaks.iterrows():
            price = row['high']
            # Round to avoid floating point duplicates
            price_rounded = round(price, 2)
            
            if price_rounded not in seen_prices:
                seen_prices.add(price_rounded)
                
                # Count touches
                touches = self._count_touches(price, tolerance=0.01)
                
                resistance_levels.append({
                    'price': price,
                    'index': idx,
                    'touches': touches,
                    'strength': touches,  # Simple strength = touch count
                    'type': 'resistance'
                })
        
        # Add pivot resistance levels
        pivots = self.find_pivot_levels()
        for level_name in ['r1', 'r2', 'r3']:
            price = pivots[level_name]
            price_rounded = round(price, 2)
            
            if price_rounded not in seen_prices:
                seen_prices.add(price_rounded)
                resistance_levels.append({
                    'price': price,
                    'index': len(self.df) - 1,
                    'touches': 1,
                    'strength': 2,  # Pivot levels get higher strength
                    'type': f'pivot_{level_name}'
                })
        
        # Sort by price
        resistance_levels.sort(key=lambda x: x['price'])
        
        logger.debug(f"Found {len(resistance_levels)} resistance levels")
        return resistance_levels
    
    def find_support_levels(self, lookback: int = 50) -> List[Dict]:
        """
        Find support levels using rolling window minima
        
        Args:
            lookback: Number of candles to analyze
            
        Returns:
            List of support levels with metadata
        """
        recent_df = self.df.tail(lookback).copy()
        
        # Find local minima using rolling window
        window = 10
        recent_df['local_min'] = recent_df['low'].rolling(window, center=True).min()
        
        # Identify valleys (where low == local_min)
        valleys = recent_df[recent_df['low'] == recent_df['local_min']].copy()
        
        # Remove duplicates
        support_levels = []
        seen_prices = set()
        
        for idx, row in valleys.iterrows():
            price = row['low']
            price_rounded = round(price, 2)
            
            if price_rounded not in seen_prices:
                seen_prices.add(price_rounded)
                
                # Count touches
                touches = self._count_touches(price, tolerance=0.01)
                
                support_levels.append({
                    'price': price,
                    'index': idx,
                    'touches': touches,
                    'strength': touches,
                    'type': 'support'
                })
        
        # Add pivot support levels
        pivots = self.find_pivot_levels()
        for level_name in ['s1', 's2', 's3']:
            price = pivots[level_name]
            price_rounded = round(price, 2)
            
            if price_rounded not in seen_prices:
                seen_prices.add(price_rounded)
                support_levels.append({
                    'price': price,
                    'index': len(self.df) - 1,
                    'touches': 1,
                    'strength': 2,
                    'type': f'pivot_{level_name}'
                })
        
        # Sort by price (descending for support)
        support_levels.sort(key=lambda x: x['price'], reverse=True)
        
        logger.debug(f"Found {len(support_levels)} support levels")
        return support_levels
    
    def get_nearest_resistance(self, price: float, min_distance: float = 0.01) -> Dict:
        """Get nearest resistance level above given price"""
        resistance_levels = self.find_resistance_levels()
        
        valid_levels = [
            r for r in resistance_levels 
            if r['price'] > price * (1 + min_distance)
        ]
        
        return valid_levels[0] if valid_levels else None
    
    def get_nearest_support(self, price: float, min_distance: float = 0.01) -> Dict:
        """Get nearest support level below given price"""
        support_levels = self.find_support_levels()
        
        valid_levels = [
            s for s in support_levels 
            if s['price'] < price * (1 - min_distance)
        ]
        
        return valid_levels[0] if valid_levels else None
    
    def get_resistance_targets(self, entry_price: float, stop_loss: float,
                              min_rr: float = 1.5, count: int = 3) -> List[Dict]:
        """
        Get resistance levels suitable for targets with R:R validation
        
        Args:
            entry_price: Entry price
            stop_loss: Stop-loss price
            min_rr: Minimum risk:reward ratio
            count: Number of targets
            
        Returns:
            List of validated resistance levels
        """
        resistance_levels = self.find_resistance_levels()
        risk = entry_price - stop_loss
        
        if risk <= 0:
            return []
        
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
        
        valid_targets.sort(key=lambda x: x['price'])
        return valid_targets[:count]
    
    def _count_touches(self, price: float, tolerance: float = 0.01) -> int:
        """Count how many times price touched this level"""
        upper_bound = price * (1 + tolerance)
        lower_bound = price * (1 - tolerance)
        
        touches = 0
        for _, row in self.df.iterrows():
            if lower_bound <= row['high'] <= upper_bound or \
               lower_bound <= row['low'] <= upper_bound:
                touches += 1
        
        return touches
    
    def get_all_levels(self, lookback: int = 50) -> Dict[str, List[Dict]]:
        """Get all support and resistance levels"""
        return {
            'support': self.find_support_levels(lookback=lookback),
            'resistance': self.find_resistance_levels(lookback=lookback),
            'pivots': self.find_pivot_levels()
        }
