"""
Candlestick pattern recognition using TA-Lib

Provides 61 candlestick patterns for pattern-based trading
"""

import pandas as pd
import numpy as np
import talib

from .base import BaseIndicator


class CandlestickPatterns(BaseIndicator):
    """
    Candlestick pattern recognition
    
    Returns 100 for bullish, -100 for bearish, 0 for no pattern
    """
    
    # ============================================================================
    # Bullish Reversal Patterns
    # ============================================================================
    
    def hammer(self) -> pd.Series:
        """Hammer - Bullish reversal"""
        return pd.Series(
            talib.CDLHAMMER(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='HAMMER'
        )
    
    def inverted_hammer(self) -> pd.Series:
        """Inverted Hammer - Bullish reversal"""
        return pd.Series(
            talib.CDLINVERTEDHAMMER(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='INVERTED_HAMMER'
        )
    
    def morning_star(self) -> pd.Series:
        """Morning Star - Bullish reversal (3-candle)"""
        return pd.Series(
            talib.CDLMORNINGSTAR(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='MORNING_STAR'
        )
    
    def morning_doji_star(self) -> pd.Series:
        """Morning Doji Star - Bullish reversal (3-candle)"""
        return pd.Series(
            talib.CDLMORNINGDOJISTAR(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='MORNING_DOJI_STAR'
        )
    
    def piercing_line(self) -> pd.Series:
        """Piercing Line - Bullish reversal (2-candle)"""
        return pd.Series(
            talib.CDLPIERCING(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='PIERCING_LINE'
        )
    
    def three_white_soldiers(self) -> pd.Series:
        """Three White Soldiers - Strong bullish reversal"""
        return pd.Series(
            talib.CDL3WHITESOLDIERS(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='THREE_WHITE_SOLDIERS'
        )
    
    # ============================================================================
    # Bearish Reversal Patterns
    # ============================================================================
    
    def hanging_man(self) -> pd.Series:
        """Hanging Man - Bearish reversal"""
        return pd.Series(
            talib.CDLHANGINGMAN(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='HANGING_MAN'
        )
    
    def shooting_star(self) -> pd.Series:
        """Shooting Star - Bearish reversal"""
        return pd.Series(
            talib.CDLSHOOTINGSTAR(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='SHOOTING_STAR'
        )
    
    def evening_star(self) -> pd.Series:
        """Evening Star - Bearish reversal (3-candle)"""
        return pd.Series(
            talib.CDLEVENINGSTAR(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='EVENING_STAR'
        )
    
    def evening_doji_star(self) -> pd.Series:
        """Evening Doji Star - Bearish reversal (3-candle)"""
        return pd.Series(
            talib.CDLEVENINGDOJISTAR(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='EVENING_DOJI_STAR'
        )
    
    def dark_cloud_cover(self) -> pd.Series:
        """Dark Cloud Cover - Bearish reversal (2-candle)"""
        return pd.Series(
            talib.CDLDARKCLOUDCOVER(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='DARK_CLOUD_COVER'
        )
    
    def three_black_crows(self) -> pd.Series:
        """Three Black Crows - Strong bearish reversal"""
        return pd.Series(
            talib.CDL3BLACKCROWS(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='THREE_BLACK_CROWS'
        )
    
    # ============================================================================
    # Engulfing Patterns
    # ============================================================================
    
    def engulfing(self) -> pd.Series:
        """Engulfing Pattern - Bullish (100) or Bearish (-100)"""
        return pd.Series(
            talib.CDLENGULFING(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='ENGULFING'
        )
    
    # ============================================================================
    # Doji Patterns
    # ============================================================================
    
    def doji(self) -> pd.Series:
        """Doji - Indecision"""
        return pd.Series(
            talib.CDLDOJI(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='DOJI'
        )
    
    def dragonfly_doji(self) -> pd.Series:
        """Dragonfly Doji - Bullish reversal"""
        return pd.Series(
            talib.CDLDRAGONFLYDOJI(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='DRAGONFLY_DOJI'
        )
    
    def gravestone_doji(self) -> pd.Series:
        """Gravestone Doji - Bearish reversal"""
        return pd.Series(
            talib.CDLGRAVESTONEDOJI(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='GRAVESTONE_DOJI'
        )
    
    def long_legged_doji(self) -> pd.Series:
        """Long Legged Doji - Strong indecision"""
        return pd.Series(
            talib.CDLLONGLEGGEDDOJI(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='LONG_LEGGED_DOJI'
        )
    
    # ============================================================================
    # Harami Patterns
    # ============================================================================
    
    def harami(self) -> pd.Series:
        """Harami - Bullish (100) or Bearish (-100)"""
        return pd.Series(
            talib.CDLHARAMI(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='HARAMI'
        )
    
    def harami_cross(self) -> pd.Series:
        """Harami Cross - Stronger reversal signal"""
        return pd.Series(
            talib.CDLHARAMICROSS(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='HARAMI_CROSS'
        )
    
    # ============================================================================
    # Other Common Patterns
    # ============================================================================
    
    def spinning_top(self) -> pd.Series:
        """Spinning Top - Indecision"""
        return pd.Series(
            talib.CDLSPINNINGTOP(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='SPINNING_TOP'
        )
    
    def marubozu(self) -> pd.Series:
        """Marubozu - Strong trend continuation"""
        return pd.Series(
            talib.CDLMARUBOZU(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='MARUBOZU'
        )
    
    def kicking(self) -> pd.Series:
        """Kicking - Strong reversal (2-candle)"""
        return pd.Series(
            talib.CDLKICKING(self.df['open'], self.df['high'], self.df['low'], self.df['close']),
            index=self.df.index, name='KICKING'
        )
    
    # ============================================================================
    # Scan All Patterns
    # ============================================================================
    
    def scan_all_patterns(self) -> pd.DataFrame:
        """
        Scan for all 61 candlestick patterns
        
        Returns:
            DataFrame with all pattern signals
        """
        # Get all TA-Lib candlestick pattern functions
        pattern_functions = [
            'CDL2CROWS', 'CDL3BLACKCROWS', 'CDL3INSIDE', 'CDL3LINESTRIKE',
            'CDL3OUTSIDE', 'CDL3STARSINSOUTH', 'CDL3WHITESOLDIERS',
            'CDLABANDONEDBABY', 'CDLADVANCEBLOCK', 'CDLBELTHOLD',
            'CDLBREAKAWAY', 'CDLCLOSINGMARUBOZU', 'CDLCONCEALBABYSWALL',
            'CDLCOUNTERATTACK', 'CDLDARKCLOUDCOVER', 'CDLDOJI',
            'CDLDOJISTAR', 'CDLDRAGONFLYDOJI', 'CDLENGULFING',
            'CDLEVENINGDOJISTAR', 'CDLEVENINGSTAR', 'CDLGAPSIDESIDEWHITE',
            'CDLGRAVESTONEDOJI', 'CDLHAMMER', 'CDLHANGINGMAN',
            'CDLHARAMI', 'CDLHARAMICROSS', 'CDLHIGHWAVE',
            'CDLHIKKAKE', 'CDLHIKKAKEMOD', 'CDLHOMINGPIGEON',
            'CDLIDENTICAL3CROWS', 'CDLINNECK', 'CDLINVERTEDHAMMER',
            'CDLKICKING', 'CDLKICKINGBYLENGTH', 'CDLLADDERBOTTOM',
            'CDLLONGLEGGEDDOJI', 'CDLLONGLINE', 'CDLMARUBOZU',
            'CDLMATCHINGLOW', 'CDLMATHOLD', 'CDLMORNINGDOJISTAR',
            'CDLMORNINGSTAR', 'CDLONNECK', 'CDLPIERCING',
            'CDLRICKSHAWMAN', 'CDLRISEFALL3METHODS', 'CDLSEPARATINGLINES',
            'CDLSHOOTINGSTAR', 'CDLSHORTLINE', 'CDLSPINNINGTOP',
            'CDLSTALLEDPATTERN', 'CDLSTICKSANDWICH', 'CDLTAKURI',
            'CDLTASUKIGAP', 'CDLTHRUSTING', 'CDLTRISTAR',
            'CDLUNIQUE3RIVER', 'CDLUPSIDEGAP2CROWS', 'CDLXSIDEGAP3METHODS'
        ]
        
        results = {}
        for pattern_name in pattern_functions:
            pattern_func = getattr(talib, pattern_name)
            results[pattern_name] = pattern_func(
                self.df['open'],
                self.df['high'],
                self.df['low'],
                self.df['close']
            )
        
        return pd.DataFrame(results, index=self.df.index)
    
    def get_active_patterns(self, threshold: int = 0) -> pd.DataFrame:
        """
        Get only active patterns (non-zero values)
        
        Args:
            threshold: Minimum absolute value to consider (default: 0)
            
        Returns:
            DataFrame with only active patterns
        """
        all_patterns = self.scan_all_patterns()
        
        # Filter to only rows with at least one active pattern
        active_rows = all_patterns[all_patterns.abs().sum(axis=1) > threshold]
        
        # Filter to only columns (patterns) that have at least one signal
        active_cols = all_patterns.columns[all_patterns.abs().sum(axis=0) > 0]
        
        return all_patterns.loc[active_rows.index, active_cols]
